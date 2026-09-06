# -*- coding: utf-8 -*-
"""
backend/app/core/config.py
Centralized configuration management for RinRec Backend.
Loads from environment variables or .env file (auto-detected).
"""
import os
import urllib.parse
from pathlib import Path

# ─── Auto-load .env file ────────────────────────────────────────────────────
def _load_env():
    """Search for .env file in current dir and up to 3 parent directories."""
    search_dirs = [
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent,
        Path(__file__).resolve().parent.parent.parent,
        Path(__file__).resolve().parent.parent.parent.parent,
    ]
    for d in search_dirs:
        env_path = d / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
            break

_load_env()

# ─── Streamlit Secrets fallback ──────────────────────────────────────────────
try:
    import streamlit as _st
    if hasattr(_st, "secrets"):
        for _k in ["MONGO_USER", "MONGO_PASS", "MONGO_HOST", "MONGO_DB_NAME", "MONGO_URI"]:
            if _k in _st.secrets and _k not in os.environ:
                os.environ[_k] = str(_st.secrets[_k])
except Exception:
    pass

# ─── MongoDB Atlas Settings ──────────────────────────────────────────────────
MONGO_USER: str = os.getenv("MONGO_USER", "rinrec_ad")
MONGO_PASS: str = os.getenv("MONGO_PASS", "Hoaibuyt05@")
MONGO_HOST: str = os.getenv("MONGO_HOST", "cluster0.t52ffqx.mongodb.net")
DB_NAME: str    = os.getenv("MONGO_DB_NAME", "RinRec_DB")

_encoded_pass = urllib.parse.quote_plus(MONGO_PASS)
DEFAULT_URI = f"mongodb+srv://{MONGO_USER}:{_encoded_pass}@{MONGO_HOST}/?retryWrites=true&w=majority"
MONGO_URI: str = os.getenv("MONGO_URI", DEFAULT_URI)

# ─── App Settings ────────────────────────────────────────────────────────────
APP_NAME: str    = os.getenv("APP_NAME", "RinRec SmartAdvisor 360")
APP_ENV: str     = os.getenv("APP_ENV", "development")   # development | production
DEBUG: bool      = APP_ENV != "production"

# ─── API Settings ────────────────────────────────────────────────────────────
API_HOST: str    = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int    = int(os.getenv("API_PORT", "8000"))
API_PREFIX: str  = "/api/v1"

# ─── Frontend Settings ───────────────────────────────────────────────────────
STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))

# ─── Face Engine Settings ────────────────────────────────────────────────────
FACE_ENGINE_ENABLED: bool = os.getenv("FACE_ENGINE_ENABLED", "true").lower() == "true"
FACE_MIN_CONFIDENCE: float = float(os.getenv("FACE_MIN_CONFIDENCE", "0.55"))
