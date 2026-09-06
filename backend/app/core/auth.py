# -*- coding: utf-8 -*-
"""
backend/app/core/auth.py
Module Quản lý Xác thực & Phân quyền (Authentication & RBAC).
Refactored: JWT-based auth, refresh tokens stored in MongoDB users.tokens[].
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ─── Path bootstrap ───────────────────────────────────────────────────────────
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from backend.app.core.db_connector import get_db_connector
    from backend.app.core.security import (
        hash_password, verify_password,
        create_access_token, create_refresh_token,
        decode_access_token, decode_refresh_token,
    )
except ImportError:
    from app.core.db_connector import get_db_connector  # type: ignore
    from app.core.security import (  # type: ignore
        hash_password, verify_password,
        create_access_token, create_refresh_token,
        decode_access_token, decode_refresh_token,
    )

logger = logging.getLogger(__name__)

# HTTPBearer scheme for Authorization header
security = HTTPBearer()

# ─── Hằng số Vai trò (Roles) ──────────────────────────────────────────────────
ROLE_TELLER     = "GDV"
ROLE_MANAGER    = "MANAGER"
ROLE_ADMIN      = "ADMIN"
ROLE_COMPLIANCE = "COMPLIANCE"

ROLE_LABELS = {
    ROLE_TELLER:     "🏢 Giao Dịch Viên",
    ROLE_MANAGER:    "📊 Giám Đốc Chi Nhánh",
    ROLE_ADMIN:      "🛡️ Quản Trị Viên Hệ Thống",
    ROLE_COMPLIANCE: "📋 Kiểm Soát Tuân Thủ",
}
ROLE_BADGE_CLASSES = {
    ROLE_TELLER:     "badge-mass",
    ROLE_MANAGER:    "badge-prime",
    ROLE_ADMIN:      "badge-diamond",
    ROLE_COMPLIANCE: "badge-secure",
}

FALLBACK_USERS_FILE = os.path.join(os.path.dirname(__file__), "users_fallback.json")


# ─── JWT Dependency Injection ─────────────────────────────────────────────────

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency: Extract and verify JWT access token from Authorization header.
    Returns user dict if valid, raises 401 if invalid/expired.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
    
    # Fetch user from DB
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    if user.get("status") != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account locked")
    
    return user


def require_role(*allowed_roles: str):
    """
    RBAC decorator factory: returns a FastAPI dependency that checks user role.
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(ROLE_ADMIN))])
    """
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {allowed_roles}"
            )
        return user
    return role_checker


# ─── Default Users ────────────────────────────────────────────────────────────

def get_default_users() -> List[Dict[str, Any]]:
    """Tài khoản Admin mặc định — nạp từ .env hoặc biến môi trường."""
    now_str = datetime.utcnow().isoformat()
    return [{
        "username":      os.getenv("ADMIN_USERNAME", "admin"),
        "password_hash": hash_password(os.getenv("ADMIN_PASSWORD", "Admin@123")),
        "full_name":     os.getenv("ADMIN_FULLNAME", "TS. Trần Anh Tuấn"),
        "user_code":     os.getenv("ADMIN_USER_CODE", "VP8000"),
        "role":          ROLE_ADMIN,
        "branch":        os.getenv("ADMIN_BRANCH", "Chi nhánh Hội Sở"),
        "status":        "ACTIVE",
        "created_at":    now_str,
        "tokens":        [],
    }]


# ─── Fallback JSON ────────────────────────────────────────────────────────────

def _save_fallback_users(users: List[Dict[str, Any]]):
    try:
        clean = [{k: v for k, v in u.items() if k != "_id"} for u in users]
        with open(FALLBACK_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(clean, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Cannot save fallback users: {e}")


def _load_fallback_users() -> List[Dict[str, Any]]:
    if os.path.exists(FALLBACK_USERS_FILE):
        try:
            with open(FALLBACK_USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    defaults = get_default_users()
    _save_fallback_users(defaults)
    return defaults


# ─── MongoDB User Operations (refactored with db_connector) ───────────────────

def init_users_collection():
    """Khởi tạo / Đồng bộ tài khoản mặc định vào MongoDB collection 'users'."""
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        existing = {u.get("username", "").lower() for u in col.find({}, limit=1000)}
        missing = [u for u in get_default_users() if u.get("username", "").lower() not in existing]
        if missing:
            for user in missing:
                col.insert_one(dict(user))
            logger.info(f"Initialized {len(missing)} default users")
    except Exception as e:
        logger.warning(f"MongoDB init_users_collection failed: {e}, using fallback")
        _load_fallback_users()


def get_all_users() -> List[Dict[str, Any]]:
    """Lấy tất cả tài khoản từ MongoDB (fallback: JSON)."""
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        users = list(col.find({}, limit=1000))
        # Remove _id for serialization
        users = [{k: v for k, v in u.items() if k != "_id"} for u in users]
        if users:
            _save_fallback_users(users)
            return users
    except Exception as e:
        logger.warning(f"get_all_users MongoDB error: {e}")
    return _load_fallback_users()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Tìm tài khoản theo username."""
    uname = str(username).strip().lower()
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        user = col.find_one({"username": uname})
        if user:
            return {k: v for k, v in user.items() if k != "_id"}
    except Exception as e:
        logger.warning(f"get_user_by_username MongoDB error: {e}")
    
    # Fallback
    return next((u for u in _load_fallback_users() if u.get("username", "").lower() == uname), None)


