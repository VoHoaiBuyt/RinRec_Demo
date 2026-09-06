# -*- coding: utf-8 -*-
"""
backend/app/services/recommendation_service.py
Business Logic Layer: AI Recommendation Engine với Hybrid Rule-based Re-ranking.
Kết hợp UltraGCN predictions từ MongoDB Atlas + Expert Rules (RuleGoiY) + Segment Filter.
"""
import os
import sys
import random
import logging
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

# ─── Path bootstrap ───────────────────────────────────────────────────────────
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

logger = logging.getLogger("RecommendationService")

try:
    from backend.app.core.mongo_connector import get_collection_df, get_database
except ImportError:
    from app.core.mongo_connector import get_collection_df, get_database  # type: ignore

# ─── Cấu hình mặc định ────────────────────────────────────────────────────────
TOP_K = 5
MIN_MATCH_SCORE = 75
MAX_MATCH_SCORE = 99

# Bảng gợi ý sản phẩm mặc định theo phân khúc (Fallback khi MongoDB chưa có dữ liệu đề xuất)
_SEGMENT_DEFAULT_RECS: Dict[str, List[Dict[str, Any]]] = {
    "DIAMOND": [
        {
            "Ma_SP": "SP010", "title": "Gói Tài Khoản VPBank Diamond VIP",
            "category": "Phân khúc", "price": "0 VND", "rate_or_fee": "Miễn phí quản lý",
            "value_proposition": "Đặc quyền phòng chờ VIP, RM riêng, hoàn tiền cao cấp",
            "match_score": "98%",
            "gdv_script": "Đây là gói hội viên dành riêng cho khách hàng Diamond VIP. Quý khách được hưởng dịch vụ RM riêng, phòng chờ ưu tiên và miễn toàn bộ phí giao dịch quầy.",
        },
        {
            "Ma_SP": "SP008", "title": "Tiết Kiệm Tích Lũy Bậc Thang VIP",
            "category": "Tiết kiệm", "price": "500,000,000 VND", "rate_or_fee": "6.8%/năm",
            "value_proposition": "Tối đa hóa lợi nhuận với lãi suất bậc thang đặc biệt",
            "match_score": "95%",
            "gdv_script": "Với số dư hiện tại, Quý khách có thể gửi tiết kiệm bậc thang VIP, lãi suất lên đến 6.8%/năm — cao hơn biểu lãi thông thường 1.2%.",
        },
        {
            "Ma_SP": "SP006", "title": "Bảo Hiểm Liên Kết Đầu Tư Diamond",
            "category": "Bảo hiểm", "price": "50,000,000 VND", "rate_or_fee": "Phí định kỳ hàng năm",
            "value_proposition": "Bảo vệ tài sản & tăng trưởng vốn kép dài hạn",
            "match_score": "92%",
            "gdv_script": "Gói bảo hiểm liên kết đầu tư Diamond vừa bảo vệ toàn diện vừa tăng trưởng tài sản theo thị trường — lý tưởng cho khách hàng có danh mục đầu tư lớn.",
        },
        {
            "Ma_SP": "SP001", "title": "Thẻ Tín Dụng VPBank Priority World",
            "category": "Thẻ", "price": "Hạn mức 500tr", "rate_or_fee": "45 ngày miễn lãi",
            "value_proposition": "Hoàn tiền quốc tế, đặc quyền sân golf & phòng chờ VIP toàn cầu",
            "match_score": "90%",
            "gdv_script": "Thẻ Priority World mang đặc quyền Dragon Pass, hoàn 2% tại sân bay và 1.5% toàn cầu — hoàn toàn phù hợp với lịch công tác thường xuyên của Quý khách.",
        },
        {
            "Ma_SP": "SP009", "title": "Dịch Vụ Ngoại Tệ & Kiều Hối VIP",
            "category": "Ngoại tệ", "price": "Theo nhu cầu", "rate_or_fee": "Ưu đãi 20 điểm tỷ giá",
            "value_proposition": "Chuyển tiền quốc tế 24/7 với tỷ giá ưu tiên",
            "match_score": "88%",
            "gdv_script": "VPBank ưu đãi tỷ giá ngoại tệ riêng cho khách hàng Diamond — hơn 20 điểm so với tỷ giá công bố, phù hợp với nhu cầu giao dịch quốc tế thường xuyên.",
        },
    ],
    "PRIME": [
        {
            "Ma_SP": "SP010", "title": "Gói Hội Viên VPBank Prime Priority",
            "category": "Phân khúc", "price": "0 VND", "rate_or_fee": "Miễn phí",
            "value_proposition": "Miễn phí chuyển khoản, hoàn tiền thẻ & xử lý ưu tiên",
            "match_score": "97%",
            "gdv_script": "Gói hội viên Prime Priority giúp Quý khách tiết kiệm toàn bộ phí chuyển khoản và nhận hoàn tiền mua sắm tháng — phù hợp với mức chi tiêu hiện tại.",
        },
        {
            "Ma_SP": "SP001", "title": "Thẻ Tín Dụng VPBank Step Up Cashback",
            "category": "Thẻ", "price": "Hạn mức 100tr", "rate_or_fee": "45 ngày miễn lãi",
            "value_proposition": "Hoàn 15% chi tiêu online & siêu thị, không cần đăng ký",
            "match_score": "94%",
            "gdv_script": "Thẻ Step Up hoàn 15% tự động mọi giao dịch online và 5% tại siêu thị — với thói quen chi tiêu hiện tại, Quý khách có thể tiết kiệm 2-3 triệu/tháng.",
        },
        {
            "Ma_SP": "SP008", "title": "Tiết Kiệm Trực Tuyến Prime Rate",
            "category": "Tiết kiệm", "price": "20,000,000 VND", "rate_or_fee": "6.2%/năm",
            "value_proposition": "+0.3% lãi suất thưởng khi gửi qua VPBank NEO App",
            "match_score": "91%",
            "gdv_script": "Gửi tiết kiệm online qua VPBank NEO được cộng thêm 0.3% lãi suất — với số dư 20 triệu, mỗi năm thu về thêm 60.000đ so với gửi quầy.",
        },
        {
            "Ma_SP": "SP002", "title": "Gói Vay Tiêu Dùng Tín Chấp Prime",
            "category": "Vay", "price": "Hạn mức 200tr", "rate_or_fee": "Từ 9.9%/năm",
            "value_proposition": "Giải ngân trong 5 phút qua VPBank NEO App",
            "match_score": "89%",
            "gdv_script": "Hạn mức 200 triệu với lãi suất cố định 9.9%/năm — phù hợp khi cần bổ sung tài chính ngắn hạn. Giải ngân chỉ 5 phút qua ứng dụng, không cần tài sản đảm bảo.",
        },
        {
            "Ma_SP": "SP006", "title": "Bảo Hiểm Sức Khỏe CarePlus VPBank",
            "category": "Bảo hiểm", "price": "5,000,000 VND", "rate_or_fee": "Phí năm",
            "value_proposition": "Bảo lãnh viện phí tại 300+ bệnh viện quốc tế, không cần đặt cọc",
            "match_score": "86%",
            "gdv_script": "CarePlus bảo lãnh trực tiếp tại 300 bệnh viện hàng đầu, không cần tự ứng tiền — phù hợp cho gia đình có trẻ nhỏ hoặc người cao tuổi cần chăm sóc y tế thường xuyên.",
        },
    ],
    "MASS": [
        {
            "Ma_SP": "SP001", "title": "Thẻ Thanh Toán VPBank NEO Mastercard",
            "category": "Thẻ", "price": "0 VND", "rate_or_fee": "Miễn phí trọn đời",
            "value_proposition": "Rút tiền miễn phí tại mọi ATM trong nước",
            "match_score": "96%",
            "gdv_script": "Thẻ NEO miễn phí phát hành và duy trì, rút tiền tại mọi ATM không mất phí — đặc biệt tiện lợi khi Quý khách có nhu cầu rút tiền thường xuyên.",
        },
        {
            "Ma_SP": "SP008", "title": "Tiết Kiệm Gửi Góp EasySave VPBank",
            "category": "Tiết kiệm", "price": "1,000,000 VND", "rate_or_fee": "5.8%/năm",
            "value_proposition": "Tự động trích tiền gửi hàng tháng, xây dựng quỹ dự phòng",
            "match_score": "93%",
            "gdv_script": "EasySave tự động gửi tiết kiệm mỗi tháng theo lịch của Quý khách — chỉ cần 1 triệu/tháng, sau 12 tháng tích lũy hơn 12.7 triệu kể cả lãi.",
        },
        {
            "Ma_SP": "SP002", "title": "Thấu Chi Tài Khoản Online VPBank",
            "category": "Vay", "price": "Hạn mức 30tr", "rate_or_fee": "Theo số ngày sử dụng",
            "value_proposition": "Dự phòng chi tiêu khẩn cấp, chỉ tính lãi ngày dùng",
            "match_score": "89%",
            "gdv_script": "Hạn mức thấu chi 30 triệu, chỉ tính lãi ngày thực sự sử dụng — là tấm đệm tài chính linh hoạt khi phát sinh chi tiêu bất ngờ.",
        },
        {
            "Ma_SP": "SP001", "title": "Thẻ Tín Dụng VPBank Shopee Platinum",
            "category": "Thẻ", "price": "Hạn mức 50tr", "rate_or_fee": "45 ngày miễn lãi",
            "value_proposition": "Tích điểm Shopee x4, hoàn tiền mua sắm tự động",
            "match_score": "87%",
            "gdv_script": "Thẻ Shopee Platinum nhân gấp 4 điểm thưởng cho mọi giao dịch Shopee — với thói quen mua online, Quý khách tiết kiệm thêm được 1-2 triệu mỗi tháng.",
        },
        {
            "Ma_SP": "SP006", "title": "Bảo Hiểm Tai Nạn Daily Care",
            "category": "Bảo hiểm", "price": "1,200,000 VND", "rate_or_fee": "Phí năm",
            "value_proposition": "Hỗ trợ 500.000đ/ngày nằm viện do tai nạn",
            "match_score": "85%",
            "gdv_script": "Daily Care hỗ trợ 500.000đ mỗi ngày nằm viện do tai nạn — với phí chỉ 1.2 triệu/năm, đây là lớp bảo vệ cơ bản rất phù hợp cho nhân viên làm việc thực địa.",
        },
    ],
}


