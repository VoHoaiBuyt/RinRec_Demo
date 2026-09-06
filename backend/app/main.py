# -*- coding: utf-8 -*-
"""
backend/app/main.py
FastAPI application entrypoint for RinRec SmartAdvisor 360 Backend API.
"""
import os
import sys

_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    _fastapi_available = True
except ImportError:
    _fastapi_available = False

from backend.app.core.config import APP_NAME, APP_ENV, API_PREFIX, DEBUG


def create_app():
    if not _fastapi_available:
        raise RuntimeError("FastAPI not installed. Run: pip install fastapi uvicorn")

    app = FastAPI(
        title=f"{APP_NAME} — Backend API",
        description="REST API for RinRec Fintech Recommendation System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )

    # ─── CORS ────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if APP_ENV == "development" else [os.getenv("FRONTEND_URL", "http://localhost:8501")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Routes ──────────────────────────────────────────────────────────────
    try:
        from backend.app.api.routes.auth import router as auth_router
        from backend.app.api.routes.customers import router as customers_router
        from backend.app.api.routes.transactions import router as transactions_router
        from backend.app.api.routes.products import router as products_router
        from backend.app.api.routes.consultations import router as consultations_router

        app.include_router(auth_router,         prefix=f"{API_PREFIX}/auth",          tags=["Authentication"])
        app.include_router(customers_router,    prefix=f"{API_PREFIX}/customers",    tags=["Customers"])
        app.include_router(transactions_router, prefix=f"{API_PREFIX}/transactions", tags=["Transactions"])
        app.include_router(products_router,     prefix=f"{API_PREFIX}/products",     tags=["Products"])
        app.include_router(consultations_router,prefix=f"{API_PREFIX}/consultations",tags=["Consultations"])
    except ImportError as e:
        print(f"⚠️ Route import error (will be registered later): {e}")

    @app.get("/", tags=["Health"])
    def root():
        return {"service": APP_NAME, "env": APP_ENV, "status": "✅ Running"}

    @app.get("/health", tags=["Health"])
    @app.get(f"{API_PREFIX}/health", tags=["Health"])
    def health():
        from backend.app.core.mongo_connector import test_connection
        db_ok = test_connection()
        return {"status": "healthy" if db_ok else "degraded", "database": "connected" if db_ok else "unreachable"}

    return app


app = create_app() if _fastapi_available else None

if __name__ == "__main__":
    import uvicorn
    from backend.app.core.config import API_HOST, API_PORT
    uvicorn.run("backend.app.main:app", host=API_HOST, port=API_PORT, reload=DEBUG)