def get_user_by_username_or_email(identifier: str) -> Optional[Dict[str, Any]]:
    """Tìm tài khoản theo username hoặc email."""
    ident = str(identifier).strip().lower()
    for u in get_all_users():
        if u.get("username", "").lower() == ident or u.get("email", "").lower() == ident:
            return u
    return None


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """
    Xác thực đăng nhập (hỗ trợ Username và Email) — trả về JWT tokens nếu thành công.
    Returns: {success, message, user?, access_token?, refresh_token?}
    """
    init_users_collection()
    ident = str(username).strip().lower()
    if not ident or not password:
        return {"success": False, "message": "Vui lòng nhập tên đăng nhập/email và mật khẩu."}
    
    user = get_user_by_username_or_email(ident)
    if not user:
        return {"success": False, "message": "Tài khoản hoặc email không tồn tại trên hệ thống."}
    
    if user.get("status") != "ACTIVE":
        return {"success": False, "message": "Tài khoản bị khóa. Vui lòng liên hệ Admin."}
    
    if not verify_password(password, user.get("password_hash", "")):
        return {"success": False, "message": "Mật khẩu không chính xác."}
    
    # Generate JWT tokens
    token_data = {"sub": user["username"], "role": user.get("role", ROLE_TELLER)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user["username"]})
    
    # Store refresh token in MongoDB users.tokens[]
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        col.update_one(
            {"username": user["username"]},
            {"$push": {"tokens": {
                "refresh_token": refresh_token,
                "created_at": datetime.utcnow().isoformat(),
            }}}
        )
    except Exception as e:
        logger.warning(f"Failed to store refresh token: {e}")
    
    return {
        "success": True,
        "message": "Đăng nhập thành công!",
        "user": {k: v for k, v in user.items() if k not in ("password_hash", "tokens", "_id")},
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def register_user(username: str, password: str, full_name: str,
                  email: Optional[str] = None, role: str = ROLE_TELLER,
                  branch: str = "Chi nhánh Hội Sở") -> Dict[str, Any]:
    """Đăng ký tài khoản người dùng mới (hỗ trợ form Sign Up tự phục vụ)."""
    uname = str(username).strip().lower()
    if len(uname) < 3:
        return {"success": False, "message": "Tên đăng nhập phải từ 3 ký tự."}
    if len(password) < 6:
        return {"success": False, "message": "Mật khẩu phải từ 6 ký tự."}
    if not full_name or not full_name.strip():
        return {"success": False, "message": "Vui lòng nhập Họ và Tên."}
    
    if get_user_by_username(uname):
        return {"success": False, "message": f"Tên đăng nhập '{uname}' đã tồn tại."}
    
    clean_email = str(email).strip().lower() if email else f"{uname}@vpbank.com.vn"
    if email and ("@" not in clean_email or "." not in clean_email):
        return {"success": False, "message": "Địa chỉ email không hợp lệ."}
    
    # Check email duplication
    if any(u.get("email", "").lower() == clean_email for u in get_all_users()):
        return {"success": False, "message": f"Email '{clean_email}' đã được đăng ký."}
    
    if role not in ROLE_LABELS:
        role = ROLE_TELLER
    
    user_code = f"VP{os.urandom(2).hex().upper()}"
    new_user = {
        "username":      uname,
        "email":         clean_email,
        "password_hash": hash_password(password),
        "full_name":     full_name.strip(),
        "user_code":     user_code,
        "role":          role,
        "branch":        branch.strip(),
        "status":        "ACTIVE",
        "created_at":    datetime.utcnow().isoformat(),
        "tokens":        [],  # For refresh tokens
    }
    
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        col.insert_one(new_user.copy())
        logger.info(f"User '{uname}' registered in MongoDB")
    except Exception as e:
        logger.warning(f"MongoDB insert failed: {e}")
    
    # Fallback save
    users = _load_fallback_users()
    users.append(new_user)
    _save_fallback_users(users)
    
    return {
        "success": True,
        "message": f"Đăng ký tài khoản '{uname}' thành công! Bạn có thể đăng nhập ngay.",
        "user": {k: v for k, v in new_user.items() if k not in ("password_hash", "tokens")}
    }


def create_user(username: str, password: str, full_name: str,
                user_code: str, role: str, branch: str = "Chi nhánh Hội Sở") -> Dict[str, Any]:
    """Tạo tài khoản nhân viên mới (Admin only)."""
    uname = str(username).strip().lower()
    if len(uname) < 3:
        return {"success": False, "message": "Tên đăng nhập phải từ 3 ký tự."}
    if len(password) < 6:
        return {"success": False, "message": "Mật khẩu phải từ 6 ký tự."}
    if not full_name:
        return {"success": False, "message": "Vui lòng nhập Họ và Tên."}
    if role not in ROLE_LABELS:
        return {"success": False, "message": f"Vai trò không hợp lệ ({role})."}
    if get_user_by_username(uname):
        return {"success": False, "message": f"Tên đăng nhập '{uname}' đã tồn tại."}

    new_user = {
        "username":      uname,
        "password_hash": hash_password(password),
        "full_name":     full_name.strip(),
        "user_code":     user_code.strip() if user_code else f"VP{os.urandom(2).hex().upper()}",
        "role":          role,
        "branch":        branch.strip(),
        "status":        "ACTIVE",
        "created_at":    datetime.utcnow().isoformat(),
        "tokens":        [],
    }
    
    mongo_saved = False
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        col.insert_one(new_user.copy())
        mongo_saved = True
    except Exception as e:
        logger.warning(f"MongoDB create_user failed: {e}")

    users = _load_fallback_users()
    users.append(new_user)
    _save_fallback_users(users)

    db_msg = "MongoDB & Fallback" if mongo_saved else "Fallback Only"
    return {"success": True, "message": f"Đã tạo tài khoản '{uname}' [{ROLE_LABELS.get(role)}] ({db_msg})."}


def update_user_role(username: str, new_role: str) -> Dict[str, Any]:
    """Cập nhật vai trò người dùng."""
    uname = str(username).strip().lower()
    if new_role not in ROLE_LABELS:
        return {"success": False, "message": "Vai trò không hợp lệ."}
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        col.update_one({"username": uname}, {"$set": {"role": new_role}})
    except Exception as e:
        logger.warning(f"MongoDB update role failed: {e}")
    
    users = _load_fallback_users()
    for u in users:
        if u.get("username", "").lower() == uname:
            u["role"] = new_role
            break
    _save_fallback_users(users)
    return {"success": True, "message": f"Đã cập nhật vai trò '{uname}' → '{ROLE_LABELS.get(new_role)}'."}


def toggle_user_status(username: str) -> Dict[str, Any]:
    """Khóa / Mở khóa tài khoản (ACTIVE ↔ LOCKED)."""
    uname = str(username).strip().lower()
    user = get_user_by_username(uname)
    if not user:
        return {"success": False, "message": "Không tìm thấy người dùng."}
    new_status = "LOCKED" if user.get("status") == "ACTIVE" else "ACTIVE"
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        col.update_one({"username": uname}, {"$set": {"status": new_status}})
    except Exception as e:
        logger.warning(f"MongoDB toggle status failed: {e}")
    
    users = _load_fallback_users()
    for u in users:
        if u.get("username", "").lower() == uname:
            u["status"] = new_status
            break
    _save_fallback_users(users)
    label = "MỞ KHÓA" if new_status == "ACTIVE" else "ĐÃ KHÓA"
    return {"success": True, "message": f"Đã {label} tài khoản '{uname}'."}


def reset_user_password(username: str, new_password: str) -> Dict[str, Any]:
    """Reset mật khẩu người dùng."""
    uname = str(username).strip().lower()
    if len(new_password) < 6:
        return {"success": False, "message": "Mật khẩu mới phải từ 6 ký tự."}
    new_hash = hash_password(new_password)
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        col.update_one({"username": uname}, {"$set": {"password_hash": new_hash}})
    except Exception as e:
        logger.warning(f"MongoDB reset password failed: {e}")
    
    users = _load_fallback_users()
    for u in users:
        if u.get("username", "").lower() == uname:
            u["password_hash"] = new_hash
            break
    _save_fallback_users(users)
    return {"success": True, "message": f"Đã đổi mật khẩu thành công cho '{uname}'."}


def revoke_refresh_token(username: str, refresh_token: str) -> Dict[str, Any]:
    """
    Revoke (remove) a refresh token from user's tokens array.
    Used for logout.
    """
    try:
        connector = get_db_connector()
        col = connector.get_collection("users")
        col.update_one(
            {"username": username},
            {"$pull": {"tokens": {"refresh_token": refresh_token}}}
        )
        return {"success": True, "message": "Refresh token revoked"}
    except Exception as e:
        logger.error(f"revoke_refresh_token failed: {e}")
        return {"success": False, "message": str(e)}