# ─── Core Service Functions ───────────────────────────────────────────────────

def get_recommendations_for_customer(
    cif_code: str,
    top_k: int = TOP_K,
    apply_rules: bool = True,
) -> List[Dict[str, Any]]:
    """
    Lấy danh sách Top-K sản phẩm gợi ý cá nhân hóa cho một khách hàng cụ thể.

    Thứ tự ưu tiên:
      1. MongoDB Atlas collection 'recommendations' (kết quả UltraGCN đã tính trước)
      2. Hybrid Rule-based Re-ranking qua bảng RuleGoiY
      3. Fallback mặc định theo phân khúc nếu MongoDB không có dữ liệu

    Args:
        cif_code:    Mã CIF của khách hàng (vd: "CUST_0001")
        top_k:       Số lượng sản phẩm gợi ý trả về
        apply_rules: Có áp dụng re-ranking theo luật chuyên gia không

    Returns:
        List các dict sản phẩm gợi ý đã xếp hạng
    """
    cif_clean = str(cif_code).strip().upper()

    # 1. Lấy thông tin phân khúc khách hàng
    segment = _get_customer_segment(cif_clean)

    # 2. Thử lấy từ MongoDB Atlas collection 'recommendations'
    recs = _fetch_from_mongo(cif_clean, top_k)

    # 3. Nếu MongoDB rỗng → dùng fallback mặc định theo phân khúc
    if not recs:
        logger.info(f"[{cif_clean}] Không có dữ liệu từ MongoDB, dùng segment fallback ({segment}).")
        recs = _get_segment_fallback(segment, top_k)

    # 4. Hybrid Rule-based Re-ranking (tùy chọn)
    if apply_rules and recs:
        recs = _apply_rule_reranking(cif_clean, recs, segment)

    # 5. Đảm bảo đúng top_k và enrich metadata
    recs = _enrich_recommendations(recs[:top_k], cif_clean, segment)

    return recs


