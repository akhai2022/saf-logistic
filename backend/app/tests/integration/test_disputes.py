"""Integration tests: dispute creation, listing, and update on jobs."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"
ADMIN_UID = "00000000-0000-0000-0000-000000000100"


@pytest_asyncio.fixture(autouse=True)
async def clean_dispute_data(db):
    """Clean up disputes and related jobs before each test."""
    # Delete in FK dependency order
    await db.execute(text("DELETE FROM subcontractor_offers WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dispute_attachments WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM disputes WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dunning_actions WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text(
        "DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE tenant_id = :tid)"
    ), {"tid": TID})
    await db.execute(text("DELETE FROM invoices WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM jobs WHERE tenant_id = :tid"), {"tid": TID})
    await db.commit()
    yield


async def _seed_delivered_job(db) -> str:
    """Seed a job with status 'delivered' so disputes can be created on it."""
    job_id = str(uuid.uuid4())
    cust_id = str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name)
        VALUES (:id, :tid, 'Dispute Test Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    await db.execute(text("""
        INSERT INTO jobs (id, tenant_id, status, reference, customer_id,
                          montant_vente_ht, created_at, updated_at)
        VALUES (:id, :tid, 'delivered', :ref, :cid, 5000.00, NOW(), NOW())
        ON CONFLICT DO NOTHING
    """), {
        "id": job_id,
        "tid": TID,
        "ref": f"DISP-{uuid.uuid4().hex[:6]}",
        "cid": cust_id,
    })
    await db.commit()
    return job_id


@pytest.mark.asyncio
async def test_create_dispute(client: AsyncClient, db):
    """Seed a delivered job, POST /v1/jobs/{id}/disputes, verify 201."""
    job_id = await _seed_delivered_job(db)

    resp = await client.post(f"/v1/jobs/{job_id}/disputes", json={
        "type": "AVARIE",
        "description": "Palette endommagee a la livraison",
        "responsabilite": "TRANSPORTEUR",
        "montant_estime_eur": 250.00,
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"] is not None
    assert data["mission_id"] == job_id
    assert data["type"] == "AVARIE"
    assert data["description"] == "Palette endommagee a la livraison"
    assert data["responsabilite"] == "TRANSPORTEUR"
    assert data["statut"] == "OUVERT"
    assert data["numero"].startswith("LIT-")
    assert float(data["montant_estime_eur"]) == 250.00


@pytest.mark.asyncio
async def test_list_disputes(client: AsyncClient, db):
    """Seed a dispute via SQL, GET /v1/jobs/disputes, verify list response."""
    job_id = await _seed_delivered_job(db)
    dispute_id = str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO disputes (id, tenant_id, numero, mission_id, type, description,
                              responsabilite, statut, montant_estime_eur, opened_by, created_at)
        VALUES (:id, :tid, :num, :mid, 'RETARD', 'Retard de 2 heures',
                'CLIENT', 'OUVERT', 100.00, :uid, NOW())
        ON CONFLICT DO NOTHING
    """), {
        "id": dispute_id,
        "tid": TID,
        "num": "LIT-2026-00099",
        "mid": job_id,
        "uid": ADMIN_UID,
    })
    await db.commit()

    resp = await client.get("/v1/jobs/disputes")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    ids = [d["id"] for d in data]
    assert dispute_id in ids

    entry = next(d for d in data if d["id"] == dispute_id)
    assert entry["type"] == "RETARD"
    assert entry["statut"] == "OUVERT"


@pytest.mark.asyncio
async def test_update_dispute(client: AsyncClient, db):
    """Create a dispute, PATCH to update statut and montant_estime, verify changes."""
    job_id = await _seed_delivered_job(db)

    # Create dispute via API
    resp = await client.post(f"/v1/jobs/{job_id}/disputes", json={
        "type": "PERTE_PARTIELLE",
        "description": "3 colis manquants sur 20",
        "responsabilite": "A_DETERMINER",
        "montant_estime_eur": 400.00,
    })
    assert resp.status_code == 201
    dispute = resp.json()
    dispute_id = dispute["id"]
    assert dispute["statut"] == "OUVERT"

    # Update dispute: move to EN_INSTRUCTION and adjust amount
    resp = await client.patch(f"/v1/jobs/{job_id}/disputes/{dispute_id}", json={
        "statut": "EN_INSTRUCTION",
        "montant_estime_eur": 350.00,
        "responsabilite": "TRANSPORTEUR",
        "notes_internes": "Enquete en cours aupres du chauffeur",
    })
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["statut"] == "EN_INSTRUCTION"
    assert float(updated["montant_estime_eur"]) == 350.00
    assert updated["responsabilite"] == "TRANSPORTEUR"
    assert updated["notes_internes"] == "Enquete en cours aupres du chauffeur"
