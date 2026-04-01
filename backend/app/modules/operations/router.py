"""Router for operational data — complaints, infractions, violations, leaves, schedules, repairs."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.modules.operations.schemas import (
    COMPLAINT_STATUSES,
    LEAVE_STATUSES,
    LEAVE_TYPES,
    PAYMENT_STATUSES,
    REPAIR_CATEGORIES,
    REPAIR_STATUSES,
    SCHEDULE_STATUSES,
    SEVERITIES,
    ComplaintCreate,
    ComplaintOut,
    InfractionCreate,
    InfractionOut,
    LeaveCreate,
    LeaveOut,
    RepairCreate,
    RepairOut,
    ScheduleCreate,
    ScheduleOut,
    ViolationCreate,
    ViolationOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/operations", tags=["operations"])


# ── Row mappers ──────────────────────────────────────────────────

def _complaint_from_row(r) -> ComplaintOut:
    return ComplaintOut(
        id=str(r.id),
        tenant_id=str(r.tenant_id),
        date_incident=r.date_incident,
        client_name=r.client_name,
        client_id=str(r.client_id) if r.client_id else None,
        contact_name=r.contact_name,
        subject=r.subject,
        driver_id=str(r.driver_id) if r.driver_id else None,
        severity=r.severity,
        status=r.status,
        resolution=r.resolution,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _infraction_from_row(r) -> InfractionOut:
    return InfractionOut(
        id=str(r.id),
        tenant_id=str(r.tenant_id),
        driver_id=str(r.driver_id),
        year=r.year,
        month=r.month,
        infraction_count=r.infraction_count,
        anomaly_count=r.anomaly_count,
        notes=r.notes,
        created_at=r.created_at,
    )


def _violation_from_row(r) -> ViolationOut:
    return ViolationOut(
        id=str(r.id),
        tenant_id=str(r.tenant_id),
        date_infraction=r.date_infraction,
        lieu=r.lieu,
        vehicle_id=str(r.vehicle_id) if r.vehicle_id else None,
        immatriculation=r.immatriculation,
        description=r.description,
        numero_avis=r.numero_avis,
        montant=r.montant,
        statut_paiement=r.statut_paiement,
        statut_dossier=r.statut_dossier,
        driver_id=str(r.driver_id) if r.driver_id else None,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _leave_from_row(r) -> LeaveOut:
    return LeaveOut(
        id=str(r.id),
        tenant_id=str(r.tenant_id),
        driver_id=str(r.driver_id),
        date_debut=r.date_debut,
        date_fin=r.date_fin,
        type_conge=r.type_conge,
        statut=r.statut,
        notes=r.notes,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# =====================================================================
# Customer Complaints (RECLAMATIONS)
# =====================================================================

@router.get("/complaints", response_model=list[ComplaintOut])
async def list_complaints(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[ComplaintOut]:
    """List customer complaints for the tenant."""
    q = "SELECT * FROM customer_complaints WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if status:
        if status not in COMPLAINT_STATUSES:
            raise HTTPException(
                422,
                f"Statut invalide. Valeurs: {', '.join(sorted(COMPLAINT_STATUSES))}",
            )
        q += " AND status = :status"
        params["status"] = status
    q += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    rows = await db.execute(text(q), params)
    return [_complaint_from_row(r) for r in rows.fetchall()]


@router.post("/complaints", response_model=ComplaintOut, status_code=201)
async def create_complaint(
    body: ComplaintCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComplaintOut:
    """Create a new customer complaint."""
    if body.severity not in SEVERITIES:
        raise HTTPException(422, f"Severite invalide. Valeurs: {', '.join(sorted(SEVERITIES))}")
    if body.status not in COMPLAINT_STATUSES:
        raise HTTPException(422, f"Statut invalide. Valeurs: {', '.join(sorted(COMPLAINT_STATUSES))}")

    tid = str(tenant.tenant_id)
    cid = str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO customer_complaints (
            id, tenant_id, date_incident, client_name, client_id, contact_name,
            subject, driver_id, severity, status, resolution
        ) VALUES (
            :id, :tid, :date_incident, :client_name, :client_id, :contact_name,
            :subject, :driver_id, :severity, :status, :resolution
        )
    """), {
        "id": cid, "tid": tid,
        "date_incident": body.date_incident,
        "client_name": body.client_name,
        "client_id": body.client_id,
        "contact_name": body.contact_name,
        "subject": body.subject,
        "driver_id": body.driver_id,
        "severity": body.severity,
        "status": body.status,
        "resolution": body.resolution,
    })
    await db.commit()

    row = (await db.execute(
        text("SELECT * FROM customer_complaints WHERE id = :id"),
        {"id": cid},
    )).first()
    return _complaint_from_row(row)


