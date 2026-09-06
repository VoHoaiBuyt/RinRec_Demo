# -*- coding: utf-8 -*-
"""
shared/schemas/__init__.py
Pydantic-compatible data schemas shared across Backend and Frontend.
"""
from .customer import (
    CustomerSchema,
    TransactionSchema,
    ProductSchema,
    ConsultationLogSchema,
)

__all__ = [
    "CustomerSchema",
    "TransactionSchema",
    "ProductSchema",
    "ConsultationLogSchema",
]
