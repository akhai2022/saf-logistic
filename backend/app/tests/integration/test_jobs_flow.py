"""Integration test: full job lifecycle."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text


@pytest.mark.asyncio
async def test_job_lifecycle(client: AsyncClient, db):
    """
    Create → Plan → Assign → Start → Deliver → Upload POD → Close
    """
    tid = "00000000-0000-0000-0000-000000000001"

    # Seed customer + driver
    cust_id = str(uuid.uuid4())
    driver_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name) VALUES (:id, :tid, 'Test Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": tid})
    await db.execute(text("""
        INSERT INTO drivers (id, tenant_id, first_name, last_name, matricule)
        VALUES (:id, :tid, 'Test', 'Driver', :mat)
        ON CONFLICT ON CONSTRAINT uq_drivers_tenant_matricule DO NOTHING
    """), {"id": driver_id, "tid": tid, "mat": f"TST-{uuid.uuid4().hex[:4]}"})
    await db.commit()

    # 1. Create job
    resp = await client.post("/v1/jobs", json={
        "reference": "TEST-001",
        "customer_id": cust_id,
        "pickup_address": "Paris",
        "delivery_address": "Lyon",
        "distance_km": 465,
    })
    assert resp.status_code == 201
    job = resp.json()
    job_id = job["id"]
    assert job["status"] == "draft"

    # 2. Plan
    resp = await client.post(f"/v1/jobs/{job_id}/transition?target_status=planned")
    assert resp.status_code == 200

    # 3. Assign
    resp = await client.post(f"/v1/jobs/{job_id}/assign?driver_id={driver_id}")
    assert resp.status_code == 200

    # 4. Start
    resp = await client.post(f"/v1/jobs/{job_id}/transition?target_status=in_progress")
    assert resp.status_code == 200

    # 5. Deliver
    resp = await client.post(f"/v1/jobs/{job_id}/transition?target_status=delivered")
    assert resp.status_code == 200

    # 6. Close without POD should fail
    resp = await client.post(f"/v1/jobs/{job_id}/close")
    assert resp.status_code == 400

    # 7. Upload POD
    fake_key = f"{tid}/job_pod/test.pdf"
    resp = await client.post(f"/v1/jobs/{job_id}/pod?s3_key={fake_key}")
    assert resp.status_code == 200

    # 8. Close with POD
    resp = await client.post(f"/v1/jobs/{job_id}/close")
    assert resp.status_code == 200

    # Verify final state
    resp = await client.get(f"/v1/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"
