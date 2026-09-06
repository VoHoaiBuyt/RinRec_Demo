# -*- coding: utf-8 -*-
"""
shared/schemas/customer_schema.py
Pydantic schemas for Customer CRUD operations.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class CustomerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^0\d{9}$")
    address: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=120)
    gender: Optional[str] = Field(None, pattern=r"^(M|F)$")
    income: Optional[str] = None  # Encrypted, stored as string
    segment: Optional[str] = Field(None, pattern=r"^(MASS|PRIME|DIAMOND)$")


class CustomerCreate(CustomerBase):
    cif: str = Field(..., pattern=r"^CUST_\d{4}$")


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^0\d{9}$")
    address: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=120)
    gender: Optional[str] = Field(None, pattern=r"^(M|F)$")
    income: Optional[str] = None
    segment: Optional[str] = Field(None, pattern=r"^(MASS|PRIME|DIAMOND)$")


class CustomerResponse(CustomerBase):
    cif: str
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True
