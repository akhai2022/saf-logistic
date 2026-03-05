"""Integration tests: fleet maintenance, claims, costs, and dashboard."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_fleet_data(db):
    """Clean up fleet-related data before each test."""
    await db.execute(text("DELETE FROM vehicle_costs WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM vehicle_claims WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM maintenance_records WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM maintenance_schedules WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM vehicles WHERE tenant_id = :tid"), {"tid": TID})
    await db.commit()
    yield


async def _seed_vehicle(db, plate: str | None = None) -> str:
    """Helper: insert a vehicle and return its ID."""
    vid = str(uuid.uuid4())
    plate = plate or f"AA-{uuid.uuid4().int % 900 + 100}-BB"
    await db.execute(text("""
        INSERT INTO vehicles (id, tenant_id, plate_number, immatriculation, statut)
        VALUES (:id, :tid, :plate, :plate, 'ACTIF')
        ON CONFLICT DO NOTHING
    """), {"id": vid, "tid": TID, "plate": plate})
    await db.commit()
    return vid


# ══════════════════════════════════════════════════════════════════
# Vehicle CRUD (via masterdata endpoints)
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_vehicle(client: AsyncClient):
    """POST /v1/masterdata/vehicles creates a vehicle and returns 201."""
    plate = f"AB-{uuid.uuid4().int % 900 + 100}-CD"
    resp = await client.post("/v1/masterdata/vehicles", json={
        "immatriculation": plate,
        "type_entity": "VEHICULE",
        "categorie": "VL",
        "marque": "Mercedes",
        "modele": "Sprinter",
    })
    assert resp.status_code == 201, resp.text
    vehicle = resp.json()
    assert vehicle["id"] is not None
    assert vehicle["marque"] == "Mercedes"


@pytest.mark.asyncio
async def test_list_vehicles(client: AsyncClient, db):
    """GET /v1/masterdata/vehicles returns a list."""
    await _seed_vehicle(db)
    resp = await client.get("/v1/masterdata/vehicles")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ══════════════════════════════════════════════════════════════════
# Maintenance Schedules
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_maintenance_schedule(client: AsyncClient, db):
    """Seed a vehicle, then POST a maintenance schedule."""
    vid = await _seed_vehicle(db)

    resp = await client.post(f"/v1/fleet/vehicles/{vid}/schedules", json={
        "type_maintenance": "VIDANGE",
        "libelle": "Vidange moteur",
        "frequence_jours": 180,
        "frequence_km": 20000,
        "prochaine_date_prevue": str(date.today() + timedelta(days=90)),
    })
    assert resp.status_code == 201, resp.text
    schedule = resp.json()
    assert schedule["type_maintenance"] == "VIDANGE"
    assert schedule["libelle"] == "Vidange moteur"
    assert schedule["vehicle_id"] == vid
    assert schedule["is_active"] is True


# ══════════════════════════════════════════════════════════════════
# Maintenance Records
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_maintenance_record(client: AsyncClient, db):
    """Seed a vehicle, POST a maintenance record, verify creation."""
    vid = await _seed_vehicle(db)

    resp = await client.post(f"/v1/fleet/vehicles/{vid}/maintenance", json={
        "type_maintenance": "REVISION",
        "libelle": "Revision annuelle",
        "date_debut": str(date.today()),
        "statut": "PLANIFIE",
        "prestataire": "Garage Test",
    })
    assert resp.status_code == 201, resp.text
    maint = resp.json()
    assert maint["type_maintenance"] == "REVISION"
    assert maint["libelle"] == "Revision annuelle"
    assert maint["vehicle_id"] == vid
    assert maint["statut"] == "PLANIFIE"


@pytest.mark.asyncio
async def test_list_maintenance(client: AsyncClient, db):
    """GET /v1/fleet/vehicles/{vid}/maintenance with pagination."""
    vid = await _seed_vehicle(db)

    # Create two maintenance records
    for label in ["Entretien A", "Entretien B"]:
        resp = await client.post(f"/v1/fleet/vehicles/{vid}/maintenance", json={
            "type_maintenance": "VIDANGE",
            "libelle": label,
            "date_debut": str(date.today()),
            "statut": "PLANIFIE",
        })
        assert resp.status_code == 201

    # List with limit
    resp = await client.get(f"/v1/fleet/vehicles/{vid}/maintenance", params={"limit": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1

    # List all
    resp = await client.get(f"/v1/fleet/vehicles/{vid}/maintenance", params={"limit": 50})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


# ══════════════════════════════════════════════════════════════════
# Claims (Sinistres)
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_claim(client: AsyncClient, db):
    """POST /v1/fleet/vehicles/{vid}/claims creates a claim with 201."""
    vid = await _seed_vehicle(db)

    resp = await client.post(f"/v1/fleet/vehicles/{vid}/claims", json={
        "date_sinistre": str(date.today()),
        "type_sinistre": "ACCROCHAGE",
        "description": "Accrochage sur parking",
        "lieu": "Parking Rungis",
        "responsabilite": "A_DETERMINER",
    })
    assert resp.status_code == 201, resp.text
    claim = resp.json()
    assert claim["vehicle_id"] == vid
    assert claim["type_sinistre"] == "ACCROCHAGE"
    assert claim["statut"] == "DECLARE"
    assert claim["numero"].startswith("SIN-")


@pytest.mark.asyncio
async def test_list_global_claims(client: AsyncClient, db):
    """GET /v1/fleet/claims returns claims across all vehicles with pagination."""
    vid1 = await _seed_vehicle(db, plate=f"CL-{uuid.uuid4().int % 900 + 100}-AA")
    vid2 = await _seed_vehicle(db, plate=f"CL-{uuid.uuid4().int % 900 + 100}-BB")

    # Create one claim per vehicle
    for vid in [vid1, vid2]:
        resp = await client.post(f"/v1/fleet/vehicles/{vid}/claims", json={
            "date_sinistre": str(date.today()),
            "type_sinistre": "BRIS_GLACE",
            "responsabilite": "NON_RESPONSABLE",
        })
        assert resp.status_code == 201

    # Global list
    resp = await client.get("/v1/fleet/claims", params={"limit": 50})
    assert resp.status_code == 200
    claims = resp.json()
    assert len(claims) >= 2

    # Verify pagination
    resp = await client.get("/v1/fleet/claims", params={"limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ══════════════════════════════════════════════════════════════════
# Fleet Dashboard (stats)
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_fleet_dashboard(client: AsyncClient, db):
    """GET /v1/fleet/dashboard returns expected stat keys."""
    # Seed a vehicle so stats are non-trivial
    await _seed_vehicle(db)

    resp = await client.get("/v1/fleet/dashboard")
    assert resp.status_code == 200
    stats = resp.json()

    expected_keys = {
        "total_vehicles",
        "vehicles_actifs",
        "vehicles_en_maintenance",
        "vehicles_immobilises",
        "taux_disponibilite",
        "maintenances_a_venir_30j",
        "maintenances_en_retard",
        "sinistres_ouverts",
        "cout_total_mois_ht",
    }
    assert expected_keys.issubset(stats.keys())
    assert stats["total_vehicles"] >= 1
    assert stats["vehicles_actifs"] >= 1
