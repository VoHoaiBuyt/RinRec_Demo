# -*- coding: utf-8 -*-
"""backend/app/api/routes/transactions.py — CRUD API cho Giao dịch"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

from fastapi import APIRouter, HTTPException, Query
from backend.app.core.mongo_connector import get_collection_df, add_transaction

router = APIRouter()


@router.get("/")
def list_transactions(limit: int = Query(100, le=1000), cif_code: str = Query(None)):
    """Lấy danh sách giao dịch, tùy chọn lọc theo CIF."""
    df = get_collection_df("purchase_history")
    if df.empty:
        return []
    if cif_code and "reviewerID" in df.columns:
        df = df[df["reviewerID"].str.upper() == cif_code.upper()]
    return df.head(limit).to_dict(orient="records")


@router.post("/")
def create_transaction(data: dict):
    """Ghi nhận giao dịch mới tại quầy."""
    required = ["cif_number", "service_name", "amount"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise HTTPException(400, f"Thiếu trường bắt buộc: {', '.join(missing)}")
    result = add_transaction(data)
    if not result.get("success"):
        raise HTTPException(500, result.get("message", "Lỗi ghi giao dịch"))
    return result
