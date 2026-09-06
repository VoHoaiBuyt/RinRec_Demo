# -*- coding: utf-8 -*-
"""
shared/utils/helpers.py
Common utility functions used by both Backend API and Frontend Streamlit app.
"""
from typing import Optional, Union


def format_currency_vnd(amount: Union[float, int, str], suffix: str = " VND") -> str:
    """
    Định dạng số tiền sang chuỗi VND có dấu phân tách hàng nghìn.

    Examples:
        >>> format_currency_vnd(1500000)
        '1,500,000 VND'
        >>> format_currency_vnd("2000000.5")
        '2,000,001 VND'
    """
    try:
        value = round(float(str(amount).replace(",", "").replace(" VND", "").strip()))
        return f"{value:,}{suffix}"
    except (ValueError, TypeError):
        return f"{amount}{suffix}"


def format_cif_code(raw: Union[str, int, float]) -> str:
    """
    Chuẩn hóa mã CIF về dạng 'CUST_XXXX'.

    Examples:
        >>> format_cif_code(1)
        'CUST_0001'
        >>> format_cif_code("93")
        'CUST_0093'
        >>> format_cif_code("CUST_0022")
        'CUST_0022'
    """
    val = str(raw).strip()
    if val.upper().startswith("CUST_"):
        return val.upper()
    # Extract numeric part
    digits = "".join(filter(str.isdigit, val))
    if digits:
        try:
            return f"CUST_{int(digits):04d}"
        except ValueError:
            pass
    return val


def segment_badge_html(segment: str) -> str:
    """
    Trả về HTML badge hiển thị phân khúc khách hàng với màu sắc phù hợp.

    Args:
        segment: 'DIAMOND' | 'PRIME' | 'MASS'

    Returns:
        HTML string cho badge phân khúc
    """
    seg = str(segment).strip().upper()
    styles = {
        "DIAMOND": ("background:linear-gradient(135deg,#F59E0B,#D97706);color:#fff;"
                    "padding:3px 10px;border-radius:14px;font-size:0.78rem;font-weight:700;"),
        "PRIME":   ("background:linear-gradient(135deg,#6366F1,#4F46E5);color:#fff;"
                    "padding:3px 10px;border-radius:14px;font-size:0.78rem;font-weight:700;"),
        "MASS":    ("background:linear-gradient(135deg,#0EA5E9,#0284C7);color:#fff;"
                    "padding:3px 10px;border-radius:14px;font-size:0.78rem;font-weight:700;"),
    }
    labels = {
        "DIAMOND": "💎 DIAMOND",
        "PRIME":   "⭐ PRIME",
        "MASS":    "🔷 MASS",
    }
    style = styles.get(seg, styles["MASS"])
    label = labels.get(seg, seg)
    return f'<span style="{style}">{label}</span>'


def truncate_text(text: str, max_length: int = 60, ellipsis: str = "…") -> str:
    """
    Cắt ngắn chuỗi văn bản nếu vượt quá độ dài tối đa.

    Examples:
        >>> truncate_text("Hello world this is a long string", 20)
        'Hello world this is…'
    """
    if not text:
        return ""
    text = str(text).strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - len(ellipsis)] + ellipsis


def safe_float(value, default: float = 0.0) -> float:
    """
    Chuyển đổi an toàn sang float, trả về default nếu lỗi.

    Examples:
        >>> safe_float("1,500,000 VND")
        1500000.0
        >>> safe_float(None)
        0.0
    """
    if value is None:
        return default
    try:
        cleaned = str(value).replace(",", "").replace(" VND", "").replace("%", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return default


def safe_int(value, default: int = 0) -> int:
    """
    Chuyển đổi an toàn sang int, trả về default nếu lỗi.

    Examples:
        >>> safe_int("42")
        42
        >>> safe_int("not_a_number")
        0
    """
    try:
        return int(safe_float(value, float(default)))
    except (ValueError, TypeError):
        return default


def extract_match_score_int(match_score: str) -> int:
    """
    Trích xuất giá trị số nguyên từ chuỗi match_score như '92%' → 92.

    Examples:
        >>> extract_match_score_int("92%")
        92
        >>> extract_match_score_int("0.88")
        88
    """
    raw = str(match_score).replace("%", "").strip()
    try:
        val = float(raw)
        # Nếu là dạng 0.0-1.0 (xác suất) → nhân 100
        if 0.0 < val <= 1.0:
            return round(val * 100)
        return round(val)
    except (ValueError, TypeError):
        return 0


def channel_badge(channel: str) -> str:
    """
    Trả về emoji + label cho kênh giao dịch.

    Examples:
        >>> channel_badge("APP")
        '📱 VPBank NEO'
        >>> channel_badge("QUẦY")
        '🏦 Tại Quầy'
    """
    mapping = {
        "APP":    "📱 VPBank NEO",
        "ONLINE": "💻 Online Banking",
        "POS":    "💳 POS/ATM",
        "ATM":    "🏧 ATM",
        "QUẦY":   "🏦 Tại Quầy",
        "EMAIL":  "📧 Email",
        "PHONE":  "📞 Phone",
    }
    key = str(channel).strip().upper()
    return mapping.get(key, f"🔹 {channel}")
