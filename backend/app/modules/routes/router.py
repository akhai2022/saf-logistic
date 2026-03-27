"""Routes (Tournées) — Recurring delivery route definitions and mission generation."""
from __future__ import annotations

import json
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user, require_permission
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/routes", tags=["routes"])


# ── Schemas ────────────────────────────────────────────────────────

RECURRENCE_PATTERNS = {"QUOTIDIENNE", "LUN_VEN", "LUN_SAM", "HEBDOMADAIRE", "BIMENSUELLE", "MENSUELLE"}
ROUTE_STATUTS = {"ACTIF", "SUSPENDUE", "ARCHIVEE"}


class RouteCreate(BaseModel):
    numero: str
    libelle: str
    client_id: str | None = None
    type_mission: str = "LOT_COMPLET"
    recurrence: str = "LUN_VEN"
    date_debut: date
    date_fin: date | None = None
    driver_id: str | None = None
    vehicle_id: str | None = None
    is_subcontracted: bool = False
    subcontractor_id: str | None = None
    montant_vente_ht: Decimal | None = None
    montant_achat_ht: Decimal | None = None
    adresse_chargement: str | None = None
    site: str | None = None
    distance_estimee_km: Decimal | None = None
    contraintes: dict | None = None
    notes: str | None = None
    agency_id: str | None = None


class RouteUpdate(RouteCreate):
    statut: str | None = None


class RouteOut(BaseModel):
    id: str
    numero: str
    libelle: str
    client_id: str | None = None
    client_name: str | None = None
    type_mission: str | None = None
    recurrence: str | None = None
    date_debut: date | None = None
    date_fin: date | None = None
    driver_id: str | None = None
    driver_name: str | None = None
    vehicle_id: str | None = None
    vehicle_plate: str | None = None
    is_subcontracted: bool = False
    montant_vente_ht: Decimal | None = None
    montant_achat_ht: Decimal | None = None
    site: str | None = None
    statut: str | None = None
    nb_missions: int = 0
    nb_missions_completees: int = 0
    created_at: str | None = None


class RouteDetail(RouteOut):
    subcontractor_id: str | None = None
    adresse_chargement: str | None = None
    distance_estimee_km: Decimal | None = None
    contraintes: dict | None = None
    notes: str | None = None
    agency_id: str | None = None
    delivery_points: list[dict] = []


class GenerateMissionsRequest(BaseModel):
    start_date: date
    end_date: date
    override_driver_id: str | None = None
    override_vehicle_id: str | None = None


class DeliveryPointCreate(BaseModel):
    ordre: int
    adresse: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    contact_nom: str | None = None
    contact_telephone: str | None = None
    instructions: str | None = None


# ── Helpers ────────────────────────────────────────────────────────

def _expand_dates(recurrence: str, start: date, end: date) -> list[date]:
    """Expand recurrence pattern into a list of dates."""
    dates = []
    d = start
    while d <= end:
        wd = d.weekday()  # 0=Monday, 6=Sunday
        if recurrence == "QUOTIDIENNE":
            dates.append(d)
        elif recurrence == "LUN_VEN" and wd < 5:
            dates.append(d)
        elif recurrence == "LUN_SAM" and wd < 6:
            dates.append(d)
        elif recurrence == "HEBDOMADAIRE" and wd == 0:
            dates.append(d)
        elif recurrence == "BIMENSUELLE" and wd == 0 and (d.isocalendar()[1] % 2 == 0):
            dates.append(d)
        elif recurrence == "MENSUELLE" and d.day == start.day:
            dates.append(d)
        d += timedelta(days=1)
    return dates


# ── CRUD ───────────────────────────────────────────────────────────

