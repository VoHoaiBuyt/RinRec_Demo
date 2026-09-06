# -*- coding: utf-8 -*-
"""
backend/app/core/auth.py
Module Quản lý Xác thực & Phân quyền (Authentication & RBAC).
Refactored: imports từ backend.app.core.mongo_connector (centralized).
"""
import os
import sys
import json
import hashlib
import binascii
from datetime import datetime
from typing import Optional, List, Dict, Any

# ─── Path bootstrap ───────────────────────────────────────────────────────────
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from backend.app.core.mongo_connector import get_database
except ImportError:
    from app.core.mongo_connector import get_database  # type: ignore

# ─── Hằng số Vai trò (Roles) ──────────────────────────────────────────────────
ROLE_TELLER  = "GDV"
ROLE_MANAGER = "MANAGER"
ROLE_ADMIN   = "ADMIN"

ROLE_LABELS = {
    ROLE_TELLER:  "🏢 Giao Dịch Viên",
    ROLE_MANAGER: "📊 Giám Đốc Chi Nhánh",
    ROLE_ADMIN:   "🛡️ Quản Trị Viên Hệ Thống",
}
ROLE_BADGE_CLASSES = {
    ROLE_TELLER:  "badge-mass",
    ROLE_MANAGER: "badge-prime",
    ROLE_ADMIN:   "badge-diamond",
}

FALLBACK_USERS_FILE = os.path.join(os.path.dirname(__file__), "users_fallback.json")


# ─── Password Helpers ─────────────────────────────────────────────────────────

def hash_password(password: str, salt: bytes = None) -> str:
    """Mã hóa mật khẩu sử dụng PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2_sha256${binascii.hexlify(salt).decode()}${binascii.hexlify(hash_bytes).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Xác minh mật khẩu so với hash đã lưu."""
    try:
        if not stored_hash or not stored_hash.startswith("pbkdf2_sha256$"):
            return False
        parts = stored_hash.split("$")
        if len(parts) != 3:
            return False
        salt = binascii.unhexlify(parts[1])
        return stored_hash == hash_password(password, salt)
    except Exception as e:
        print(f"⚠️ Lỗi verify_password: {e}")
        return False


# ─── Default Users ────────────────────────────────────────────────────────────

def get_default_users() -> List[Dict[str, Any]]:
    """Tài khoản Admin mặc định — nạp từ .env hoặc biến môi trường."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [{
        "username":      os.getenv("ADMIN_USERNAME", "admin"),
        "password_hash": hash_password(os.getenv("ADMIN_PASSWORD", "Admin@123")),
        "full_name":     os.getenv("ADMIN_FULLNAME", "TS. Trần Anh Tuấn"),
        "user_code":     os.getenv("ADMIN_USER_CODE", "VP8000"),
        "role":          ROLE_ADMIN,
        "branch":        os.getenv("ADMIN_BRANCH", "Chi nhánh Hội Sở"),
        "status":        "ACTIVE",
        "created_at":    now_str,
    }]


# ─── Fallback JSON ────────────────────────────────────────────────────────────

def _save_fallback_users(users: List[Dict[str, Any]]):
    try:
        clean = [{k: v for k, v in u.items() if k != "_id"} for u in users]
        with open(FALLBACK_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(clean, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Không thể lưu fallback users: {e}")


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


# ─── MongoDB User Operations ──────────────────────────────────────────────────

def init_users_collection():
    """Khởi tạo / Đồng bộ tài khoản mặc định vào MongoDB collection 'users'."""
    try:
        db = get_database()
        col = db["users"]
        existing = {u.get("username", "").lower() for u in col.find({}, {"username": 1, "_id": 0})}
        missing = [u for u in get_default_users() if u.get("username", "").lower() not in existing]
        if missing:
            col.insert_many([dict(u) for u in missing])
    except Exception as e:
        print(f"⚠️ MongoDB không khả dụng ({e}), dùng fallback JSON.")
        _load_fallback_users()


def get_all_users() -> List[Dict[str, Any]]:
    """Lấy tất cả tài khoản từ MongoDB (fallback: JSON)."""
    try:
        db = get_database()
        users = list(db["users"].find({}, {"_id": 0}))
        if users:
            _save_fallback_users(users)
            return users
    except Exception as e:
        print(f"⚠️ Lỗi lấy users từ MongoDB: {e}")
    return _load_fallback_users()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Tìm tài khoản theo username."""
    uname = str(username).strip().lower()
    return next((u for u in get_all_users() if u.get("username", "").lower() == uname), None)


