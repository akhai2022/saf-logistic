"""Integration tests: Planning module — driver/vehicle planning & availability check."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_planning_data(db):
    """Clean up planning-related data before each test."""
    # Delete in FK dependency order
    await db.execute(text("DELETE FROM subcontractor_offers WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dispute_attachments WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM disputes WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM jobs WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text(
        "DELETE FROM drivers WHERE tenant_id = :tid AND matricule LIKE 'PLAN-%'"
    ), {"tid": TID})
    await db.execute(text(
        "DELETE FROM vehicles WHERE tenant_id = :tid AND immatriculation LIKE 'PL-%'"
    ), {"tid": TID})
    await db.commit()
    yield


# ---- helpers ----------------------------------------------------------------

async def _seed_driver(db, driver_id: str) -> None:
    mat = f"PLAN-{uuid.uuid4().hex[:6]}"
    await db.execute(text("""
        INSERT INTO drivers (id, tenant_id, first_name, last_name, matricule,
                             nom, prenom, statut)
        VALUES (:id, :tid, 'Plan', 'Driver', :mat, 'Driver', 'Plan', 'ACTIF')
        ON CONFLICT (id) DO NOTHING
    """), {"id": driver_id, "tid": TID, "mat": mat})
    await db.commit()


async def _seed_vehicle(db, vehicle_id: str) -> str:
    plate = f"PL-{uuid.uuid4().int % 900 + 100}-ZZ"
    await db.execute(text("""
        INSERT INTO vehicles (id, tenant_id, immatriculation, plate_number, statut)
        VALUES (:id, :tid, :plate, :plate, 'ACTIF')
        ON CONFLICT (id) DO NOTHING
    """), {"id": vehicle_id, "tid": TID, "plate": plate})
    await db.commit()
    return plate


# ══════════════════════════════════════════════════════════════════
# 1. Driver planning
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_driver_planning(client: AsyncClient, db):
    """GET /v1/planning/drivers?start=...&end=... — verify 200 and list response."""
    driver_id = str(uuid.uuid4())
    await _seed_driver(db, driver_id)

    resp = await client.get("/v1/planning/drivers", params={
        "start": "2024-01-01",
        "end": "2024-12-31",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # The seeded driver should appear (it is ACTIF)
    assert any(d["driver_id"] == driver_id for d in data)
    # Verify structure of the response items
    if data:
        item = data[0]
        assert "driver_id" in item
        assert "driver_name" in item
        assert "blocks" in item
        assert isinstance(item["blocks"], list)


# ══════════════════════════════════════════════════════════════════
# 2. Vehicle planning
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_vehicle_planning(client: AsyncClient, db):
    """GET /v1/planning/vehicles?start=...&end=... — verify 200 and list response."""
    vehicle_id = str(uuid.uuid4())
    plate = await _seed_vehicle(db, vehicle_id)

    resp = await client.get("/v1/planning/vehicles", params={
        "start": "2024-01-01",
        "end": "2024-12-31",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # The seeded vehicle should appear
    assert any(v["vehicle_id"] == vehicle_id for v in data)
    # Verify structure
    if data:
        item = data[0]
        assert "vehicle_id" in item
        assert "plate" in item
        assert "blocks" in item
        assert isinstance(item["blocks"], list)


# ══════════════════════════════════════════════════════════════════
# 3. Availability check
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_check_availability(client: AsyncClient, db):
    """POST /v1/planning/check-availability — verify 200 with available=true for free driver."""
    driver_id = str(uuid.uuid4())
    await _seed_driver(db, driver_id)

    resp = await client.post("/v1/planning/check-availability", json={
        "driver_id": driver_id,
        "start": "2024-06-01",
        "end": "2024-06-02",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "available" in data
    assert "conflicts" in data
    # Driver has no jobs, so should be available
    assert data["available"] is True
    assert data["conflicts"] == []


@pytest.mark.asyncio
async def test_check_availability_with_conflict(client: AsyncClient, db):
    """Seed a job for a driver, then check availability in overlapping window — expect conflict."""
    driver_id = str(uuid.uuid4())
    await _seed_driver(db, driver_id)

    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name)
        VALUES (:id, :tid, 'Planning Test Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    # Seed a job assigned to this driver within the date range
    job_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO jobs (id, tenant_id, customer_id, reference, driver_id,
                          status,
                          date_chargement_prevue, date_livraison_prevue)
        VALUES (:id, :tid, :cid, 'PLAN-CONFLICT-001', :did,
                'planned',
                '2024-06-01', '2024-06-03')
        ON CONFLICT DO NOTHING
    """), {"id": job_id, "tid": TID, "cid": cust_id, "did": driver_id})
    await db.commit()

    # Check availability overlapping the job dates
    resp = await client.post("/v1/planning/check-availability", json={
        "driver_id": driver_id,
        "start": "2024-06-02",
        "end": "2024-06-04",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is False
    assert len(data["conflicts"]) >= 1
    assert data["conflicts"][0]["job_id"] == job_id