@router.get("", response_model=list[RouteOut])
async def list_routes(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    client_id: str | None = Query(None),
    search: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    tid = str(tenant.tenant_id)
    q = """
        SELECT r.*,
               c.raison_sociale AS client_name,
               COALESCE(d.nom, d.last_name) || ' ' || COALESCE(d.prenom, d.first_name) AS driver_name,
               COALESCE(v.immatriculation, v.plate_number) AS vehicle_plate,
               (SELECT COUNT(*) FROM jobs j WHERE j.route_id = r.id) AS nb_missions,
               (SELECT COUNT(*) FROM jobs j WHERE j.route_id = r.id AND j.status IN ('CLOTUREE','FACTUREE')) AS nb_missions_completees
        FROM routes r
        LEFT JOIN customers c ON r.client_id = c.id
        LEFT JOIN drivers d ON r.driver_id = d.id
        LEFT JOIN vehicles v ON r.vehicle_id = v.id
        WHERE r.tenant_id = :tid
    """
    params: dict[str, Any] = {"tid": tid}
    if statut:
        q += " AND r.statut = :statut"
        params["statut"] = statut
    if client_id:
        q += " AND r.client_id = :client_id"
        params["client_id"] = client_id
    if search:
        q += " AND (r.numero ILIKE :search OR r.libelle ILIKE :search OR r.site ILIKE :search)"
        params["search"] = f"%{search}%"
    allowed = {"numero": "r.numero", "libelle": "r.libelle", "created_at": "r.created_at", "statut": "r.statut"}
    sort_col = allowed.get(sort_by, "r.created_at") if sort_by else "r.created_at"
    q += f" ORDER BY {sort_col} {order} LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = (await db.execute(text(q), params)).fetchall()
    return [
        RouteOut(
            id=str(r.id), numero=r.numero, libelle=r.libelle,
            client_id=str(r.client_id) if r.client_id else None,
            client_name=r.client_name,
            type_mission=r.type_mission, recurrence=r.recurrence,
            date_debut=r.date_debut, date_fin=r.date_fin,
            driver_id=str(r.driver_id) if r.driver_id else None,
            driver_name=r.driver_name,
            vehicle_id=str(r.vehicle_id) if r.vehicle_id else None,
            vehicle_plate=r.vehicle_plate,
            is_subcontracted=r.is_subcontracted or False,
            montant_vente_ht=r.montant_vente_ht, montant_achat_ht=r.montant_achat_ht,
            site=r.site, statut=r.statut,
            nb_missions=r.nb_missions, nb_missions_completees=r.nb_missions_completees,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]


@router.post("", response_model=RouteOut, status_code=201)
async def create_route(
    body: RouteCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    if body.recurrence not in RECURRENCE_PATTERNS:
        raise HTTPException(422, f"Recurrence invalide. Valeurs: {', '.join(sorted(RECURRENCE_PATTERNS))}")

    # Check uniqueness
    existing = (await db.execute(
        text("SELECT id FROM routes WHERE tenant_id = :tid AND numero = :num"),
        {"tid": tid, "num": body.numero},
    )).first()
    if existing:
        raise HTTPException(409, f"La tournee {body.numero} existe deja")

    rid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO routes (
            id, tenant_id, agency_id, numero, libelle, client_id, type_mission,
            recurrence, date_debut, date_fin,
            driver_id, vehicle_id, is_subcontracted, subcontractor_id,
            montant_vente_ht, montant_achat_ht,
            adresse_chargement, site, distance_estimee_km, contraintes, notes,
            created_by
        ) VALUES (
            :id, :tid, :aid, :num, :lib, :cid, :type,
            :rec, :debut, :fin,
            :did, :vid, :sub, :subid,
            :vente, :achat,
            :addr, :site, :dist, CAST(:contraintes AS jsonb), :notes,
            :uid
        )
    """), {
        "id": str(rid), "tid": tid, "aid": body.agency_id,
        "num": body.numero, "lib": body.libelle,
        "cid": body.client_id, "type": body.type_mission,
        "rec": body.recurrence, "debut": body.date_debut, "fin": body.date_fin,
        "did": body.driver_id, "vid": body.vehicle_id,
        "sub": body.is_subcontracted, "subid": body.subcontractor_id,
        "vente": body.montant_vente_ht, "achat": body.montant_achat_ht,
        "addr": body.adresse_chargement, "site": body.site,
        "dist": body.distance_estimee_km,
        "contraintes": json.dumps(body.contraintes) if body.contraintes else None,
        "notes": body.notes, "uid": user.get("id"),
    })
    await db.commit()

    return RouteOut(
        id=str(rid), numero=body.numero, libelle=body.libelle,
        client_id=body.client_id, type_mission=body.type_mission,
        recurrence=body.recurrence, date_debut=body.date_debut, date_fin=body.date_fin,
        driver_id=body.driver_id, vehicle_id=body.vehicle_id,
        is_subcontracted=body.is_subcontracted,
        montant_vente_ht=body.montant_vente_ht, montant_achat_ht=body.montant_achat_ht,
        site=body.site, statut="ACTIF", nb_missions=0, nb_missions_completees=0,
    )


@router.get("/{route_id}", response_model=RouteDetail)
async def get_route(
    route_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    r = (await db.execute(text("""
        SELECT r.*,
               c.raison_sociale AS client_name,
               COALESCE(d.nom, d.last_name) || ' ' || COALESCE(d.prenom, d.first_name) AS driver_name,
               COALESCE(v.immatriculation, v.plate_number) AS vehicle_plate,
               (SELECT COUNT(*) FROM jobs j WHERE j.route_id = r.id) AS nb_missions,
               (SELECT COUNT(*) FROM jobs j WHERE j.route_id = r.id AND j.status IN ('CLOTUREE','FACTUREE')) AS nb_missions_completees
        FROM routes r
        LEFT JOIN customers c ON r.client_id = c.id
        LEFT JOIN drivers d ON r.driver_id = d.id
        LEFT JOIN vehicles v ON r.vehicle_id = v.id
        WHERE r.id = :id AND r.tenant_id = :tid
    """), {"id": route_id, "tid": tid})).first()
    if not r:
        raise HTTPException(404, "Tournee non trouvee")

    # Delivery points
    dp_rows = (await db.execute(text(
        "SELECT * FROM route_delivery_points WHERE route_id = :rid ORDER BY ordre"
    ), {"rid": route_id})).fetchall()
    delivery_points = [
        {"id": str(dp.id), "ordre": dp.ordre, "adresse": dp.adresse,
         "code_postal": dp.code_postal, "ville": dp.ville,
         "contact_nom": dp.contact_nom, "contact_telephone": dp.contact_telephone,
         "instructions": dp.instructions}
        for dp in dp_rows
    ]

    return RouteDetail(
        id=str(r.id), numero=r.numero, libelle=r.libelle,
        client_id=str(r.client_id) if r.client_id else None,
        client_name=r.client_name,
        type_mission=r.type_mission, recurrence=r.recurrence,
        date_debut=r.date_debut, date_fin=r.date_fin,
        driver_id=str(r.driver_id) if r.driver_id else None,
        driver_name=r.driver_name,
        vehicle_id=str(r.vehicle_id) if r.vehicle_id else None,
        vehicle_plate=r.vehicle_plate,
        is_subcontracted=r.is_subcontracted or False,
        subcontractor_id=str(r.subcontractor_id) if r.subcontractor_id else None,
        montant_vente_ht=r.montant_vente_ht, montant_achat_ht=r.montant_achat_ht,
        adresse_chargement=r.adresse_chargement,
        site=r.site, distance_estimee_km=r.distance_estimee_km,
        contraintes=r.contraintes, notes=r.notes,
        agency_id=str(r.agency_id) if r.agency_id else None,
        statut=r.statut,
        nb_missions=r.nb_missions, nb_missions_completees=r.nb_missions_completees,
        created_at=r.created_at.isoformat() if r.created_at else None,
        delivery_points=delivery_points,
    )


@router.put("/{route_id}", response_model=RouteOut)
async def update_route(
    route_id: str,
    body: RouteUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    existing = (await db.execute(
        text("SELECT id FROM routes WHERE id = :id AND tenant_id = :tid"),
        {"id": route_id, "tid": tid},
    )).first()
    if not existing:
        raise HTTPException(404, "Tournee non trouvee")

    await db.execute(text("""
        UPDATE routes SET
            libelle = :lib, client_id = :cid, type_mission = :type,
            recurrence = :rec, date_debut = :debut, date_fin = :fin,
            driver_id = :did, vehicle_id = :vid,
            is_subcontracted = :sub, subcontractor_id = :subid,
            montant_vente_ht = :vente, montant_achat_ht = :achat,
            adresse_chargement = :addr, site = :site, distance_estimee_km = :dist,
            contraintes = CAST(:contraintes AS jsonb), notes = :notes,
            statut = COALESCE(:statut, statut),
            updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": route_id, "tid": tid,
        "lib": body.libelle, "cid": body.client_id, "type": body.type_mission,
        "rec": body.recurrence, "debut": body.date_debut, "fin": body.date_fin,
        "did": body.driver_id, "vid": body.vehicle_id,
        "sub": body.is_subcontracted, "subid": body.subcontractor_id,
        "vente": body.montant_vente_ht, "achat": body.montant_achat_ht,
        "addr": body.adresse_chargement, "site": body.site, "dist": body.distance_estimee_km,
        "contraintes": json.dumps(body.contraintes) if body.contraintes else None,
        "notes": body.notes, "statut": body.statut,
    })
    await db.commit()
    return await get_route(route_id, tenant, user, db)


@router.post("/{route_id}/generate-missions")
async def generate_missions(
    route_id: str,
    body: GenerateMissionsRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate individual missions from a route template for a date range."""
    tid = str(tenant.tenant_id)

    r = (await db.execute(text(
        "SELECT * FROM routes WHERE id = :id AND tenant_id = :tid AND statut = 'ACTIF'"
    ), {"id": route_id, "tid": tid})).first()
    if not r:
        raise HTTPException(404, "Tournee non trouvee ou inactive")

    # Expand recurrence to dates
    exec_dates = _expand_dates(r.recurrence, body.start_date, body.end_date)
    if not exec_dates:
        raise HTTPException(422, "Aucune date de mission pour cette periode et cette recurrence")

    driver_id = body.override_driver_id or (str(r.driver_id) if r.driver_id else None)
    vehicle_id = body.override_vehicle_id or (str(r.vehicle_id) if r.vehicle_id else None)

    # Get next mission number
    last_num = (await db.execute(text(
        "SELECT numero FROM jobs WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 1"
    ), {"tid": tid})).scalar()

    counter = 1
    if last_num:
        try:
            counter = int(last_num.split("-")[-1]) + 1
        except (ValueError, IndexError):
            pass

    created_missions = []
    for exec_date in exec_dates:
        # Check no duplicate for this route+date
        existing = (await db.execute(text(
            "SELECT id FROM jobs WHERE route_id = :rid AND date_chargement_prevue = :d"
        ), {"rid": route_id, "d": exec_date})).first()
        if existing:
            continue

        mid = uuid.uuid4()
        numero = f"MIS-{exec_date.year}-{exec_date.month:02d}-{counter:05d}"
        counter += 1

        await db.execute(text("""
            INSERT INTO jobs (
                id, tenant_id, numero, customer_id, type_mission,
                date_chargement_prevue, date_livraison_prevue,
                driver_id, vehicle_id,
                is_subcontracted, subcontractor_id,
                montant_vente_ht, montant_achat_ht,
                notes_exploitation, route_id,
                status, created_by
            ) VALUES (
                :id, :tid, :num, :cid, :type,
                :date_charge, :date_livre,
                :did, :vid,
                :sub, :subid,
                :vente, :achat,
                :notes, :rid,
                'PLANIFIEE', :uid
            )
        """), {
            "id": str(mid), "tid": tid, "num": numero,
            "cid": str(r.client_id) if r.client_id else None,
            "type": r.type_mission,
            "date_charge": exec_date, "date_livre": exec_date,
            "did": driver_id, "vid": vehicle_id,
            "sub": r.is_subcontracted, "subid": str(r.subcontractor_id) if r.subcontractor_id else None,
            "vente": r.montant_vente_ht, "achat": r.montant_achat_ht,
            "notes": f"Generee depuis tournee {r.numero}", "rid": route_id,
            "uid": user.get("id"),
        })
        created_missions.append({"id": str(mid), "numero": numero, "date": exec_date.isoformat()})

    await db.commit()
    return {"generated": len(created_missions), "missions": created_missions}


@router.get("/{route_id}/missions")
async def list_route_missions(
    route_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List all missions generated from this route."""
    tid = str(tenant.tenant_id)
    rows = (await db.execute(text("""
        SELECT j.id, j.numero, j.status AS statut, j.date_chargement_prevue, j.date_livraison_prevue,
               j.montant_vente_ht, j.montant_achat_ht,
               COALESCE(d.nom, d.last_name) || ' ' || COALESCE(d.prenom, d.first_name) AS driver_name,
               COALESCE(v.immatriculation, v.plate_number) AS vehicle_plate
        FROM jobs j
        LEFT JOIN drivers d ON j.driver_id = d.id
        LEFT JOIN vehicles v ON j.vehicle_id = v.id
        WHERE j.route_id = :rid AND j.tenant_id = :tid
        ORDER BY j.date_chargement_prevue DESC
        LIMIT :lim OFFSET :off
    """), {"rid": route_id, "tid": tid, "lim": limit, "off": offset})).fetchall()
    return [
        {
            "id": str(r.id), "numero": r.numero, "statut": r.statut,
            "date_chargement": r.date_chargement_prevue.isoformat() if r.date_chargement_prevue else None,
            "date_livraison": r.date_livraison_prevue.isoformat() if r.date_livraison_prevue else None,
            "montant_vente_ht": float(r.montant_vente_ht) if r.montant_vente_ht else None,
            "driver_name": r.driver_name, "vehicle_plate": r.vehicle_plate,
        }
        for r in rows
    ]


@router.post("/{route_id}/delivery-points", status_code=201)
async def add_delivery_point(
    route_id: str,
    body: DeliveryPointCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    dpid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO route_delivery_points (id, tenant_id, route_id, ordre, adresse, code_postal, ville,
            contact_nom, contact_telephone, instructions)
        VALUES (:id, :tid, :rid, :ordre, :addr, :cp, :ville, :nom, :tel, :instr)
    """), {
        "id": str(dpid), "tid": tid, "rid": route_id, "ordre": body.ordre,
        "addr": body.adresse, "cp": body.code_postal, "ville": body.ville,
        "nom": body.contact_nom, "tel": body.contact_telephone, "instr": body.instructions,
    })
    await db.commit()
    return {"id": str(dpid)}


@router.patch("/{route_id}/suspend")
async def suspend_route(
    route_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    await db.execute(text(
        "UPDATE routes SET statut = 'SUSPENDUE', updated_at = NOW() WHERE id = :id AND tenant_id = :tid"
    ), {"id": route_id, "tid": tid})
    await db.commit()
    return {"ok": True, "statut": "SUSPENDUE"}


@router.patch("/{route_id}/activate")
async def activate_route(
    route_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    await db.execute(text(
        "UPDATE routes SET statut = 'ACTIF', updated_at = NOW() WHERE id = :id AND tenant_id = :tid"
    ), {"id": route_id, "tid": tid})
    await db.commit()
    return {"ok": True, "statut": "ACTIF"}
