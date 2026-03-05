"""Integration tests: Auth — login, me, unauthorized access."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_auth_data(db):
    """Clean up auth-related transient data before each test."""
    await db.execute(text(
        "DELETE FROM password_reset_tokens WHERE user_id IN "
        "(SELECT id FROM users WHERE tenant_id = :tid)"
    ), {"tid": TID})
    await db.commit()
    yield


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """POST /v1/auth/login with valid credentials should return 200 and a token."""
    resp = await client.post("/v1/auth/login", json={
        "email": "admin@test.local",
        "password": "test",
        "tenant_id": TID,
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == "00000000-0000-0000-0000-000000000100"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """POST /v1/auth/login with wrong password should return 401."""
    resp = await client.post("/v1/auth/login", json={
        "email": "admin@test.local",
        "password": "wrong-password",
        "tenant_id": TID,
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient):
    """GET /v1/auth/me with authenticated client should return user info."""
    resp = await client.get("/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@test.local"
    assert data["id"] == "00000000-0000-0000-0000-000000000100"
    assert data["role"] == "admin"
    assert data["tenant_id"] == TID


@pytest.mark.asyncio
async def test_unauthorized_no_token(seed_db, session_factory):
    """GET /v1/auth/me without auth token should return 401 or 403."""
    from app.core.db import get_db

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Tenant-ID": TID},
        ) as unauthed:
            resp = await unauthed.get("/v1/auth/me")
            assert resp.status_code in (401, 403)
    finally:
        app.dependency_overrides.clear()
