"""Integration tests: audit log listing and pagination."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"
ADMIN_UID = "00000000-0000-0000-0000-000000000100"


@pytest_asyncio.fixture(autouse=True)
async def clean_audit_data(db):
    """Clean up audit_logs before each test."""
    await db.execute(text("DELETE FROM audit_logs WHERE tenant_id = :tid"), {"tid": TID})
    await db.commit()
    yield


@pytest.mark.asyncio
async def test_list_audit_logs(client: AsyncClient, db):
    """Seed one audit_log entry, GET /v1/audit-logs, verify it appears."""
    log_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO audit_logs (id, tenant_id, user_id, action, entity_type, entity_id, metadata, created_at)
        VALUES (:id, :tid, :uid, 'CREATE', 'job', :eid, '{}', NOW())
        ON CONFLICT DO NOTHING
    """), {
        "id": log_id,
        "tid": TID,
        "uid": ADMIN_UID,
        "eid": str(uuid.uuid4()),
    })
    await db.commit()

    resp = await client.get("/v1/audit-logs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    ids = [entry["id"] for entry in data]
    assert log_id in ids

    # Verify fields on the seeded entry
    entry = next(e for e in data if e["id"] == log_id)
    assert entry["action"] == "CREATE"
    assert entry["entity_type"] == "job"
    assert entry["user_id"] == ADMIN_UID


@pytest.mark.asyncio
async def test_audit_logs_pagination(client: AsyncClient, db):
    """Seed 3 audit entries, GET with limit=2, verify only 2 returned."""
    for i in range(3):
        await db.execute(text("""
            INSERT INTO audit_logs (id, tenant_id, user_id, action, entity_type, entity_id, created_at)
            VALUES (:id, :tid, :uid, :action, 'invoice', :eid, NOW())
            ON CONFLICT DO NOTHING
        """), {
            "id": str(uuid.uuid4()),
            "tid": TID,
            "uid": ADMIN_UID,
            "action": f"UPDATE_{i}",
            "eid": str(uuid.uuid4()),
        })
    await db.commit()

    resp = await client.get("/v1/audit-logs", params={"limit": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
