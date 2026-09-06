# -*- coding: utf-8 -*-
"""
backend/app/core/db_connector.py
MongoDB Atlas connector with JSON fallback for RinRec SmartAdvisor 360.

Features:
  - Ping MongoDB on startup, fallback to JSON if unreachable
  - Auto-sync JSON → MongoDB when connection restored
  - Collections: customers, products, transactions, consultations, users, recommendations, rules, audit_logs
  - Singleton pattern for db client
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Setup logger
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    Singleton MongoDB connector with JSON fallback.
    """
    _instance: Optional["DatabaseConnector"] = None
    _client: Optional[MongoClient] = None
    _db = None
    _fallback_mode: bool = False
    _fallback_data: Dict[str, List[Dict[str, Any]]] = {}
    
    COLLECTIONS = [
        "customers",
        "products",
        "transactions",
        "consultations",
        "users",
        "recommendations",
        "rules",
        "audit_logs",
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._connect()

    def _connect(self):
        """Attempt to connect to MongoDB, fallback to JSON if fail."""
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGODB_DB_NAME", "rinrec_smartadvisor")
        timeout_ms = int(os.getenv("MONGODB_TIMEOUT_MS", "5000"))

        try:
            logger.info(f"Connecting to MongoDB: {mongo_uri[:30]}...")
            self._client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
            )
            # Ping to verify connection
            self._client.admin.command("ping")
            self._db = self._client[db_name]
            self._fallback_mode = False
            logger.info(f"✓ MongoDB connected: database='{db_name}'")
            
            # Create indexes
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"MongoDB connection failed: {e}")
            logger.warning("Switching to JSON fallback mode")
            self._fallback_mode = True
            self._load_fallback_data()

    def _create_indexes(self):
        """Create indexes for performance."""
        if self._fallback_mode or not self._db:
            return
        
        try:
            # Customers: index on cif (unique)
            self._db.customers.create_index("cif", unique=True)
            # Products: index on product_id
            self._db.products.create_index("product_id", unique=True)
            # Transactions: index on cif, transaction_date
            self._db.transactions.create_index([("cif", 1), ("transaction_date", -1)])
            # Consultations: index on cif, teller_id
            self._db.consultations.create_index([("cif", 1), ("teller_id", 1)])
            # Users: index on username (unique)
            self._db.users.create_index("username", unique=True)
            # Audit logs: index on timestamp (desc), user
            self._db.audit_logs.create_index([("timestamp", -1), ("user", 1)])
            logger.info("✓ Database indexes created")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def _load_fallback_data(self):
        """Load data from core/fallback_data/*.json"""
        fallback_dir = Path(__file__).parent.parent.parent.parent / "core" / "fallback_data"
        if not fallback_dir.exists():
            logger.warning(f"Fallback data directory not found: {fallback_dir}")
            # Initialize empty collections
            for coll in self.COLLECTIONS:
                self._fallback_data[coll] = []
            return

        for coll in self.COLLECTIONS:
            json_path = fallback_dir / f"{coll}.json"
            if json_path.exists():
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._fallback_data[coll] = data if isinstance(data, list) else []
                    logger.info(f"✓ Loaded {len(self._fallback_data[coll])} records from {coll}.json")
                except Exception as e:
                    logger.error(f"Failed to load {json_path}: {e}")
                    self._fallback_data[coll] = []
            else:
                self._fallback_data[coll] = []

    def ping_db(self) -> bool:
        """
        Healthcheck: ping MongoDB.
        Returns True if connected, False if fallback mode.
        """
        if self._fallback_mode:
            # Try to reconnect
            try:
                mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
                test_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
                test_client.admin.command("ping")
                test_client.close()
                logger.info("MongoDB now reachable, attempting reconnect...")
                self._connect()
                if not self._fallback_mode:
                    self._sync_fallback_to_db()
                return not self._fallback_mode
            except Exception:
                return False
        else:
            try:
                self._client.admin.command("ping")
                return True
            except Exception as e:
                logger.warning(f"MongoDB ping failed: {e}, switching to fallback")
                self._fallback_mode = True
                self._load_fallback_data()
                return False

    def _sync_fallback_to_db(self):
        """Sync JSON data to MongoDB (one-way: JSON → DB)."""
        if self._fallback_mode or not self._db:
            return

        logger.info("Syncing fallback data to MongoDB...")
        for coll_name, records in self._fallback_data.items():
            if not records:
                continue
            try:
                coll = self._db[coll_name]
                # Upsert based on primary key
                pk_field = self._get_pk_field(coll_name)
                for rec in records:
                    if pk_field and pk_field in rec:
                        coll.update_one(
                            {pk_field: rec[pk_field]},
                            {"$set": rec},
                            upsert=True
                        )
                logger.info(f"✓ Synced {len(records)} records to {coll_name}")
            except Exception as e:
                logger.error(f"Failed to sync {coll_name}: {e}")

    def _get_pk_field(self, collection: str) -> Optional[str]:
        """Return primary key field name for each collection."""
        pk_map = {
            "customers": "cif",
            "products": "product_id",
            "transactions": "transaction_id",
            "consultations": "consultation_id",
            "users": "username",
            "rules": "rule_id",
            "recommendations": "recommendation_id",
            "audit_logs": "log_id",
        }
        return pk_map.get(collection)

    def get_collection(self, name: str):
        """
        Get MongoDB collection or fallback list.
        Returns a wrapper object with insert_one, find, find_one, etc.
        """
        if self._fallback_mode:
            return FallbackCollection(name, self._fallback_data.get(name, []))
        else:
            return self._db[name]

    def is_connected(self) -> bool:
        """Check if MongoDB is connected (not in fallback mode)."""
        return not self._fallback_mode

    def get_db(self):
        """Return MongoDB database object (or None if fallback)."""
        return self._db if not self._fallback_mode else None


