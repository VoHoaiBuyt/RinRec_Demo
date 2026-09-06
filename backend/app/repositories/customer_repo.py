# -*- coding: utf-8 -*-
"""
backend/app/repositories/customer_repo.py
Customer data access layer for RinRec SmartAdvisor 360.
"""
from typing import List, Optional, Dict, Any
from backend.app.core.db_connector import get_db_connector
from backend.app.core.security import encrypt_pii_fields, decrypt_pii_fields

PII_FIELDS = ["email", "phone", "address", "income"]


class CustomerRepository:
    """Customer repository with PII encryption."""
    
    def __init__(self):
        self.connector = get_db_connector()
        self.collection = self.connector.get_collection("customers")
    
    def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all customers (decrypted)."""
        customers = list(self.collection.find({}, limit=limit))
        return [self._decrypt_customer(c) for c in customers]
    
    def find_by_cif(self, cif: str) -> Optional[Dict[str, Any]]:
        """Find customer by CIF."""
        customer = self.collection.find_one({"cif": cif})
        if customer:
            return self._decrypt_customer(customer)
        return None
    
    def create(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new customer (encrypt PII)."""
        encrypted = encrypt_pii_fields(customer_data, PII_FIELDS)
        self.collection.insert_one(encrypted)
        return self._decrypt_customer(encrypted)
    
    def update(self, cif: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update customer (encrypt PII fields if present)."""
        encrypted = encrypt_pii_fields(update_data, PII_FIELDS)
        result = self.collection.update_one({"cif": cif}, {"$set": encrypted})
        if result.matched_count > 0:
            return self.find_by_cif(cif)
        return None
    
    def delete(self, cif: str) -> bool:
        """Delete customer."""
        result = self.collection.delete_one({"cif": cif})
        return result.deleted_count > 0
    
    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search customers by name or CIF."""
        # Simple search (in production, use text index)
        customers = list(self.collection.find({}, limit=limit))
        filtered = [
            c for c in customers
            if query.lower() in c.get("cif", "").lower()
            or query.lower() in c.get("full_name", "").lower()
        ]
        return [self._decrypt_customer(c) for c in filtered[:limit]]
    
    def _decrypt_customer(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt PII fields and remove _id."""
        decrypted = decrypt_pii_fields(customer, PII_FIELDS)
        decrypted.pop("_id", None)
        return decrypted


def get_customer_repository() -> CustomerRepository:
    """FastAPI dependency."""
    return CustomerRepository()
