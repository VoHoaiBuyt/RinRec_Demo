# -*- coding: utf-8 -*-
"""
core/auth.py
Module Quản lý Xác thực & Phân quyền (Authentication & Role-Based Access Control - RBAC)
Lưu trữ thông tin người dùng trong MongoDB Atlas (Collection: 'users')
kèm cơ chế tự động Fallback file JSON nếu CSDL Cloud tạm thời mất kết nối.
"""

import os
import sys
import json
import hashlib
import binascii
from datetime import datetime
from typing import Optional, List, Dict, Any

# Đảm bảo root directory luôn có trong sys.path
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from core.mongo_connector import get_database

# Hằng số Vai trò (Roles) trong Ngân hàng
ROLE_TELLER = "GDV"          # Giao dịch viên tại quầy
ROLE_MANAGER = "MANAGER"      # Giám đốc / Trưởng phòng Chi nhánh
ROLE_ADMIN = "ADMIN"          # Quản trị viên hệ thống IT

ROLE_LABELS = {
    ROLE_TELLER: "🏢 Giao Dịch Viên",
    ROLE_MANAGER: "📊 Giám Đốc Chi Nhánh",
    ROLE_ADMIN: "🛡️ Quản Trị Viên Hệ Thống"
}

ROLE_BADGE_CLASSES = {
    ROLE_TELLER: "badge-mass",
    ROLE_MANAGER: "badge-prime",
    ROLE_ADMIN: "badge-diamond"
}

FALLBACK_USERS_FILE = os.path.join(os.path.dirname(__file__), "users_fallback.json")


def hash_password(password: str, salt: bytes = None) -> str:
    """
    Mã hóa mật khẩu sử dụng PBKDF2-HMAC-SHA256 chuẩn an toàn.
    Trả về dạng string: pbkdf2_sha256$salt_hex$hash_hex
    """
    if salt is None:
        salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    salt_hex = binascii.hexlify(salt).decode('utf-8')
    hash_hex = binascii.hexlify(hash_bytes).decode('utf-8')
    return f"pbkdf2_sha256${salt_hex}${hash_hex}"


def verify_password(password: str, stored_password_hash: str) -> bool:
    """
    Kiểm tra mật khẩu khớp với chuỗi hash đã lưu hay không.
    """
    try:
        if not stored_password_hash or not stored_password_hash.startswith("pbkdf2_sha256$"):
            return False
        parts = stored_password_hash.split("$")
        if len(parts) != 3:
            return False
        salt = binascii.unhexlify(parts[1])
        expected_hash = hash_password(password, salt)
        return stored_password_hash == expected_hash
    except Exception as e:
        print(f"⚠️ Lỗi xác thực mật khẩu: {e}")
        return False


def get_default_users() -> List[Dict[str, Any]]:
    """
    Danh sách tài khoản nhân viên mặc định ban đầu (chỉ bao gồm Admin, nạp từ .env)
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "Admin@123")
    admin_name = os.getenv("ADMIN_FULLNAME", "TS. Trần Anh Tuấn")
    admin_code = os.getenv("ADMIN_USER_CODE", "VP8000")
    admin_branch = os.getenv("ADMIN_BRANCH", "Chi nhánh Hội Sở")

    return [
        {
            "username": admin_user,
            "password_hash": hash_password(admin_pass),
            "full_name": admin_name,
            "user_code": admin_code,
            "role": ROLE_ADMIN,
            "branch": admin_branch,
            "status": "ACTIVE",
            "created_at": now_str
        }
    ]



def _save_fallback_users(users: List[Dict[str, Any]]):
    """Lưu danh sách users ra file JSON dự phòng"""
    try:
        clean_users = []
        for u in users:
            u_copy = dict(u)
            if "_id" in u_copy:
                del u_copy["_id"]
            clean_users.append(u_copy)
        with open(FALLBACK_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Không thể lưu fallback users: {e}")


def _load_fallback_users() -> List[Dict[str, Any]]:
    """Tải danh sách users từ file JSON dự phòng"""
    if os.path.exists(FALLBACK_USERS_FILE):
        try:
            with open(FALLBACK_USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default_users = get_default_users()
    _save_fallback_users(default_users)
    return default_users


def init_users_collection():
    """
    Khởi tạo / Đồng bộ các tài khoản mặc định vào collection 'users' trên MongoDB Atlas.
    """
    try:
        db = get_database()
        col = db["users"]
        default_users = get_default_users()
        existing_users = list(col.find({}, {"username": 1, "_id": 0}))
        existing_unames = {u.get("username", "").lower() for u in existing_users}
        
        missing_users = [u for u in default_users if u.get("username", "").lower() not in existing_unames]
        if missing_users:
            col.insert_many([dict(u) for u in missing_users])
            print(f"✅ Đã bổ sung {len(missing_users)} tài khoản mặc định vào MongoDB collection 'users'.")
    except Exception as e:
        print(f"⚠️ MongoDB Atlas không khả dụng ({e}), sử dụng fallback local JSON.")
        _load_fallback_users()



def get_all_users() -> List[Dict[str, Any]]:
    """
    Lấy danh sách tất cả tài khoản người dùng từ MongoDB (hoặc Fallback JSON).
    """
    try:
        db = get_database()
        col = db["users"]
        cursor = col.find({}, {"_id": 0})
        users = list(cursor)
        if users:
            _save_fallback_users(users)
            return users
    except Exception as e:
        print(f"⚠️ Lỗi kết nối MongoDB khi lấy danh sách users: {e}")
    
    return _load_fallback_users()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Tìm tài khoản người dùng theo username.
    """
    uname_clean = str(username).strip().lower()
    users = get_all_users()
    for u in users:
        if u.get("username", "").strip().lower() == uname_clean:
            return u
    return None


