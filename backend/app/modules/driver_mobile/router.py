from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/driver", tags=["driver-mobile"])


# ---- Schemas ----

class DriverMissionOut(BaseModel):
    id: str
    numero: str | None = None
    client_name: str | None = None
    statut: str | None = None
    type_mission: str | None = None
    date_chargement_prevue: str | None = None
    date_livraison_prevue: str | None = None
    pickup_address_text: str | None = None
    delivery_address_text: str | None = None


class DriverEventCreate(BaseModel):
    event_type: str  # DEPART_CHARGEMENT, ARRIVE_CHARGEMENT, CHARGEMENT_TERMINE, EN_ROUTE, ARRIVE_LIVRAISON, LIVRAISON_TERMINEE, INCIDENT, PAUSE, REPRISE
    latitude: float | None = None
    longitude: float | None = None
    notes: str | None = None
    photo_s3_key: str | None = None


class DriverEventOut(BaseModel):
    id: str
    event_type: str
    latitude: float | None = None
    longitude: float | None = None
    notes: str | None = None
    created_at: str | None = None


class MobilePodCreate(BaseModel):
    fichier_s3_key: str
    fichier_nom_original: str
    fichier_taille_octets: int
    fichier_mime_type: str
    delivery_point_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    has_reserves: bool = False
    reserves_texte: str | None = None


# ---- Helpers ----

VALID_EVENT_TYPES = {
    "DEPART_CHARGEMENT", "ARRIVE_CHARGEMENT", "CHARGEMENT_TERMINE",
    "EN_ROUTE", "ARRIVE_LIVRAISON", "LIVRAISON_TERMINEE",
    "INCIDENT", "PAUSE", "REPRISE",
}


async def _resolve_driver_id(db: AsyncSession, tid: str, user: dict) -> str:
    """Resolve the driver record for the current authenticated user."""
    user_id = user.get("id") or user.get("sub")
    user_email = user.get("email")
    row = (await db.execute(text("""
        SELECT id FROM drivers
        WHERE tenant_id = :tid AND (user_id = :uid OR email = :email)
        LIMIT 1
    """), {"tid": tid, "uid": user_id, "email": user_email})).first()
    if not row:
        raise HTTPException(403, "No driver profile linked to this user account")
    return str(row.id)


# ---- Endpoints ----

@router.get("/my-missions", response_model=list[DriverMissionOut])
async def list_my_missions(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
):
    tid = str(tenant.tenant_id)
    driver_id = await _resolve_driver_id(db, tid, user)

    q = """
        SELECT j.id, j.numero, c.name AS client_name, j.statut,
               j.type_mission, j.date_chargement_prevue, j.date_livraison_prevue,
               j.pickup_address_text, j.delivery_address_text
        FROM jobs j
        LEFT JOIN customers c ON j.customer_id = c.id
        WHERE j.tenant_id = :tid AND j.driver_id = :did
    """
    params: dict = {"tid": tid, "did": driver_id}
    if statut:
        q += " AND j.statut = :statut"
        params["statut"] = statut
    if date_from:
        q += " AND j.date_chargement_prevue >= :dfrom"
        params["dfrom"] = date_from
    if date_to:
        q += " AND j.date_chargement_prevue <= :dto"
        params["dto"] = date_to
    q += " ORDER BY j.date_chargement_prevue DESC"

    rows = (await db.execute(text(q), params)).fetchall()
    return [DriverMissionOut(
        id=str(r.id),
        numero=r.numero,
        client_name=r.client_name,
        statut=r.statut,
        type_mission=r.type_mission,
        date_chargement_prevue=str(r.date_chargement_prevue) if r.date_chargement_prevue else None,
        date_livraison_prevue=str(r.date_livraison_prevue) if r.date_livraison_prevue else None,
        pickup_address_text=r.pickup_address_text,
        delivery_address_text=r.delivery_address_text,
    ) for r in rows]


