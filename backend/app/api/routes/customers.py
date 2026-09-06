# -*- coding: utf-8 -*-
"""backend/app/api/routes/customers.py — CRUD API cho Khách hàng"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

from fastapi import APIRouter, HTTPException, Query
from backend.app.core.mongo_connector import get_collection_df, create_customer

router = APIRouter()


@router.get("/")
def list_customers(limit: int = Query(50, le=500), segment: str = Query(None)):
    """Lấy danh sách khách hàng, tùy chọn lọc theo phân khúc."""
    query = {"segment": segment.upper()} if segment else {}
    df = get_collection_df("dim_customer", query=query)
    if df.empty:
        return []
    cols = ["customer_id", "cif_number", "cif_code", "full_name", "segment",
            "phone_number", "casa_balance", "kyc_biometric_status"]
    existing_cols = [c for c in cols if c in df.columns]
    return df[existing_cols].head(limit).to_dict(orient="records")


@router.get("/{cif_code}")
def get_customer(cif_code: str):
    """Lấy hồ sơ 360° của một khách hàng theo CIF code."""
    df = get_collection_df("dim_customer")
    if df.empty:
        raise HTTPException(404, "Không có dữ liệu khách hàng")
    mask = (
        df.get("cif_code", df.get("cif_number", "")).str.upper() == cif_code.upper()
    ) if "cif_code" in df.columns else (
        df["cif_number"].str.upper() == cif_code.upper()
    )
    row = df[mask]
    if row.empty:
        raise HTTPException(404, f"Không tìm thấy khách hàng CIF: {cif_code}")
    return row.iloc[0].to_dict()


@router.post("/")
def onboard_customer(data: dict):
    """Tạo mới khách hàng (Onboarding CIF)."""
    if not data.get("full_name"):
        raise HTTPException(400, "full_name là bắt buộc")
    result = create_customer(data)
    if not result.get("success"):
        raise HTTPException(500, result.get("message", "Lỗi tạo khách hàng"))
    return result