def get_user_by_username_or_email(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Tìm tài khoản người dùng theo username hoặc email.
    """
    ident = str(identifier).strip().lower()
    for u in get_all_users():
        if u.get("username", "").strip().lower() == ident or u.get("email", "").strip().lower() == ident:
            return u
    return None


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """
    Xác thực thông tin đăng nhập (hỗ trợ cả Username và Email).
    Trả về dict dạng: {"success": True/False, "message": str, "user": dict}
    """
    init_users_collection()
    ident = str(username).strip().lower()
    if not ident or not password:
        return {"success": False, "message": "Vui lòng nhập tên đăng nhập/email và mật khẩu."}
    
    user = get_user_by_username_or_email(ident)
    if not user:
        return {"success": False, "message": "Tài khoản hoặc email không tồn tại trên hệ thống."}
    
    if user.get("status") != "ACTIVE":
        return {"success": False, "message": "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Admin."}
    
    stored_hash = user.get("password_hash", "")
    if verify_password(password, stored_hash):
        user_info = {k: v for k, v in user.items() if k != "password_hash"}
        return {"success": True, "message": "Đăng nhập thành công!", "user": user_info}
    else:
        return {"success": False, "message": "Mật khẩu không chính xác. Vui lòng thử lại."}


def register_user(username: str, password: str, full_name: str,
                  email: Optional[str] = None, role: str = ROLE_TELLER,
                  branch: str = "Chi nhánh Hội Sở") -> Dict[str, Any]:
    """
    Đăng ký tài khoản người dùng mới (hỗ trợ form Sign Up).
    """
    uname_clean = str(username).strip().lower()
    if len(uname_clean) < 3:
        return {"success": False, "message": "Tên đăng nhập phải từ 3 ký tự."}
    if len(password) < 6:
        return {"success": False, "message": "Mật khẩu phải từ 6 ký tự."}
    if not full_name or not full_name.strip():
        return {"success": False, "message": "Vui lòng nhập Họ và Tên."}
    
    if get_user_by_username(uname_clean):
        return {"success": False, "message": f"Tên đăng nhập '{uname_clean}' đã tồn tại."}
    
    clean_email = str(email).strip().lower() if email else f"{uname_clean}@vpbank.com.vn"
    if email and ("@" not in clean_email or "." not in clean_email):
        return {"success": False, "message": "Địa chỉ email không hợp lệ."}
    
    if any(u.get("email", "").lower() == clean_email for u in get_all_users()):
        return {"success": False, "message": f"Email '{clean_email}' đã được đăng ký."}
    
    if role not in ROLE_LABELS:
        role = ROLE_TELLER
    
    user_code = f"VP{os.urandom(2).hex().upper()}"
    new_user = {
        "username":      uname_clean,
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
        "message": f"Đăng ký tài khoản '{uname_clean}' thành công! Bạn có thể đăng nhập ngay.",
        "user": {k: v for k, v in new_user.items() if k != "password_hash"}
    }


def create_user(username: str, password: str, full_name: str, user_code: str, role: str, branch: str = "Chi nhánh Hội Sở") -> Dict[str, Any]:
    """
    Tạo tài khoản người dùng mới và lưu vào MongoDB Atlas / Fallback JSON.
    """
    uname_clean = str(username).strip().lower()
    if not uname_clean or len(uname_clean) < 3:
        return {"success": False, "message": "Tên đăng nhập phải có ít nhất 3 ký tự."}
    if not password or len(password) < 6:
        return {"success": False, "message": "Mật khẩu phải từ 6 ký tự trở lên."}
    if not full_name:
        return {"success": False, "message": "Vui lòng nhập Họ và Tên nhân viên."}
    if role not in ROLE_LABELS:
        return {"success": False, "message": f"Vai trò không hợp lệ ({role})."}
    
    if get_user_by_username(uname_clean):
        return {"success": False, "message": f"Tên đăng nhập '{uname_clean}' đã được sử dụng."}
    
    new_user = {
        "username": uname_clean,
        "password_hash": hash_password(password),
        "full_name": full_name.strip(),
        "user_code": user_code.strip() if user_code else f"VP{os.urandom(2).hex().upper()}",
        "role": role,
        "branch": branch.strip() if branch else "Chi nhánh Hội Sở",
        "status": "ACTIVE",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 1. Lưu vào MongoDB Atlas
    mongo_saved = False
    try:
        db = get_database()
        col = db["users"]
        col.insert_one(new_user.copy())
        mongo_saved = True
    except Exception as e:
        print(f"⚠️ Không thể lưu user mới vào MongoDB: {e}")
    
    # 2. Đồng bộ với Local Fallback
    users = _load_fallback_users()
    users.append(new_user)
    _save_fallback_users(users)
    
    db_msg = "MongoDB Atlas & Fallback Local" if mongo_saved else "Fallback Local File"
    return {"success": True, "message": f"Đã tạo thành công tài khoản '{uname_clean}' [{ROLE_LABELS.get(role)}] ({db_msg})."}


def update_user_role(username: str, new_role: str) -> Dict[str, Any]:
    """Cập nhật vai trò (Role) của người dùng"""
    uname_clean = str(username).strip().lower()
    if new_role not in ROLE_LABELS:
        return {"success": False, "message": "Vai trò không hợp lệ."}
    
    try:
        db = get_database()
        col = db["users"]
        col.update_one({"username": uname_clean}, {"$set": {"role": new_role}})
    except Exception as e:
        print(f"⚠️ Lỗi MongoDB khi update role: {e}")
        
    users = _load_fallback_users()
    updated = False
    for u in users:
        if u.get("username", "").lower() == uname_clean:
            u["role"] = new_role
            updated = True
            break
    if updated:
        _save_fallback_users(users)
        return {"success": True, "message": f"Đã cập nhật vai trò tài khoản '{uname_clean}' thành '{ROLE_LABELS.get(new_role)}'."}
    return {"success": False, "message": "Không tìm thấy người dùng."}


def toggle_user_status(username: str) -> Dict[str, Any]:
    """Khóa / Mở khóa trạng thái người dùng (ACTIVE <-> LOCKED)"""
    uname_clean = str(username).strip().lower()
    user = get_user_by_username(uname_clean)
    if not user:
        return {"success": False, "message": "Không tìm thấy người dùng."}
    
    new_status = "LOCKED" if user.get("status") == "ACTIVE" else "ACTIVE"
    
    try:
        db = get_database()
        col = db["users"]
        col.update_one({"username": uname_clean}, {"$set": {"status": new_status}})
    except Exception as e:
        print(f"⚠️ Lỗi MongoDB khi toggle status: {e}")
        
    users = _load_fallback_users()
    for u in users:
        if u.get("username", "").lower() == uname_clean:
            u["status"] = new_status
            break
    _save_fallback_users(users)
    
    status_label = "MỞ KHÓA" if new_status == "ACTIVE" else "ĐÃ KHÓA"
    return {"success": True, "message": f"Đã {status_label} tài khoản '{uname_clean}'."}


def reset_user_password(username: str, new_password: str) -> Dict[str, Any]:
    """Reset mật khẩu cho người dùng"""
    uname_clean = str(username).strip().lower()
    if not new_password or len(new_password) < 6:
        return {"success": False, "message": "Mật khẩu mới phải có ít nhất 6 ký tự."}
    
    new_hash = hash_password(new_password)
    try:
        db = get_database()
        col = db["users"]
        col.update_one({"username": uname_clean}, {"$set": {"password_hash": new_hash}})
    except Exception as e:
        print(f"⚠️ Lỗi MongoDB khi reset password: {e}")
        
    users = _load_fallback_users()
    for u in users:
        if u.get("username", "").lower() == uname_clean:
            u["password_hash"] = new_hash
            break
    _save_fallback_users(users)
    return {"success": True, "message": f"Đã đổi mật khẩu thành công cho tài khoản '{uname_clean}'."}
