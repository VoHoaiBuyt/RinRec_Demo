# -*- coding: utf-8 -*-
"""
shared/utils/__init__.py
Common utility helpers shared across Backend and Frontend.
"""
from .helpers import (
    format_currency_vnd,
    format_cif_code,
    segment_badge_html,
    truncate_text,
    safe_float,
    safe_int,
)

__all__ = [
    "format_currency_vnd",
    "format_cif_code",
    "segment_badge_html",
    "truncate_text",
    "safe_float",
    "safe_int",
]
