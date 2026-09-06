# -*- coding: utf-8 -*-
"""
backend/app/api/routes/auth.py
REST API endpoints cho Xác thực (Login) và Đăng ký (Register / Sign Up).
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from backend.app.core.auth import (
    authenticate_user,
    register_user,
    get_all_users,
    get_user_by_username_or_email,
    ROLE_TELLER,
    ROLE_LABELS
)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., description="Tên đăng nhập hoặc Email")
    password: str = Field(..., description="Mật khẩu")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, description="Tên đăng nhập (tối thiểu 3 ký tự)")
    password: str = Field(..., min_length=6, description="Mật khẩu (tối thiểu 6 ký tự)")
    full_name: str = Field(..., min_length=2, description="Họ và tên đầy đủ")
    email: Optional[str] = Field(None, description="Địa chỉ email hợp lệ")
    role: Optional[str] = Field(ROLE_TELLER, description="Vai trò: GDV, MANAGER, ADMIN")
    branch: Optional[str] = Field("Chi nhánh Hội Sở", description="Chi nhánh làm việc")


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None


@router.post("/login", response_model=AuthResponse, summary="Đăng nhập hệ thống (Username hoặc Email)")
def login_endpoint(payload: LoginRequest):
    """
    Xác thực người dùng dựa trên PBKDF2-HMAC-SHA256 kết hợp MongoDB Atlas và Fallback Local.
    Hỗ trợ đăng nhập linh hoạt bằng cả Tên đăng nhập hoặc Email.
    """
    result = authenticate_user(payload.username, payload.password)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("message", "Đăng nhập thất bại.")
        )
    return result


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Đăng ký tài khoản người dùng mới")
def register_endpoint(payload: RegisterRequest):
    """
    Đăng ký tài khoản nhân viên / giao dịch viên mới theo chuẩn kiến trúc Monorepo.
    """
    result = register_user(
        username=payload.username,
        password=payload.password,
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role or ROLE_TELLER,
        branch=payload.branch or "Chi nhánh Hội Sở"
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Đăng ký thất bại.")
        )
    return result


@router.get("/verify/{identifier}", summary="Kiểm tra sự tồn tại của tài khoản hoặc email")
def verify_identifier(identifier: str):
    user = get_user_by_username_or_email(identifier)
    return {"exists": user is not None}
