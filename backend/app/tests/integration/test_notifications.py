"""Integration tests: Notifications — list, count, mark read."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"
ADMIN_UID = "00000000-0000-0000-0000-000000000100"


@pytest_asyncio.fixture(autouse=True)
async def clean_notifications_data(db):
    """Clean up notifications data before each test."""
    await db.execute(text(
        "DELETE FROM notifications WHERE tenant_id = :tid"
    ), {"tid": TID})
    await db.execute(text(
        "DELETE FROM notification_configs WHERE tenant_id = :tid"
    ), {"tid": TID})
    await db.commit()
    yield


async def _seed_notification(
    db, *, title: str = "Test Notification", read: bool = False,
) -> str:
    """Insert a notification for the admin user via raw SQL. Returns notification id."""
    nid = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO notifications (id, tenant_id, user_id, title, message, event_type, read)
        VALUES (:id, :tid, :uid, :title, 'Test message body', 'job_created', :read)
    """), {
        "id": nid, "tid": TID, "uid": ADMIN_UID,
        "title": title, "read": read,
    })
    await db.commit()
    return nid


@pytest.mark.asyncio
async def test_list_notifications(client: AsyncClient, db):
    """GET /v1/notifications should return seeded notifications."""
    nid = await _seed_notification(db, title="Nouvelle mission creee")

    resp = await client.get("/v1/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(n["id"] == nid for n in data)

    found = next(n for n in data if n["id"] == nid)
    assert found["title"] == "Nouvelle mission creee"
    assert found["read"] is False


@pytest.mark.asyncio
async def test_notification_count(client: AsyncClient, db):
    """GET /v1/notifications/count should return the unread count."""
    await _seed_notification(db, title="Unread 1", read=False)
    await _seed_notification(db, title="Unread 2", read=False)
    await _seed_notification(db, title="Already read", read=True)

    resp = await client.get("/v1/notifications/count")
    assert resp.status_code == 200
    data = resp.json()
    assert "unread" in data
    assert data["unread"] >= 2


@pytest.mark.asyncio
async def test_mark_notification_read(client: AsyncClient, db):
    """PATCH /v1/notifications/{id}/read should set read=true."""
    nid = await _seed_notification(db, title="To be read")

    resp = await client.patch(f"/v1/notifications/{nid}/read")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == nid
    assert data["read"] is True


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient, db):
    """POST /v1/notifications/read-all should mark all notifications as read."""
    await _seed_notification(db, title="Notif A", read=False)
    await _seed_notification(db, title="Notif B", read=False)

    resp = await client.post("/v1/notifications/read-all")
    assert resp.status_code == 200
    data = resp.json()
    assert "updated" in data
    assert data["updated"] >= 2

    # Verify all are now read
    count_resp = await client.get("/v1/notifications/count")
    assert count_resp.status_code == 200
    assert count_resp.json()["unread"] == 0


@pytest.mark.asyncio
async def test_notification_config(client: AsyncClient, db):
    """GET /v1/settings/notifications should return a list of notification configs."""
    # Seed a notification config
    cfg_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO notification_configs
            (id, tenant_id, event_type, channels, is_active)
        VALUES (:id, :tid, 'job_created', '{IN_APP}', true)
    """), {"id": cfg_id, "tid": TID})
    await db.commit()

    resp = await client.get("/v1/settings/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(c["event_type"] == "job_created" for c in data)