def get_user_by_username_or_email(identifier: str) -> Optional[Dict[str, Any]]:
    """Tìm tài khoản theo username hoặc email."""
    ident = str(identifier).strip().lower()
    for u in get_all_users():
        if u.get("username", "").lower() == ident or u.get("email", "").lower() == ident:
            return u
    return None


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """Xác thực đăng nhập (hỗ trợ cả Username và Email) — trả về dict {success, message, user?}."""
    init_users_collection()
    ident = str(username).strip().lower()
    if not ident or not password:
        return {"success": False, "message": "Vui lòng nhập tên đăng nhập/email và mật khẩu."}
    user = get_user_by_username_or_email(ident)
    if not user:
        return {"success": False, "message": "Tài khoản hoặc email không tồn tại trên hệ thống."}
    if user.get("status") != "ACTIVE":
        return {"success": False, "message": "Tài khoản bị khóa. Vui lòng liên hệ Admin."}
    if verify_password(password, user.get("password_hash", "")):
        return {"success": True, "message": "Đăng nhập thành công!", "user": {k: v for k, v in user.items() if k != "password_hash"}}
    return {"success": False, "message": "Mật khẩu không chính xác."}


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
    
    # Kiểm tra trùng email
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
        "created_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    mongo_saved = False
    try:
        get_database()["users"].insert_one(new_user.copy())
        mongo_saved = True
    except Exception as e:
        print(f"⚠️ Không thể lưu vào MongoDB: {e}")

    users = _load_fallback_users()
    users.append(new_user)
    _save_fallback_users(users)

    return {
        "success": True,
        "message": f"Đăng ký tài khoản '{uname}' thành công! Bạn có thể đăng nhập ngay.",
        "user": {k: v for k, v in new_user.items() if k != "password_hash"}
    }


def create_user(username: str, password: str, full_name: str,
                user_code: str, role: str, branch: str = "Chi nhánh Hội Sở") -> Dict[str, Any]:
    """Tạo tài khoản nhân viên mới."""
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
        "created_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    mongo_saved = False
    try:
        get_database()["users"].insert_one(new_user.copy())
        mongo_saved = True
    except Exception as e:
        print(f"⚠️ Không thể lưu vào MongoDB: {e}")

    users = _load_fallback_users()
    users.append(new_user)
    _save_fallback_users(users)

    db_msg = "MongoDB Atlas & Fallback" if mongo_saved else "Fallback Local"
    return {"success": True, "message": f"Đã tạo tài khoản '{uname}' [{ROLE_LABELS.get(role)}] ({db_msg})."}


def update_user_role(username: str, new_role: str) -> Dict[str, Any]:
    """Cập nhật vai trò người dùng."""
    uname = str(username).strip().lower()
    if new_role not in ROLE_LABELS:
        return {"success": False, "message": "Vai trò không hợp lệ."}
    try:
        get_database()["users"].update_one({"username": uname}, {"$set": {"role": new_role}})
    except Exception as e:
        print(f"⚠️ Lỗi MongoDB update role: {e}")
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
        get_database()["users"].update_one({"username": uname}, {"$set": {"status": new_status}})
    except Exception as e:
        print(f"⚠️ Lỗi MongoDB toggle status: {e}")
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
        get_database()["users"].update_one({"username": uname}, {"$set": {"password_hash": new_hash}})
    except Exception as e:
        print(f"⚠️ Lỗi MongoDB reset password: {e}")
    users = _load_fallback_users()
    for u in users:
        if u.get("username", "").lower() == uname:
            u["password_hash"] = new_hash
            break
    _save_fallback_users(users)
    return {"success": True, "message": f"Đã đổi mật khẩu thành công cho '{uname}'."}