class FallbackCollection:
    """
    Mock collection for JSON fallback mode.
    Implements basic MongoDB-like interface: insert_one, find, find_one, update_one, delete_one.
    """
    def __init__(self, name: str, data: List[Dict[str, Any]]):
        self.name = name
        self.data = data

    def insert_one(self, document: Dict[str, Any]):
        """Insert document into list."""
        doc = document.copy()
        if "_id" not in doc:
            doc["_id"] = f"{self.name}_{len(self.data) + 1}"
        self.data.append(doc)
        logger.info(f"[Fallback] Inserted into {self.name}: {doc.get('_id')}")
        return type("InsertResult", (), {"inserted_id": doc["_id"]})

    def find(self, query: Optional[Dict[str, Any]] = None, *args, **kwargs):
        """Find documents matching query."""
        query = query or {}
        results = [doc for doc in self.data if self._matches(doc, query)]
        # Support limit
        limit = kwargs.get("limit")
        if limit:
            results = results[:limit]
        return results

    def find_one(self, query: Optional[Dict[str, Any]] = None):
        """Find one document matching query."""
        query = query or {}
        for doc in self.data:
            if self._matches(doc, query):
                return doc
        return None

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert=False):
        """Update one document."""
        for doc in self.data:
            if self._matches(doc, query):
                # Apply $set operator
                if "$set" in update:
                    doc.update(update["$set"])
                else:
                    doc.update(update)
                logger.info(f"[Fallback] Updated in {self.name}: {query}")
                return type("UpdateResult", (), {"matched_count": 1, "modified_count": 1})
        
        # Upsert if not found
        if upsert:
            new_doc = query.copy()
            if "$set" in update:
                new_doc.update(update["$set"])
            else:
                new_doc.update(update)
            self.insert_one(new_doc)
            return type("UpdateResult", (), {"matched_count": 0, "modified_count": 0, "upserted_id": new_doc.get("_id")})
        
        return type("UpdateResult", (), {"matched_count": 0, "modified_count": 0})

    def delete_one(self, query: Dict[str, Any]):
        """Delete one document."""
        for i, doc in enumerate(self.data):
            if self._matches(doc, query):
                del self.data[i]
                logger.info(f"[Fallback] Deleted from {self.name}: {query}")
                return type("DeleteResult", (), {"deleted_count": 1})
        return type("DeleteResult", (), {"deleted_count": 0})

    def count_documents(self, query: Optional[Dict[str, Any]] = None):
        """Count documents matching query."""
        query = query or {}
        return len([doc for doc in self.data if self._matches(doc, query)])

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Simple query matching (only equality checks)."""
        for key, value in query.items():
            if key not in doc or doc[key] != value:
                return False
        return True


# Singleton instance
db_connector = DatabaseConnector()


def get_db_connector() -> DatabaseConnector:
    """FastAPI dependency: return DB connector singleton."""
    return db_connector
