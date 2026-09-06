# -*- coding: utf-8 -*-
"""
backend/app/api/routes/recommendations.py
REST API endpoints cho Gợi ý Sản phẩm Cá nhân hóa (UltraGCN + Hybrid Rules).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

from fastapi import APIRouter, HTTPException, Query
from backend.app.services.recommendation_service import (
    recommend_for_api,
    get_top_recommendations_all_customers,
    generate_xai_script,
)

router = APIRouter()


@router.get("/{cif_code}", summary="Lấy Top-K gợi ý sản phẩm cá nhân hóa cho một khách hàng")
def get_customer_recommendations(
    cif_code: str,
    top_k: int = Query(5, ge=1, le=20, description="Số lượng sản phẩm gợi ý"),
):
    """
    Trả về danh sách Top-K sản phẩm tài chính được gợi ý cho khách hàng theo CIF,
    kết hợp UltraGCN predictions + Hybrid Rule-based Re-ranking + XAI script.
    """
    result = recommend_for_api(cif_code=cif_code.strip().upper(), top_k=top_k)
    if not result.get("recommendations"):
        raise HTTPException(404, f"Không tìm thấy gợi ý nào cho CIF: {cif_code}")
    return result


@router.get("/", summary="Lấy bảng tổng hợp gợi ý cho tất cả khách hàng")
def get_all_recommendations(
    segment: str = Query(None, description="Lọc theo phân khúc: MASS | PRIME | DIAMOND"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Trả về DataFrame tổng hợp gợi ý Top-5 cho tất cả khách hàng.
    Dùng cho Admin Dashboard / Manager overview.
    """
    df = get_top_recommendations_all_customers(
        segment_filter=segment,
        limit=limit,
    )
    if df.empty:
        return {"total": 0, "data": []}
    return {"total": len(df), "data": df.to_dict(orient="records")}


@router.post("/xai-script", summary="Sinh kịch bản tư vấn XAI cho một cặp KH-Sản phẩm")
def generate_script(payload: dict):
    """
    Sinh kịch bản tư vấn chi tiết (Explainable AI) để GDV đọc trực tiếp tại quầy.

    Payload:
        cif_code, product_name, product_category, match_score,
        customer_segment, casa_balance (optional)
    """
    required = ["cif_code", "product_name", "product_category", "match_score", "customer_segment"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        raise HTTPException(400, f"Thiếu các trường bắt buộc: {', '.join(missing)}")

    script = generate_xai_script(
        cif_code=payload["cif_code"],
        product_name=payload["product_name"],
        product_category=payload["product_category"],
        match_score=payload["match_score"],
        customer_segment=payload["customer_segment"],
        casa_balance=float(payload.get("casa_balance", 0.0)),
    )
    return {"cif_code": payload["cif_code"], "gdv_script": script}