@router.get("/my-missions/{job_id}", response_model=dict)
async def get_my_mission(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    driver_id = await _resolve_driver_id(db, tid, user)

    row = (await db.execute(text("""
        SELECT j.*, c.name AS client_name
        FROM jobs j
        LEFT JOIN customers c ON j.customer_id = c.id
        WHERE j.id = :jid AND j.tenant_id = :tid AND j.driver_id = :did
    """), {"jid": job_id, "tid": tid, "did": driver_id})).first()
    if not row:
        raise HTTPException(404, "Mission not found or not assigned to you")

    # Fetch delivery points
    delivery_points = (await db.execute(text("""
        SELECT * FROM delivery_points WHERE job_id = :jid ORDER BY point_order
    """), {"jid": job_id})).fetchall()

    # Fetch goods
    goods = (await db.execute(text("""
        SELECT * FROM goods WHERE job_id = :jid ORDER BY created_at
    """), {"jid": job_id})).fetchall()

    return {
        "id": str(row.id),
        "numero": row.numero,
        "client_name": row.client_name,
        "statut": row.statut,
        "type_mission": row.type_mission,
        "date_chargement_prevue": str(row.date_chargement_prevue) if row.date_chargement_prevue else None,
        "date_livraison_prevue": str(row.date_livraison_prevue) if row.date_livraison_prevue else None,
        "pickup_address_text": row.pickup_address_text,
        "delivery_address_text": row.delivery_address_text,
        "delivery_points": [{
            "id": str(dp.id),
            "address_text": dp.address_text if hasattr(dp, "address_text") else None,
            "point_order": dp.point_order if hasattr(dp, "point_order") else None,
            "type": dp.type if hasattr(dp, "type") else None,
        } for dp in delivery_points],
        "goods": [{
            "id": str(g.id),
            "description": g.description if hasattr(g, "description") else None,
            "quantity": float(g.quantity) if hasattr(g, "quantity") and g.quantity else None,
            "weight_kg": float(g.weight_kg) if hasattr(g, "weight_kg") and g.weight_kg else None,
        } for g in goods],
    }


@router.post("/my-missions/{job_id}/events", response_model=DriverEventOut, status_code=201)
async def create_event(
    job_id: str,
    body: DriverEventCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    driver_id = await _resolve_driver_id(db, tid, user)

    # Verify job belongs to this driver
    job = (await db.execute(text("""
        SELECT id, statut FROM jobs
        WHERE id = :jid AND tenant_id = :tid AND driver_id = :did
    """), {"jid": job_id, "tid": tid, "did": driver_id})).first()
    if not job:
        raise HTTPException(404, "Mission not found or not assigned to you")

    if body.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(400, f"Invalid event_type. Must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}")

    eid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO driver_events
            (id, tenant_id, job_id, driver_id, event_type, latitude, longitude,
             notes, photo_s3_key)
        VALUES (:id, :tid, :jid, :did, :etype, :lat, :lon, :notes, :photo)
    """), {
        "id": str(eid), "tid": tid, "jid": job_id, "did": driver_id,
        "etype": body.event_type, "lat": body.latitude, "lon": body.longitude,
        "notes": body.notes, "photo": body.photo_s3_key,
    })

    # Auto-update job statut based on event_type
    if body.event_type == "DEPART_CHARGEMENT" and job.statut == "AFFECTEE":
        await db.execute(text("""
            UPDATE jobs SET statut = 'EN_COURS' WHERE id = :jid AND tenant_id = :tid
        """), {"jid": job_id, "tid": tid})
    elif body.event_type == "LIVRAISON_TERMINEE" and job.statut == "EN_COURS":
        await db.execute(text("""
            UPDATE jobs SET statut = 'LIVREE' WHERE id = :jid AND tenant_id = :tid
        """), {"jid": job_id, "tid": tid})

    await db.commit()

    row = (await db.execute(text("""
        SELECT * FROM driver_events WHERE id = :id
    """), {"id": str(eid)})).first()

    return DriverEventOut(
        id=str(row.id),
        event_type=row.event_type,
        latitude=float(row.latitude) if row.latitude else None,
        longitude=float(row.longitude) if row.longitude else None,
        notes=row.notes,
        created_at=str(row.created_at) if row.created_at else None,
    )


@router.get("/my-missions/{job_id}/events", response_model=list[DriverEventOut])
async def list_events(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    driver_id = await _resolve_driver_id(db, tid, user)

    # Verify job belongs to this driver
    job = (await db.execute(text("""
        SELECT id FROM jobs WHERE id = :jid AND tenant_id = :tid AND driver_id = :did
    """), {"jid": job_id, "tid": tid, "did": driver_id})).first()
    if not job:
        raise HTTPException(404, "Mission not found or not assigned to you")

    rows = (await db.execute(text("""
        SELECT * FROM driver_events
        WHERE job_id = :jid AND tenant_id = :tid
        ORDER BY created_at
    """), {"jid": job_id, "tid": tid})).fetchall()

    return [DriverEventOut(
        id=str(r.id),
        event_type=r.event_type,
        latitude=float(r.latitude) if r.latitude else None,
        longitude=float(r.longitude) if r.longitude else None,
        notes=r.notes,
        created_at=str(r.created_at) if r.created_at else None,
    ) for r in rows]


@router.post("/my-missions/{job_id}/pod", response_model=dict, status_code=201)
async def upload_pod(
    job_id: str,
    body: MobilePodCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    driver_id = await _resolve_driver_id(db, tid, user)

    # Verify job belongs to this driver
    job = (await db.execute(text("""
        SELECT id FROM jobs WHERE id = :jid AND tenant_id = :tid AND driver_id = :did
    """), {"jid": job_id, "tid": tid, "did": driver_id})).first()
    if not job:
        raise HTTPException(404, "Mission not found or not assigned to you")

    pod_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO proof_of_delivery
            (id, tenant_id, job_id, delivery_point_id,
             fichier_s3_key, fichier_nom_original, fichier_taille_octets,
             fichier_mime_type, latitude, longitude,
             has_reserves, reserves_texte, uploaded_by_driver_id)
        VALUES (:id, :tid, :jid, :dpid,
                :s3key, :fname, :fsize,
                :fmime, :lat, :lon,
                :has_res, :res_txt, :did)
    """), {
        "id": str(pod_id), "tid": tid, "jid": job_id,
        "dpid": body.delivery_point_id,
        "s3key": body.fichier_s3_key, "fname": body.fichier_nom_original,
        "fsize": body.fichier_taille_octets, "fmime": body.fichier_mime_type,
        "lat": body.latitude, "lon": body.longitude,
        "has_res": body.has_reserves, "res_txt": body.reserves_texte,
        "did": driver_id,
    })
    await db.commit()

    return {
        "id": str(pod_id),
        "job_id": job_id,
        "fichier_s3_key": body.fichier_s3_key,
        "fichier_nom_original": body.fichier_nom_original,
        "has_reserves": body.has_reserves,
        "created": True,
    }
