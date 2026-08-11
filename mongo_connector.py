"""
mongo_connector.py
Quản lý kết nối và truy xuất dữ liệu từ MongoDB Atlas (Database: RinRec_DB) cho hệ thống RinRec Fintech Recommendation System.
"""
import os
import sys
import urllib.parse
import pandas as pd
from pymongo import MongoClient

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Tự động nạp cấu hình từ file .env nếu có
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

# Cấu hình kết nối MongoDB Atlas
MONGO_USER = os.getenv("MONGO_USER", "rinrec_ad")
MONGO_PASS = os.getenv("MONGO_PASS", "Hoaibuyt05@")
MONGO_HOST = os.getenv("MONGO_HOST", "cluster0.t52ffqx.mongodb.net")
DB_NAME = os.getenv("MONGO_DB_NAME", "RinRec_DB")

# URL Encode mật khẩu để xử lý ký tự đặc biệt như '@'
encoded_pass = urllib.parse.quote_plus(MONGO_PASS)
DEFAULT_URI = f"mongodb+srv://{MONGO_USER}:{encoded_pass}@{MONGO_HOST}/?retryWrites=true&w=majority"
MONGO_URI = os.getenv("MONGO_URI", DEFAULT_URI)

_client = None

def get_mongo_client():
    """Khởi tạo hoặc tái sử dụng MongoClient singleton"""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    return _client

def get_database():
    """Lấy database RinRec_DB từ MongoDB Atlas"""
    client = get_mongo_client()
    return client[DB_NAME]

def get_collection_df(collection_name: str, query: dict = None, projection: dict = None) -> pd.DataFrame:
    """
    Truy vấn dữ liệu từ MongoDB collection và trả về Pandas DataFrame.
    Tự động loại bỏ trường '_id' của MongoDB.
    """
    try:
        db = get_database()
        if projection is None:
            projection = {"_id": 0}
        else:
            projection["_id"] = 0
            
        cursor = db[collection_name].find(query or {}, projection)
        data = list(cursor)
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"⚠️ Lỗi khi tải collection '{collection_name}' từ MongoDB: {e}")
        return pd.DataFrame()

def save_df_to_collection(collection_name: str, df: pd.DataFrame, drop_existing: bool = True):
    """
    Lưu DataFrame vào MongoDB collection.
    """
    if df.empty:
        print(f"⚠️ DataFrame rỗng, bỏ qua lưu vào '{collection_name}'.")
        return
    try:
        db = get_database()
        col = db[collection_name]
        if drop_existing:
            col.delete_many({})
        records = df.to_dict(orient="records")
        col.insert_many(records)
        print(f"✅ Đã lưu {len(records)} bản ghi vào collection '{collection_name}' trên MongoDB.")
    except Exception as e:
        print(f"⚠️ Lỗi khi ghi vào collection '{collection_name}': {e}")

def test_connection():
    """Kiểm tra kết nối và in danh sách collection hiện có"""
    try:
        db = get_database()
        cols = db.list_collection_names()
        print(f"✅ Kết nối MongoDB Atlas thành công! Danh sách collections trong '{DB_NAME}':")
        for c in cols:
            cnt = db[c].count_documents({})
            print(f"  - {c}: {cnt} documents")
        return True
    except Exception as e:
        print(f"❌ Kết nối MongoDB Atlas thất bại: {e}")
        return False

if __name__ == "__main__":
    test_connection()
