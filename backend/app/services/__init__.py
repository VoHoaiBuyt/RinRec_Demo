# -*- coding: utf-8 -*-
"""
backend/app/services/__init__.py
Business Logic Services Layer for RinRec SmartAdvisor 360.
"""
from .recommendation_service import (
    get_recommendations_for_customer,
    get_top_recommendations_all_customers,
    generate_xai_script,
    recommend_for_api,
)

__all__ = [
    "get_recommendations_for_customer",
    "get_top_recommendations_all_customers",
    "generate_xai_script",
    "recommend_for_api",
]
