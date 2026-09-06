# -*- coding: utf-8 -*-
"""
backend/app/api/routes/loans.py
Loans & CIC endpoints for RinRec SmartAdvisor 360.
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from backend.app.core.auth import get_current_user

router = APIRouter(prefix="/customers/{cif}", tags=["Loans & CIC"])


@router.get("/loans")
async def get_customer_loans(cif: str, user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Get all loans for a customer."""
    # Mock data (replace with actual DB query)
    return [
        {
            "loan_id": "LOAN_001",
            "loan_type": "Vay tiêu dùng",
            "amount": 50000000,
            "outstanding": 35000000,
            "term": 24,
            "interest_rate": 11.88,
            "disbursement_date": "2024-01-15",
            "maturity_date": "2026-01-15",
            "status": "ACTIVE"
        }
    ]


@router.get("/cic")
async def get_customer_cic(cif: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get CIC (Credit Information Center) data for customer."""
    # Mock data
    return {
        "updated_date": "2024-09-01",
        "num_institutions": 3,
        "total_debt": 85000000,
        "debt_group": 1,
        "bad_debt_history": []
    }