def get_top_recommendations_all_customers(
    top_k: int = TOP_K,
    segment_filter: Optional[str] = None,
    limit: int = 200,
) -> pd.DataFrame:
    """
    Lấy bảng tổng hợp gợi ý Top-K cho tất cả khách hàng (dùng cho Admin/Manager view).

    Args:
        top_k:            Số sản phẩm gợi ý mỗi khách hàng
        segment_filter:   Lọc theo phân khúc (MASS | PRIME | DIAMOND | None = tất cả)
        limit:            Giới hạn số khách hàng xử lý

    Returns:
        DataFrame tổng hợp
    """
    try:
        df = get_collection_df("recommendations")
        if df.empty:
            df = get_collection_df("purchase_history")
    except Exception as e:
        logger.warning(f"Lỗi lấy recommendations từ MongoDB: {e}")
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    if segment_filter and "segment" in df.columns:
        df = df[df["segment"].str.upper() == segment_filter.upper()]

    # Lấy top_k dòng đầu mỗi khách hàng
    if "reviewerID" in df.columns:
        df = df.groupby("reviewerID").head(top_k).reset_index(drop=True)

    return df.head(limit)


def generate_xai_script(
    cif_code: str,
    product_name: str,
    product_category: str,
    match_score: str,
    customer_segment: str,
    casa_balance: float = 0.0,
) -> str:
    """
    Sinh kịch bản tư vấn XAI (Explainable AI) cụ thể cho từng cặp KH-Sản phẩm.
    GDV đọc trực tiếp trên màn hình để tư vấn tại quầy.

    Args:
        cif_code:         Mã CIF khách hàng
        product_name:     Tên sản phẩm được gợi ý
        product_category: Nhóm sản phẩm
        match_score:      Điểm độ phù hợp (vd: "92%")
        customer_segment: Phân khúc khách hàng
        casa_balance:     Số dư tài khoản CASA hiện tại

    Returns:
        Chuỗi kịch bản tư vấn tiếng Việt dành cho GDV
    """
    seg = customer_segment.upper()
    cat = product_category.lower()
    bal_fmt = f"{casa_balance:,.0f}đ" if casa_balance > 0 else "số dư hiện tại"
    score_str = match_score.replace("%", "")

    # Kịch bản theo nhóm sản phẩm
    if "tiết kiệm" in cat or "tiền gửi" in cat:
        if seg == "DIAMOND":
            return (f"Kính thưa Quý khách, với số dư {bal_fmt}, hệ thống AI đề xuất "
                    f"'{product_name}' với mức độ phù hợp {match_score}. "
                    f"Đây là gói tiết kiệm VIP lãi suất bậc thang cao nhất, "
                    f"dành riêng cho khách hàng Diamond với hạn mức không giới hạn.")
        else:
            return (f"Quý khách có {bal_fmt} số dư nhàn rỗi. "
                    f"'{product_name}' (Độ phù hợp: {match_score}) giúp tối ưu lãi suất "
                    f"định kỳ — cao hơn lãi suất không kỳ hạn từ 3-5 lần.")

    elif "thẻ" in cat:
        if seg == "DIAMOND":
            return (f"'{product_name}' ({match_score}) mang đặc quyền Dragon Pass, "
                    f"hoàn tiền quốc tế lên đến 2% và miễn phí phòng chờ hàng không toàn cầu — "
                    f"hoàn toàn xứng tầm với danh mục Diamond của Quý khách.")
        elif seg == "PRIME":
            return (f"'{product_name}' ({match_score}) hoàn tiền tự động mọi giao dịch online. "
                    f"Với thói quen chi tiêu hiện tại, Quý khách tiết kiệm ước tính 1-2 triệu/tháng.")
        else:
            return (f"'{product_name}' ({match_score}) hoàn toàn miễn phí phát hành và duy trì, "
                    f"được dùng ngay sau khi phát hành — lý tưởng để bắt đầu xây dựng lịch sử tín dụng.")

    elif "bảo hiểm" in cat:
        return (f"'{product_name}' ({match_score}) bảo vệ toàn diện tài chính gia đình "
                f"với mức phí hợp lý. Trong tình huống không may, "
                f"Quý khách sẽ không phải lo lắng về chi phí y tế hay gánh nặng tài chính.")

    elif "vay" in cat or "tín dụng" in cat:
        return (f"'{product_name}' ({match_score}) cung cấp nguồn vốn linh hoạt với lãi suất "
                f"ưu đãi — giải ngân nhanh, thủ tục đơn giản, phù hợp khi cần bổ sung "
                f"tài chính ngắn hạn hoặc đầu tư kinh doanh.")

    elif "ngoại tệ" in cat or "quốc tế" in cat:
        return (f"'{product_name}' ({match_score}) với tỷ giá ưu đãi riêng dành cho "
                f"khách hàng {seg} — tiết kiệm chi phí chuyển đổi ngoại tệ và "
                f"giao dịch quốc tế 24/7 không giới hạn thời gian.")

    elif "đầu tư" in cat:
        return (f"'{product_name}' ({match_score}) tối ưu danh mục đầu tư tài chính "
                f"với rủi ro được kiểm soát chặt chẽ — "
                f"phù hợp với hồ sơ rủi ro và mục tiêu tài chính dài hạn của Quý khách.")

    # Kịch bản chung
    return (f"Hệ thống AI (UltraGCN) đề xuất '{product_name}' với độ phù hợp {match_score} "
            f"dựa trên phân tích hành vi giao dịch cá nhân của Quý khách. "
            f"Sản phẩm này giúp tối ưu hóa danh mục tài chính theo đúng nhu cầu và phân khúc {seg}.")


