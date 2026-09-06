# -*- coding: utf-8 -*-
"""backend/app/api/routes/products.py — CRUD API cho Sản phẩm"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

from fastapi import APIRouter, HTTPException, Query
from backend.app.core.mongo_connector import get_collection_df, add_product

router = APIRouter()


@router.get("/")
def list_products(nhom: str = Query(None), phan_khuc: str = Query(None)):
    """Lấy danh mục sản phẩm tài chính, tùy chọn lọc theo nhóm hoặc phân khúc."""
    query = {}
    if nhom:
        query["Nhom"] = nhom
    if phan_khuc:
        query["Phan_khuc"] = {"$in": [phan_khuc.upper(), "ALL"]}
    df = get_collection_df("DanhMucSanPham", query=query)
    if df.empty:
        return []
    return df.sort_values("Uu_tien", ascending=True).to_dict(orient="records")


@router.post("/")
def create_product(data: dict):
    """Thêm sản phẩm tài chính mới vào danh mục."""
    if not data.get("Ten_san_pham"):
        raise HTTPException(400, "Ten_san_pham là bắt buộc")
    result = add_product(data)
    if not result.get("success"):
        raise HTTPException(500, result.get("message", "Lỗi thêm sản phẩm"))
    return result
