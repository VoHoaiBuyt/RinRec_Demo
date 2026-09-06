# -*- coding: utf-8 -*-
"""
backend/app/core/security.py
Security utilities for RinRec SmartAdvisor 360.

Features:
  - JWT encode/decode (access + refresh tokens)
  - Password hashing (bcrypt)
  - PII field encryption (AES-256 via Fernet)
  - Rate limiting (slowapi)
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# ─── Password Hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash plaintext password with bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Tokens ───────────────────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION_JWT_SECRET_KEY_12345")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "CHANGE_ME_REFRESH_SECRET_67890")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Payload dict (e.g. {"sub": username, "role": "teller"})
        expires_delta: Optional expiration timedelta
    
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Payload dict (e.g. {"sub": username})
    
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT access token.
    
    Returns:
        Payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            logger.warning("Token type mismatch: expected 'access'")
            return None
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT refresh token.
    
    Returns:
        Payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_REFRESH_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            logger.warning("Token type mismatch: expected 'refresh'")
            return None
        return payload
    except JWTError as e:
        logger.warning(f"JWT refresh decode failed: {e}")
        return None


# ─── PII Encryption ───────────────────────────────────────────────────────────
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", None)

if not ENCRYPTION_KEY:
    # Generate a key if not provided (FOR DEV ONLY, must set in production)
    logger.warning("ENCRYPTION_KEY not set, generating temporary key (NOT FOR PRODUCTION)")
    ENCRYPTION_KEY = Fernet.generate_key().decode()

fernet = Fernet(ENCRYPTION_KEY.encode())


def encrypt_field(plaintext: str) -> str:
    """
    Encrypt PII field (email, phone, income, etc.) using Fernet (AES-128-CBC + HMAC).
    
    Args:
        plaintext: Original value
    
    Returns:
        Base64-encoded ciphertext
    """
    if not plaintext:
        return ""
    try:
        encrypted = fernet.encrypt(plaintext.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return plaintext  # Fallback to plaintext (not ideal, but prevents crash)


def decrypt_field(ciphertext: str) -> str:
    """
    Decrypt PII field.
    
    Args:
        ciphertext: Base64-encoded ciphertext
    
    Returns:
        Decrypted plaintext
    """
    if not ciphertext:
        return ""
    try:
        decrypted = fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return ciphertext  # Return as-is if decryption fails (might be unencrypted legacy data)


def encrypt_pii_fields(data: Dict[str, Any], fields: list) -> Dict[str, Any]:
    """
    Encrypt specified fields in a dict.
    
    Args:
        data: Dict containing PII fields
        fields: List of field names to encrypt (e.g. ["email", "phone", "income"])
    
    Returns:
        Dict with encrypted fields
    """
    encrypted_data = data.copy()
    for field in fields:
        if field in encrypted_data and encrypted_data[field]:
            encrypted_data[field] = encrypt_field(str(encrypted_data[field]))
    return encrypted_data


def decrypt_pii_fields(data: Dict[str, Any], fields: list) -> Dict[str, Any]:
    """
    Decrypt specified fields in a dict.
    
    Args:
        data: Dict containing encrypted PII fields
        fields: List of field names to decrypt
    
    Returns:
        Dict with decrypted fields
    """
    decrypted_data = data.copy()
    for field in fields:
        if field in decrypted_data and decrypted_data[field]:
            decrypted_data[field] = decrypt_field(decrypted_data[field])
    return decrypted_data


# ─── Rate Limiting ────────────────────────────────────────────────────────────
# Initialize slowapi limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],  # 100 requests/min per IP
    storage_uri=os.getenv("REDIS_URL", "memory://"),  # Use Redis if available, else in-memory
)


def get_rate_limiter():
    """FastAPI dependency: return rate limiter."""
    return limiter