# ─── Internal Helpers ─────────────────────────────────────────────────────────

def _get_customer_segment(cif_code: str) -> str:
    """Lấy phân khúc khách hàng từ MongoDB dim_customer."""
    try:
        db = get_database()
        doc = db["dim_customer"].find_one(
            {"$or": [{"cif_code": cif_code}, {"cif_number": cif_code}]},
            {"segment": 1, "_id": 0}
        )
        if doc:
            return str(doc.get("segment", "MASS")).upper()
    except Exception as e:
        logger.debug(f"Không lấy được segment từ MongoDB: {e}")

    # Fallback: đoán từ mã CIF
    try:
        digits = int("".join(filter(str.isdigit, cif_code)))
        if digits <= 10:
            return "DIAMOND"
        if digits <= 30:
            return "PRIME"
    except Exception:
        pass
    return "MASS"


def _fetch_from_mongo(cif_code: str, top_k: int) -> List[Dict[str, Any]]:
    """Lấy danh sách gợi ý từ MongoDB collection 'recommendations'."""
    try:
        db = get_database()
        docs = list(
            db["recommendations"]
            .find({"reviewerID": cif_code}, {"_id": 0})
            .limit(top_k * 2)  # lấy dư để có chỗ re-rank
        )
        if docs:
            return docs
    except Exception as e:
        logger.debug(f"Lỗi lấy recommendations MongoDB [{cif_code}]: {e}")
    return []


