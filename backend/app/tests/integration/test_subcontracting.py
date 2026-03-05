"""Integration tests: Subcontracting — offer CRUD and lifecycle."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_subcontracting_data(db):
    """Clean up subcontracting data before each test."""
    # Delete in FK dependency order
    await db.execute(text("DELETE FROM subcontractor_offers WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dispute_attachments WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM disputes WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text(
        "DELETE FROM jobs WHERE tenant_id = :tid AND reference LIKE 'SUB-%%'"
    ), {"tid": TID})
    await db.commit()
    yield


async def _seed_job_and_subcontractor(db):
    """Seed a job and subcontractor for subcontracting tests. Returns (job_id, subcontractor_id)."""
    job_id = str(uuid.uuid4())
    sub_id = str(uuid.uuid4())
    sub_code = f"ST-{uuid.uuid4().hex[:6]}"

    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name)
        VALUES (:id, :tid, 'Sub Test Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    await db.execute(text("""
        INSERT INTO subcontractors (id, tenant_id, code, raison_sociale, siret,
            adresse_ligne1, code_postal, ville, email)
        VALUES (:id, :tid, :code, 'Transports Test ST', '44306184100047',
            '1 Rue Test', '75001', 'Paris', 'st@test.fr')
        ON CONFLICT (id) DO NOTHING
    """), {"id": sub_id, "tid": TID, "code": sub_code})

    await db.execute(text("""
        INSERT INTO jobs (id, tenant_id, reference, customer_id, status)
        VALUES (:id, :tid, :ref, :cid, 'draft')
        ON CONFLICT (id) DO NOTHING
    """), {"id": job_id, "tid": TID, "ref": f"SUB-{uuid.uuid4().hex[:6]}", "cid": cust_id})

    await db.commit()
    return job_id, sub_id


async def _seed_offer(db, job_id: str, sub_id: str, statut: str = "ENVOYEE") -> str:
    """Insert an offer directly via SQL. Returns the offer id."""
    offer_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO subcontractor_offers
            (id, tenant_id, job_id, subcontractor_id, montant_propose, statut, date_envoi)
        VALUES (:id, :tid, :jid, :sid, 1500.00, :statut, NOW())
    """), {
        "id": offer_id, "tid": TID, "jid": job_id,
        "sid": sub_id, "statut": statut,
    })
    await db.commit()
    return offer_id


@pytest.mark.asyncio
async def test_create_offer(client: AsyncClient, db):
    """POST /v1/subcontracting/offers should create an offer and return 201."""
    job_id, sub_id = await _seed_job_and_subcontractor(db)

    resp = await client.post("/v1/subcontracting/offers", json={
        "job_id": job_id,
        "subcontractor_id": sub_id,
        "montant_propose": 1200.50,
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["job_id"] == job_id
    assert data["subcontractor_id"] == sub_id
    assert data["montant_propose"] == 1200.50
    assert data["statut"] == "ENVOYEE"


@pytest.mark.asyncio
async def test_list_offers_pagination(client: AsyncClient, db):
    """GET /v1/subcontracting/offers?limit=1 should return only 1 offer when 2 exist."""
    job_id, sub_id = await _seed_job_and_subcontractor(db)
    await _seed_offer(db, job_id, sub_id)
    await _seed_offer(db, job_id, sub_id)

    resp = await client.get("/v1/subcontracting/offers?limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1

    # Without limit, both should be returned
    resp_all = await client.get("/v1/subcontracting/offers")
    assert resp_all.status_code == 200
    assert len(resp_all.json()) >= 2


@pytest.mark.asyncio
async def test_accept_offer(client: AsyncClient, db):
    """POST /v1/subcontracting/offers/{id}/accept should change statut to ACCEPTEE."""
    job_id, sub_id = await _seed_job_and_subcontractor(db)
    offer_id = await _seed_offer(db, job_id, sub_id, statut="ENVOYEE")

    resp = await client.post(f"/v1/subcontracting/offers/{offer_id}/accept")
    assert resp.status_code == 200
    data = resp.json()
    assert data["statut"] == "ACCEPTEE"
    assert data["id"] == offer_id


@pytest.mark.asyncio
async def test_reject_offer(client: AsyncClient, db):
    """POST /v1/subcontracting/offers/{id}/reject should change statut to REFUSEE."""
    job_id, sub_id = await _seed_job_and_subcontractor(db)
    offer_id = await _seed_offer(db, job_id, sub_id, statut="ENVOYEE")

    resp = await client.post(f"/v1/subcontracting/offers/{offer_id}/reject", json={
        "motif_refus": "Prix trop eleve",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["statut"] == "REFUSEE"
    assert data["motif_refus"] == "Prix trop eleve"


@pytest.mark.asyncio
async def test_cancel_offer(client: AsyncClient, db):
    """POST /v1/subcontracting/offers/{id}/cancel should change statut to ANNULEE."""
    job_id, sub_id = await _seed_job_and_subcontractor(db)
    offer_id = await _seed_offer(db, job_id, sub_id, statut="ENVOYEE")

    resp = await client.post(f"/v1/subcontracting/offers/{offer_id}/cancel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["statut"] == "ANNULEE"
    assert data["id"] == offer_id
