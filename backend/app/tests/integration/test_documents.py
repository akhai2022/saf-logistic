"""Integration tests: Module D — Documents & Compliance (CRUD + checklist + alerts + templates)."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_documents_data(db):
    """Clean up document & compliance data before each test."""
    await db.execute(text("DELETE FROM compliance_alerts WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM compliance_checklists WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM documents WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM compliance_templates WHERE tenant_id = :tid"), {"tid": TID})
    await db.commit()
    yield


# ---- helpers ----------------------------------------------------------------

def _make_driver_id() -> str:
    return str(uuid.uuid4())


async def _seed_driver(db, driver_id: str) -> None:
    mat = f"DRV-{uuid.uuid4().hex[:6]}"
    await db.execute(text("""
        INSERT INTO drivers (id, tenant_id, first_name, last_name, matricule, nom, prenom, statut)
        VALUES (:id, :tid, 'Test', 'DocDriver', :mat, 'DocDriver', 'Test', 'ACTIF')
        ON CONFLICT (id) DO NOTHING
    """), {"id": driver_id, "tid": TID, "mat": mat})
    await db.commit()


# ══════════════════════════════════════════════════════════════════
# Document CRUD
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_document(client: AsyncClient, db):
    """POST /v1/documents — create a document and verify 201."""
    driver_id = _make_driver_id()
    await _seed_driver(db, driver_id)

    resp = await client.post("/v1/documents", json={
        "entity_type": "DRIVER",
        "entity_id": driver_id,
        "type_document": "PERMIS_CONDUIRE",
        "fichier_s3_key": f"{TID}/docs/permis-test.pdf",
        "fichier_nom_original": "permis-test.pdf",
        "fichier_taille_octets": 102400,
        "fichier_mime_type": "application/pdf",
        "numero_document": "PC-001",
        "date_emission": "2023-01-15",
        "date_expiration": "2028-01-15",
    })
    assert resp.status_code == 201, resp.text
    doc = resp.json()
    assert doc["entity_type"] == "DRIVER"
    assert doc["entity_id"] == driver_id
    assert doc["type_document"] == "PERMIS_CONDUIRE"
    assert doc["statut"] == "VALIDE"
    assert doc["fichier_s3_key"] is not None


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, db):
    """GET /v1/documents — verify response is a list."""
    driver_id = _make_driver_id()
    await _seed_driver(db, driver_id)

    # Seed a document via API
    await client.post("/v1/documents", json={
        "entity_type": "DRIVER",
        "entity_id": driver_id,
        "type_document": "CARTE_ID",
        "fichier_s3_key": f"{TID}/docs/id-card.pdf",
        "fichier_nom_original": "id-card.pdf",
        "fichier_taille_octets": 50000,
        "fichier_mime_type": "application/pdf",
    })

    resp = await client.get("/v1/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_document(client: AsyncClient, db):
    """Create doc then GET /v1/documents/{id} — verify fields."""
    driver_id = _make_driver_id()
    await _seed_driver(db, driver_id)

    create_resp = await client.post("/v1/documents", json={
        "entity_type": "DRIVER",
        "entity_id": driver_id,
        "type_document": "FIMO",
        "fichier_s3_key": f"{TID}/docs/fimo.pdf",
        "fichier_nom_original": "fimo.pdf",
        "fichier_taille_octets": 80000,
        "fichier_mime_type": "application/pdf",
        "date_expiration": "2027-06-30",
    })
    assert create_resp.status_code == 201
    doc_id = create_resp.json()["id"]

    resp = await client.get(f"/v1/documents/{doc_id}")
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["id"] == doc_id
    assert doc["entity_type"] == "DRIVER"
    assert doc["type_document"] == "FIMO"
    assert doc["fichier_nom_original"] == "fimo.pdf"


# ══════════════════════════════════════════════════════════════════
# Compliance Templates
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_compliance_template(client: AsyncClient):
    """POST /v1/compliance/templates — create template, verify 201."""
    resp = await client.post("/v1/compliance/templates", json={
        "entity_type": "DRIVER",
        "type_document": "PERMIS_CONDUIRE",
        "libelle": "Permis de conduire",
        "bloquant": True,
        "obligatoire": True,
    })
    assert resp.status_code == 201, resp.text
    tpl = resp.json()
    assert tpl["entity_type"] == "DRIVER"
    assert tpl["type_document"] == "PERMIS_CONDUIRE"
    assert tpl["libelle"] == "Permis de conduire"
    assert tpl["bloquant"] is True
    assert tpl["is_active"] is True


@pytest.mark.asyncio
async def test_list_compliance_templates(client: AsyncClient):
    """GET /v1/compliance/templates — verify response is a list."""
    # Create a template first
    await client.post("/v1/compliance/templates", json={
        "entity_type": "VEHICLE",
        "type_document": "CONTROLE_TECHNIQUE",
        "libelle": "Controle technique",
        "bloquant": True,
    })

    resp = await client.get("/v1/compliance/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(t["type_document"] == "CONTROLE_TECHNIQUE" for t in data)


# ══════════════════════════════════════════════════════════════════
# Compliance Checklist
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_compliance_checklist(client: AsyncClient, db):
    """Seed driver + template + document, GET /v1/compliance/DRIVER/{id} — verify checklist."""
    driver_id = _make_driver_id()
    await _seed_driver(db, driver_id)

    # Create compliance template
    tpl_resp = await client.post("/v1/compliance/templates", json={
        "entity_type": "DRIVER",
        "type_document": "PERMIS_CONDUIRE",
        "libelle": "Permis de conduire",
        "bloquant": True,
        "obligatoire": True,
    })
    assert tpl_resp.status_code == 201

    # Upload matching document
    doc_resp = await client.post("/v1/documents", json={
        "entity_type": "DRIVER",
        "entity_id": driver_id,
        "type_document": "PERMIS_CONDUIRE",
        "fichier_s3_key": f"{TID}/docs/permis.pdf",
        "fichier_nom_original": "permis.pdf",
        "fichier_taille_octets": 100000,
        "fichier_mime_type": "application/pdf",
        "date_expiration": "2030-12-31",
    })
    assert doc_resp.status_code == 201

    # Get compliance checklist
    resp = await client.get(f"/v1/compliance/DRIVER/{driver_id}")
    assert resp.status_code == 200
    checklist = resp.json()
    assert checklist["entity_type"] == "DRIVER"
    assert checklist["entity_id"] == driver_id
    assert "statut_global" in checklist
    assert "items" in checklist
    assert checklist["nb_documents_requis"] >= 1
    # Since we have a matching valid document, it should be counted
    assert checklist["nb_documents_valides"] >= 1


# ══════════════════════════════════════════════════════════════════
# Compliance Alerts
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_compliance_alerts(client: AsyncClient, db):
    """GET /v1/compliance/alerts — verify response is a list."""
    # Seed an alert directly so the list endpoint has something to return
    driver_id = _make_driver_id()
    await _seed_driver(db, driver_id)

    doc_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO documents (id, tenant_id, entity_type, entity_id, doc_type,
                               statut, s3_key)
        VALUES (:id, :tid, 'DRIVER', :eid, 'PERMIS_CONDUIRE',
                'EXPIRE', 'test/key.pdf')
        ON CONFLICT DO NOTHING
    """), {"id": doc_id, "tid": TID, "eid": driver_id})

    alert_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO compliance_alerts (id, tenant_id, document_id, entity_type, entity_id,
                                       type_alerte, date_expiration_document, statut)
        VALUES (:id, :tid, :did, 'DRIVER', :eid, 'EXPIRATION_J0', '2024-01-01', 'ENVOYEE')
    """), {"id": alert_id, "tid": TID, "did": doc_id, "eid": driver_id})
    await db.commit()

    resp = await client.get("/v1/compliance/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(a["id"] == alert_id for a in data)