def _get_segment_fallback(segment: str, top_k: int) -> List[Dict[str, Any]]:
    """Trả về danh sách gợi ý mặc định theo phân khúc."""
    seg_key = segment.upper()
    if seg_key not in _SEGMENT_DEFAULT_RECS:
        seg_key = "MASS"
    recs = _SEGMENT_DEFAULT_RECS[seg_key].copy()
    return recs[:top_k]


def _apply_rule_reranking(
    cif_code: str,
    recs: List[Dict[str, Any]],
    segment: str,
) -> List[Dict[str, Any]]:
    """
    Hybrid Rule-based Re-ranking:
    Lấy các luật từ MongoDB collection 'RuleGoiY' và điều chỉnh thứ tự gợi ý
    dựa trên hành vi giao dịch gần nhất và phân khúc.
    """
    try:
        db = get_database()

        # Lấy các luật áp dụng cho phân khúc
        rule_query = {"$or": [{"Phan_khuc": segment}, {"Phan_khuc": "ALL"}, {"Phan_khuc": {"$exists": False}}]}
        rules = list(db["RuleGoiY"].find(rule_query, {"_id": 0}).limit(20))

        if not rules:
            return recs

        # Xây dựng bộ tín hiệu từ lịch sử giao dịch gần nhất
        recent_categories: set = set()
        try:
            recent_txns = list(
                db["purchase_history"]
                .find({"reviewerID": cif_code}, {"category": 1, "_id": 0})
                .sort("transaction_time", -1)
                .limit(10)
            )
            recent_categories = {t.get("category", "") for t in recent_txns}
        except Exception:
            pass

        # Tính điểm boost cho mỗi sản phẩm dựa trên luật khớp
        boosted: List[tuple] = []
        for rec in recs:
            boost = 0.0
            prod_name = str(rec.get("title", "")).lower()
            prod_cat = str(rec.get("category", "")).lower()

            for rule in rules:
                rule_trigger = str(rule.get("Trigger_Tag", "")).lower()
                rule_prod = str(rule.get("Product_Code", "")).upper()
                rule_weight = float(rule.get("Weight", 1.0) or 1.0)
                rule_nhom = str(rule.get("Nhom_SP", "")).lower()

                # Khớp theo nhóm sản phẩm
                if rule_nhom and rule_nhom in prod_cat:
                    boost += rule_weight * 0.5

                # Khớp theo mã sản phẩm
                if rule_prod and rule_prod == str(rec.get("Ma_SP", "")).upper():
                    boost += rule_weight * 1.0

                # Khớp theo trigger từ lịch sử giao dịch
                if rule_trigger:
                    for cat in recent_categories:
                        if rule_trigger in str(cat).lower():
                            boost += rule_weight * 0.8
                            break

            boosted.append((boost, rec))

        # Sắp xếp giảm dần theo điểm boost, giữ thứ tự ban đầu khi điểm bằng nhau
        boosted.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in boosted]

    except Exception as e:
        logger.warning(f"Lỗi rule re-ranking [{cif_code}]: {e}")
        return recs


