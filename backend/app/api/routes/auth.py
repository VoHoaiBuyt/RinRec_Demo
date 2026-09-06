# -*- coding: utf-8 -*-
"""
backend/app/api/routes/auth.py
Authentication endpoints: /login, /refresh, /logout for RinRec SmartAdvisor 360.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.core.auth import (
    authenticate_user,
    register_user,
    revoke_refresh_token,
    get_current_user,
)
from backend.app.core.security import (
    create_access_token,
    decode_refresh_token,
    get_rate_limiter,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = get_rate_limiter()


# ─── Request/Response Models ──────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, description="Username or email")
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[dict] = None


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    email: Optional[str] = None
    branch: str = "Chi nhánh Hội Sở"


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None


class LogoutRequest(BaseModel):
    refresh_token: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")  # Rate limit: 10 login attempts per minute per IP
async def login(request: LoginRequest):
    """
    Login endpoint: returns JWT access + refresh tokens.
    
    - **username**: Username or email
    - **password**: Password
    
    Returns:
    - access_token: JWT access token (30min expiry)
    - refresh_token: JWT refresh token (7 days expiry)
    - user: User profile (without password_hash)
    """
    result = authenticate_user(request.username, request.password)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("message", "Authentication failed"),
        )
    
    return LoginResponse(
        success=True,
        message=result["message"],
        access_token=result.get("access_token"),
        refresh_token=result.get("refresh_token"),
        user=result.get("user"),
    )


@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")  # Rate limit: 5 registrations per minute per IP
async def register(request: RegisterRequest):
    """
    Register a new user account (self-service).
    
    Default role: Teller (GDV).
    Admin can change role later via /users endpoint.
    """
    result = register_user(
        username=request.username,
        password=request.password,
        full_name=request.full_name,
        email=request.email,
        branch=request.branch,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Registration failed"),
        )
    
    # Auto-login after registration
    login_result = authenticate_user(request.username, request.password)
    
    return LoginResponse(
        success=True,
        message=result["message"],
        access_token=login_result.get("access_token"),
        refresh_token=login_result.get("refresh_token"),
        user=login_result.get("user"),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token (obtained from /login)
    
    Returns:
    - New access token (refresh token remains valid)
    """
    payload = decode_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing subject",
        )
    
    # TODO: verify refresh token exists in MongoDB users.tokens[]
    # (skip for now, assume valid if JWT signature is valid)
    
    # Generate new access token
    new_access_token = create_access_token({"sub": username})
    
    return RefreshResponse(
        success=True,
        message="Access token refreshed",
        access_token=new_access_token,
    )


@router.post("/logout")
async def logout(request: LogoutRequest, user: dict = Depends(get_current_user)):
    """
    Logout: revoke refresh token.
    
    - **refresh_token**: Refresh token to revoke
    
    Requires valid access token in Authorization header.
    """
    result = revoke_refresh_token(user["username"], request.refresh_token)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Logout failed"),
        )
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """
    Get current user profile (requires valid access token).
    """
    return {"success": True, "user": user}
