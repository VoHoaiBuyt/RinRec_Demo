# -*- coding: utf-8 -*-
"""backend/app/api/routes/consultations.py — CRUD API cho Nhật ký Tư vấn"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

from fastapi import APIRouter, HTTPException, Query
from backend.app.core.mongo_connector import log_consultation, get_consultation_logs

router = APIRouter()


@router.get("/")
def list_logs(cif_number: str = Query(None), limit: int = Query(50, le=200)):
    """Lấy danh sách nhật ký tư vấn, tùy chọn lọc theo CIF."""
    logs = get_consultation_logs(cif_number=cif_number)
    return logs[:limit]


@router.post("/")
def create_log(data: dict):
    """Ghi nhận kết quả tư vấn & chốt đơn bán chéo."""
    required = ["cif_number", "customer_name", "product_name", "status"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise HTTPException(400, f"Thiếu trường bắt buộc: {', '.join(missing)}")
    result = log_consultation(data)
    if not result.get("success"):
        raise HTTPException(500, result.get("message", "Lỗi lưu nhật ký"))
    return result
