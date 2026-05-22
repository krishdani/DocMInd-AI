"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "NewPass1",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    resp = await client.post("/api/auth/register", json={
        "email": "test@example.com",  # already exists
        "username": "another",
        "password": "AnotherPass1",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "weak@example.com",
        "username": "weakuser",
        "password": "weak",  # too short, no uppercase, no digit
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    resp = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    resp = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPass1",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={
        "email": "ghost@example.com",
        "password": "GhostPass1",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user):
    # First login to get tokens
    login_resp = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass1",
    })
    refresh_token = login_resp.json()["refresh_token"]

    # Use refresh token
    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, test_user, auth_headers):
    resp = await client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 403  # No bearer token


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
