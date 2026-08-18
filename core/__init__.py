"""
RinRec Core AI & Data Engine Package
Module xử lý dữ liệu, kết nối MongoDB Atlas, và thuật toán gợi ý sản phẩm tài chính (UltraGCN, LightGCN, NCF, Deep MLP, MF).
"""

from core.mongo_connector import (
    get_mongo_client,
    get_database,
    get_collection_df,
    save_df_to_collection,
    upsert_customer_face,
    get_customer_faces,
    get_customer_face,
    delete_customer_face,
    update_customer_ekyc_status,
    test_connection
)
from core.fintech_data_pipeline import run_data_pipeline

__all__ = [
    "get_mongo_client",
    "get_database",
    "get_collection_df",
    "save_df_to_collection",
    "upsert_customer_face",
    "get_customer_faces",
    "get_customer_face",
    "delete_customer_face",
    "update_customer_ekyc_status",
    "test_connection",
    "run_data_pipeline"
]
