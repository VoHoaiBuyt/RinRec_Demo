# -*- coding: utf-8 -*-
"""
backend/tests/test_api.py
Pytest suite for RinRec SmartAdvisor 360 API endpoints.
"""
import pytest
from httpx import AsyncClient
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login with default admin credentials."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "admin"


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "WrongPassword"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user():
    """Test /auth/me endpoint with valid token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First login to get token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@123"}
        )
        token = login_response.json()["access_token"]
        
        # Then call /me with token
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["username"] == "admin"


@pytest.mark.asyncio
async def test_refresh_token():
    """Test refresh token endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data


@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test accessing protected endpoint without token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403  # No Authorization header
