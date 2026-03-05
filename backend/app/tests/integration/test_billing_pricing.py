"""Integration test: KM pricing, flat rate, surcharge — invoice total calculation."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_billing_data(db):
    """Clean up billing/pricing data before each test."""
    # Delete in FK dependency order
    await db.execute(text("DELETE FROM subcontractor_offers WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dunning_actions WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM tasks WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dispute_attachments WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM disputes WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text(
        "DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE tenant_id = :tid)"
    ), {"tid": TID})
    await db.execute(text("DELETE FROM invoices WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM pricing_rules WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM jobs WHERE tenant_id = :tid"), {"tid": TID})
    await db.commit()
    yield


@pytest.mark.asyncio
async def test_km_pricing_basic(client: AsyncClient, db):
    """A km rule at 1.50 EUR/km applied to a 465 km job should yield 697.50 HT."""
    tid = TID

    # Seed customer
    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name, payment_terms_days)
        VALUES (:id, :tid, 'KM Test Client', 30) ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": tid})

    # Seed km pricing rule (global, no customer_id)
    rule_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO pricing_rules (id, tenant_id, customer_id, label, rule_type, rate)
        VALUES (:id, :tid, NULL, 'Tarif km standard', 'km', 1.50)
    """), {"id": rule_id, "tid": tid})
    await db.commit()

    # Create job with distance
    resp = await client.post("/v1/jobs", json={
        "reference": "PRICE-KM-001",
        "customer_id": cust_id,
        "pickup_address": "Paris",
        "delivery_address": "Lyon",
        "distance_km": 465,
    })
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Create invoice from job
    resp = await client.post("/v1/billing/invoices", json={
        "customer_id": cust_id,
        "job_ids": [job_id],
        "tva_rate": 20.0,
    })
    assert resp.status_code == 201
    inv = resp.json()
    assert inv["total_ht"] == pytest.approx(697.50, abs=0.01)
    assert inv["tva_rate"] == 20.0
    assert inv["total_tva"] == pytest.approx(139.50, abs=0.01)
    assert inv["total_ttc"] == pytest.approx(837.00, abs=0.01)
    assert inv["status"] == "draft"


@pytest.mark.asyncio
async def test_km_pricing_with_range(client: AsyncClient, db):
    """km rules with min_km/max_km ranges should only apply within bounds."""
    tid = TID

    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name) VALUES (:id, :tid, 'Range Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": tid})

    # Rule: 2.00/km for 0-200km
    await db.execute(text("""
        INSERT INTO pricing_rules (id, tenant_id, customer_id, label, rule_type, rate, min_km, max_km)
        VALUES (:id, :tid, :cid, 'Short haul', 'km', 2.00, 0, 200)
    """), {"id": str(uuid.uuid4()), "tid": tid, "cid": cust_id})

    # Rule: 1.20/km for 200-1000km
    await db.execute(text("""
        INSERT INTO pricing_rules (id, tenant_id, customer_id, label, rule_type, rate, min_km, max_km)
        VALUES (:id, :tid, :cid, 'Long haul', 'km', 1.20, 200, 1000)
    """), {"id": str(uuid.uuid4()), "tid": tid, "cid": cust_id})
    await db.commit()

    # Job at 150 km: only short haul applies → 300.00
    resp = await client.post("/v1/jobs", json={
        "reference": "RANGE-SHORT",
        "customer_id": cust_id,
        "distance_km": 150,
    })
    assert resp.status_code == 201
    job_short = resp.json()["id"]

    resp = await client.post("/v1/billing/invoices", json={
        "customer_id": cust_id,
        "job_ids": [job_short],
    })
    assert resp.status_code == 201
    assert resp.json()["total_ht"] == pytest.approx(300.00, abs=0.01)


@pytest.mark.asyncio
async def test_flat_and_surcharge(client: AsyncClient, db):
    """Flat rate + surcharge should be additive."""
    tid = TID

    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name) VALUES (:id, :tid, 'Flat Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": tid})

    # Flat rate: 250.00 EUR per job
    await db.execute(text("""
        INSERT INTO pricing_rules (id, tenant_id, customer_id, label, rule_type, rate)
        VALUES (:id, :tid, :cid, 'Forfait livraison', 'flat', 250.00)
    """), {"id": str(uuid.uuid4()), "tid": tid, "cid": cust_id})

    # Surcharge: 35.00 EUR (fuel surcharge)
    await db.execute(text("""
        INSERT INTO pricing_rules (id, tenant_id, customer_id, label, rule_type, rate)
        VALUES (:id, :tid, :cid, 'Surcharge carburant', 'surcharge', 35.00)
    """), {"id": str(uuid.uuid4()), "tid": tid, "cid": cust_id})
    await db.commit()

    resp = await client.post("/v1/jobs", json={
        "reference": "FLAT-001",
        "customer_id": cust_id,
    })
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    resp = await client.post("/v1/billing/invoices", json={
        "customer_id": cust_id,
        "job_ids": [job_id],
        "tva_rate": 20.0,
    })
    assert resp.status_code == 201
    inv = resp.json()
    # flat 250 + surcharge 35 = 285
    assert inv["total_ht"] == pytest.approx(285.00, abs=0.01)
    assert inv["total_tva"] == pytest.approx(57.00, abs=0.01)
    assert inv["total_ttc"] == pytest.approx(342.00, abs=0.01)


@pytest.mark.asyncio
async def test_multi_job_invoice(client: AsyncClient, db):
    """Invoice from multiple jobs should sum all line amounts."""
    tid = TID

    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name) VALUES (:id, :tid, 'Multi Job Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": tid})

    await db.execute(text("""
        INSERT INTO pricing_rules (id, tenant_id, customer_id, label, rule_type, rate)
        VALUES (:id, :tid, :cid, 'Km rate', 'km', 1.00)
    """), {"id": str(uuid.uuid4()), "tid": tid, "cid": cust_id})
    await db.commit()

    job_ids = []
    for i, dist in enumerate([100, 200, 300]):
        resp = await client.post("/v1/jobs", json={
            "reference": f"MULTI-{i}",
            "customer_id": cust_id,
            "distance_km": dist,
        })
        assert resp.status_code == 201
        job_ids.append(resp.json()["id"])

    resp = await client.post("/v1/billing/invoices", json={
        "customer_id": cust_id,
        "job_ids": job_ids,
        "tva_rate": 20.0,
    })
    assert resp.status_code == 201
    # 100 + 200 + 300 = 600 HT
    assert resp.json()["total_ht"] == pytest.approx(600.00, abs=0.01)

    # Verify lines via detail endpoint
    inv_id = resp.json()["id"]
    detail = await client.get(f"/v1/billing/invoices/{inv_id}")
    assert detail.status_code == 200
    assert len(detail.json()["lines"]) == 3
