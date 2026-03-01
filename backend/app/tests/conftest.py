"""Pytest fixtures for integration tests."""
from __future__ import annotations

import asyncio
import json
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test env vars before importing app
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://saf:saf@localhost:5432/saf_test")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
os.environ.setdefault("APP_SECRET_KEY", "test-secret")
os.environ.setdefault("OCR_PROVIDER", "MOCK")
os.environ.setdefault("S3_ENDPOINT_URL", "")
os.environ.setdefault("S3_ACCESS_KEY", "test")
os.environ.setdefault("S3_SECRET_KEY", "test")
os.environ.setdefault("S3_BUCKET", "test")
os.environ.setdefault("S3_REGION", "eu-west-3")
os.environ.setdefault("S3_USE_PATH_STYLE", "true")

from app.core.db import get_db
from app.core.security import create_access_token, hash_password
from app.main import app

# ---- Tenant A (primary test tenant) ----
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000100")
READONLY_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000101")

# ---- Tenant B (isolation testing) ----
TENANT_B_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
ADMIN_B_ID = uuid.UUID("00000000-0000-0000-0000-000000000200")

test_engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db():
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def seed_db(db: AsyncSession):
    """Ensure base tenant, roles, admin user, and readonly user exist."""
    # ---- Tenant A ----
    await db.execute(text("""
        INSERT INTO tenants (id, name, siren, address)
        VALUES (:id, 'Test Tenant', '123456789', '1 Rue Test, 75001 Paris')
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(TENANT_ID)})

    admin_role_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO roles (id, tenant_id, name, permissions) VALUES (:id, :tid, 'admin', '["*"]'::jsonb)
        ON CONFLICT ON CONSTRAINT uq_roles_tenant_name DO NOTHING
    """), {"id": str(admin_role_id), "tid": str(TENANT_ID)})

    readonly_role_id = uuid.uuid4()
    readonly_perms = json.dumps([
        "jobs.read", "masterdata.read", "documents.read",
        "billing.invoice.read", "billing.pricing.read",
        "payroll.read", "tasks.read",
    ])
    await db.execute(text("""
        INSERT INTO roles (id, tenant_id, name, permissions)
        VALUES (:id, :tid, 'lecture_seule', :perms::jsonb)
        ON CONFLICT ON CONSTRAINT uq_roles_tenant_name DO NOTHING
    """), {"id": str(readonly_role_id), "tid": str(TENANT_ID), "perms": readonly_perms})

    # Fetch actual role IDs (in case of ON CONFLICT DO NOTHING)
    admin_role_row = (await db.execute(text(
        "SELECT id FROM roles WHERE tenant_id = :tid AND name = 'admin'"
    ), {"tid": str(TENANT_ID)})).first()
    readonly_role_row = (await db.execute(text(
        "SELECT id FROM roles WHERE tenant_id = :tid AND name = 'lecture_seule'"
    ), {"tid": str(TENANT_ID)})).first()

    # Admin user
    await db.execute(text("""
        INSERT INTO users (id, tenant_id, email, password_hash, full_name, role_id)
        VALUES (:id, :tid, 'admin@test.local', :pwd, 'Test Admin', :rid)
        ON CONFLICT ON CONSTRAINT uq_users_tenant_email DO NOTHING
    """), {"id": str(ADMIN_ID), "tid": str(TENANT_ID),
           "pwd": hash_password("test"), "rid": str(admin_role_row.id)})

    # Readonly user
    await db.execute(text("""
        INSERT INTO users (id, tenant_id, email, password_hash, full_name, role_id)
        VALUES (:id, :tid, 'readonly@test.local', :pwd, 'Test Readonly', :rid)
        ON CONFLICT ON CONSTRAINT uq_users_tenant_email DO NOTHING
    """), {"id": str(READONLY_USER_ID), "tid": str(TENANT_ID),
           "pwd": hash_password("test"), "rid": str(readonly_role_row.id)})

    await db.commit()


@pytest_asyncio.fixture
async def seed_tenant_b(db: AsyncSession, seed_db):
    """Seed a second tenant for isolation testing."""
    await db.execute(text("""
        INSERT INTO tenants (id, name, siren) VALUES (:id, 'Tenant B', '987654321')
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(TENANT_B_ID)})

    role_b_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO roles (id, tenant_id, name, permissions) VALUES (:id, :tid, 'admin', '["*"]'::jsonb)
        ON CONFLICT ON CONSTRAINT uq_roles_tenant_name DO NOTHING
    """), {"id": str(role_b_id), "tid": str(TENANT_B_ID)})

    role_b_row = (await db.execute(text(
        "SELECT id FROM roles WHERE tenant_id = :tid AND name = 'admin'"
    ), {"tid": str(TENANT_B_ID)})).first()

    await db.execute(text("""
        INSERT INTO users (id, tenant_id, email, password_hash, full_name, role_id)
        VALUES (:id, :tid, 'admin@tenantb.local', :pwd, 'Admin B', :rid)
        ON CONFLICT ON CONSTRAINT uq_users_tenant_email DO NOTHING
    """), {"id": str(ADMIN_B_ID), "tid": str(TENANT_B_ID),
           "pwd": hash_password("test"), "rid": str(role_b_row.id)})

    await db.commit()


@pytest_asyncio.fixture
async def client(seed_db):
    token = create_access_token(ADMIN_ID, TENANT_ID, "admin")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TENANT_ID),
    }

    async def override_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_readonly(seed_db):
    """Client authenticated as lecture_seule user — read-only permissions."""
    token = create_access_token(READONLY_USER_ID, TENANT_ID, "lecture_seule")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TENANT_ID),
    }

    async def override_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_tenant_b(seed_tenant_b):
    """Client authenticated as admin of Tenant B."""
    token = create_access_token(ADMIN_B_ID, TENANT_B_ID, "admin")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TENANT_B_ID),
    }

    async def override_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