# =====================================================================
# Driver Infractions (INFRACTIONS CHAUFFEURS)
# =====================================================================

@router.get("/infractions", response_model=list[InfractionOut])
async def list_infractions(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    driver_id: str | None = Query(None, description="Filter by driver"),
    year: int | None = Query(None, description="Filter by year"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[InfractionOut]:
    """List driver infraction records for the tenant."""
    q = "SELECT * FROM driver_infractions WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if driver_id:
        q += " AND driver_id = :driver_id"
        params["driver_id"] = driver_id
    if year:
        q += " AND year = :year"
        params["year"] = year
    q += " ORDER BY year DESC, month DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    rows = await db.execute(text(q), params)
    return [_infraction_from_row(r) for r in rows.fetchall()]


@router.post("/infractions", response_model=InfractionOut, status_code=201)
async def create_infraction(
    body: InfractionCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InfractionOut:
    """Create or update a monthly infraction record (upsert on unique constraint)."""
    tid = str(tenant.tenant_id)

    # Upsert: if a record for the same tenant/driver/year/month exists, update it.
    result = await db.execute(text("""
        INSERT INTO driver_infractions (
            id, tenant_id, driver_id, year, month,
            infraction_count, anomaly_count, notes
        ) VALUES (
            gen_random_uuid(), :tid, :driver_id, :year, :month,
            :infraction_count, :anomaly_count, :notes
        )
        ON CONFLICT (tenant_id, driver_id, year, month)
        DO UPDATE SET
            infraction_count = EXCLUDED.infraction_count,
            anomaly_count = EXCLUDED.anomaly_count,
            notes = EXCLUDED.notes
        RETURNING *
    """), {
        "tid": tid,
        "driver_id": body.driver_id,
        "year": body.year,
        "month": body.month,
        "infraction_count": body.infraction_count,
        "anomaly_count": body.anomaly_count,
        "notes": body.notes,
    })
    await db.commit()

    row = result.first()
    return _infraction_from_row(row)


# =====================================================================
# Traffic Violations (CONTRAVENTIONS)
# =====================================================================

@router.get("/violations", response_model=list[ViolationOut])
async def list_violations(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    vehicle_id: str | None = Query(None, description="Filter by vehicle"),
    statut_paiement: str | None = Query(None, description="Filter by payment status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[ViolationOut]:
    """List traffic violations for the tenant."""
    q = "SELECT * FROM traffic_violations WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if vehicle_id:
        q += " AND vehicle_id = :vehicle_id"
        params["vehicle_id"] = vehicle_id
    if statut_paiement:
        if statut_paiement not in PAYMENT_STATUSES:
            raise HTTPException(
                422,
                f"Statut paiement invalide. Valeurs: {', '.join(sorted(PAYMENT_STATUSES))}",
            )
        q += " AND statut_paiement = :statut_paiement"
        params["statut_paiement"] = statut_paiement
    q += " ORDER BY date_infraction DESC NULLS LAST LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    rows = await db.execute(text(q), params)
    return [_violation_from_row(r) for r in rows.fetchall()]


@router.post("/violations", response_model=ViolationOut, status_code=201)
async def create_violation(
    body: ViolationCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ViolationOut:
    """Create a new traffic violation record."""
    if body.statut_paiement not in PAYMENT_STATUSES:
        raise HTTPException(
            422,
            f"Statut paiement invalide. Valeurs: {', '.join(sorted(PAYMENT_STATUSES))}",
        )

    tid = str(tenant.tenant_id)
    vid = str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO traffic_violations (
            id, tenant_id, date_infraction, lieu, vehicle_id, immatriculation,
            description, numero_avis, montant, statut_paiement, statut_dossier, driver_id
        ) VALUES (
            :id, :tid, :date_infraction, :lieu, :vehicle_id, :immatriculation,
            :description, :numero_avis, :montant, :statut_paiement, :statut_dossier, :driver_id
        )
    """), {
        "id": vid, "tid": tid,
        "date_infraction": body.date_infraction,
        "lieu": body.lieu,
        "vehicle_id": body.vehicle_id,
        "immatriculation": body.immatriculation,
        "description": body.description,
        "numero_avis": body.numero_avis,
        "montant": body.montant,
        "statut_paiement": body.statut_paiement,
        "statut_dossier": body.statut_dossier,
        "driver_id": body.driver_id,
    })
    await db.commit()

    row = (await db.execute(
        text("SELECT * FROM traffic_violations WHERE id = :id"),
        {"id": vid},
    )).first()
    return _violation_from_row(row)


# =====================================================================
# Driver Leaves (Tableau des congés)
# =====================================================================

@router.get("/leaves", response_model=list[LeaveOut])
async def list_leaves(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    driver_id: str | None = Query(None, description="Filter by driver"),
    type_conge: str | None = Query(None, description="Filter by leave type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[LeaveOut]:
    """List driver leaves for the tenant."""
    q = "SELECT * FROM driver_leaves WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if driver_id:
        q += " AND driver_id = :driver_id"
        params["driver_id"] = driver_id
    if type_conge:
        if type_conge not in LEAVE_TYPES:
            raise HTTPException(
                422,
                f"Type conge invalide. Valeurs: {', '.join(sorted(LEAVE_TYPES))}",
            )
        q += " AND type_conge = :type_conge"
        params["type_conge"] = type_conge
    q += " ORDER BY date_debut DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    rows = await db.execute(text(q), params)
    return [_leave_from_row(r) for r in rows.fetchall()]


@router.post("/leaves", response_model=LeaveOut, status_code=201)
async def create_leave(
    body: LeaveCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaveOut:
    """Create a new driver leave record."""
    if body.type_conge not in LEAVE_TYPES:
        raise HTTPException(422, f"Type conge invalide. Valeurs: {', '.join(sorted(LEAVE_TYPES))}")
    if body.statut not in LEAVE_STATUSES:
        raise HTTPException(422, f"Statut invalide. Valeurs: {', '.join(sorted(LEAVE_STATUSES))}")
    if body.date_fin < body.date_debut:
        raise HTTPException(422, "date_fin doit etre >= date_debut")

    tid = str(tenant.tenant_id)
    lid = str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO driver_leaves (
            id, tenant_id, driver_id, date_debut, date_fin,
            type_conge, statut, notes
        ) VALUES (
            :id, :tid, :driver_id, :date_debut, :date_fin,
            :type_conge, :statut, :notes
        )
    """), {
        "id": lid, "tid": tid,
        "driver_id": body.driver_id,
        "date_debut": body.date_debut,
        "date_fin": body.date_fin,
        "type_conge": body.type_conge,
        "statut": body.statut,
        "notes": body.notes,
    })
    await db.commit()

    row = (await db.execute(
        text("SELECT * FROM driver_leaves WHERE id = :id"),
        {"id": lid},
    )).first()
    return _leave_from_row(row)


# ── Row mappers (schedules / repairs) ───────────────────────────

def _schedule_from_row(r) -> ScheduleOut:
    return ScheduleOut(
        id=str(r.id),
        tenant_id=str(r.tenant_id),
        driver_id=str(r.driver_id),
        date=r.date,
        status=r.status,
        shift_start=r.shift_start,
        shift_end=r.shift_end,
        notes=r.notes,
        created_at=r.created_at,
    )


def _repair_from_row(r) -> RepairOut:
    return RepairOut(
        id=str(r.id),
        tenant_id=str(r.tenant_id),
        vehicle_id=str(r.vehicle_id),
        immatriculation=r.immatriculation,
        category=r.category,
        description=r.description,
        status=r.status,
        date_signalement=r.date_signalement,
        date_realisation=r.date_realisation,
        cout=r.cout,
        prestataire=r.prestataire,
        notes=r.notes,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# =====================================================================
# Staff Schedules (Planning de travail SAF AT)
# =====================================================================

@router.get("/schedules", response_model=list[ScheduleOut])
async def list_schedules(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    driver_id: str | None = Query(None, description="Filter by driver"),
    date: str | None = Query(None, description="Filter by date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[ScheduleOut]:
    """List staff schedules for the tenant."""
    q = "SELECT * FROM staff_schedules WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if driver_id:
        q += " AND driver_id = :driver_id"
        params["driver_id"] = driver_id
    if date:
        q += " AND date = :date"
        params["date"] = date
    q += " ORDER BY date DESC, created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    rows = await db.execute(text(q), params)
    return [_schedule_from_row(r) for r in rows.fetchall()]


@router.post("/schedules", response_model=ScheduleOut, status_code=201)
async def create_schedule(
    body: ScheduleCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScheduleOut:
    """Create or update a staff schedule entry (upsert on unique constraint)."""
    if body.status not in SCHEDULE_STATUSES:
        raise HTTPException(
            422,
            f"Statut invalide. Valeurs: {', '.join(sorted(SCHEDULE_STATUSES))}",
        )

    tid = str(tenant.tenant_id)

    # Upsert: if a record for the same tenant/driver/date exists, update it.
    result = await db.execute(text("""
        INSERT INTO staff_schedules (
            id, tenant_id, driver_id, date, status,
            shift_start, shift_end, notes
        ) VALUES (
            gen_random_uuid(), :tid, :driver_id, :date, :status,
            :shift_start, :shift_end, :notes
        )
        ON CONFLICT (tenant_id, driver_id, date)
        DO UPDATE SET
            status = EXCLUDED.status,
            shift_start = EXCLUDED.shift_start,
            shift_end = EXCLUDED.shift_end,
            notes = EXCLUDED.notes
        RETURNING *
    """), {
        "tid": tid,
        "driver_id": body.driver_id,
        "date": body.date,
        "status": body.status,
        "shift_start": body.shift_start,
        "shift_end": body.shift_end,
        "notes": body.notes,
    })
    await db.commit()

    row = result.first()
    return _schedule_from_row(row)


# =====================================================================
# Vehicle Repairs (tableau REPARATION 3 mois format)
# =====================================================================

@router.get("/repairs", response_model=list[RepairOut])
async def list_repairs(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    vehicle_id: str | None = Query(None, description="Filter by vehicle"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[RepairOut]:
    """List vehicle repairs for the tenant."""
    q = "SELECT * FROM vehicle_repairs WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if vehicle_id:
        q += " AND vehicle_id = :vehicle_id"
        params["vehicle_id"] = vehicle_id
    if status:
        if status not in REPAIR_STATUSES:
            raise HTTPException(
                422,
                f"Statut invalide. Valeurs: {', '.join(sorted(REPAIR_STATUSES))}",
            )
        q += " AND status = :status"
        params["status"] = status
    q += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    rows = await db.execute(text(q), params)
    return [_repair_from_row(r) for r in rows.fetchall()]


@router.post("/repairs", response_model=RepairOut, status_code=201)
async def create_repair(
    body: RepairCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RepairOut:
    """Create a new vehicle repair record."""
    if body.category not in REPAIR_CATEGORIES:
        raise HTTPException(
            422,
            f"Categorie invalide. Valeurs: {', '.join(sorted(REPAIR_CATEGORIES))}",
        )
    if body.status not in REPAIR_STATUSES:
        raise HTTPException(
            422,
            f"Statut invalide. Valeurs: {', '.join(sorted(REPAIR_STATUSES))}",
        )

    tid = str(tenant.tenant_id)
    rid = str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO vehicle_repairs (
            id, tenant_id, vehicle_id, immatriculation, category,
            description, status, date_signalement, date_realisation,
            cout, prestataire, notes
        ) VALUES (
            :id, :tid, :vehicle_id, :immatriculation, :category,
            :description, :status, :date_signalement, :date_realisation,
            :cout, :prestataire, :notes
        )
    """), {
        "id": rid, "tid": tid,
        "vehicle_id": body.vehicle_id,
        "immatriculation": body.immatriculation,
        "category": body.category,
        "description": body.description,
        "status": body.status,
        "date_signalement": body.date_signalement,
        "date_realisation": body.date_realisation,
        "cout": body.cout,
        "prestataire": body.prestataire,
        "notes": body.notes,
    })
    await db.commit()

    row = (await db.execute(
        text("SELECT * FROM vehicle_repairs WHERE id = :id"),
        {"id": rid},
    )).first()
    return _repair_from_row(row)