def _enrich_recommendations(
    recs: List[Dict[str, Any]],
    cif_code: str,
    segment: str,
) -> List[Dict[str, Any]]:
    """
    Enrich dữ liệu gợi ý: đảm bảo đủ các trường cần thiết,
    điều chỉnh match_score thực tế và sinh gdv_script nếu còn thiếu.
    """
    enriched = []
    for idx, rec in enumerate(recs):
        item = dict(rec)

        # Đảm bảo match_score có định dạng đúng
        score_raw = str(item.get("match_score", "")).replace("%", "").strip()
        try:
            score_int = int(float(score_raw))
        except ValueError:
            # Sinh điểm giảm dần từ 97% → theo rank
            score_int = max(MIN_MATCH_SCORE, MAX_MATCH_SCORE - idx * 3 - random.randint(0, 2))
        item["match_score"] = f"{min(MAX_MATCH_SCORE, score_int)}%"

        # Sinh gdv_script nếu chưa có hoặc rỗng
        if not item.get("gdv_script", "").strip():
            item["gdv_script"] = generate_xai_script(
                cif_code=cif_code,
                product_name=item.get("title", "Sản phẩm"),
                product_category=item.get("category", "Tài chính"),
                match_score=item["match_score"],
                customer_segment=segment,
            )

        # Đảm bảo các trường tối thiểu luôn tồn tại
        item.setdefault("reviewerID", cif_code)
        item.setdefault("segment", segment)
        item.setdefault("brand", "VPBank Financial")
        item.setdefault("rate_or_fee", "Theo biểu phí chuẩn VPBank")
        item.setdefault("value_proposition", "Giải pháp tài chính tối ưu")

        enriched.append(item)

    return enriched


# ─── API-friendly wrappers ────────────────────────────────────────────────────

def recommend_for_api(cif_code: str, top_k: int = TOP_K) -> Dict[str, Any]:
    """
    Wrapper chuẩn cho FastAPI endpoint — trả về dict JSON serializable.

    Returns:
        {
          "cif_code": str,
          "segment": str,
          "total": int,
          "recommendations": List[Dict]
        }
    """
    segment = _get_customer_segment(cif_code)
    recs = get_recommendations_for_customer(cif_code, top_k=top_k, apply_rules=True)
    return {
        "cif_code": cif_code,
        "segment": segment,
        "total": len(recs),
        "recommendations": recs,
    }
