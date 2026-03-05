from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/planning", tags=["planning"])


# ---- Schemas ----

class TimeBlock(BaseModel):
    job_id: str
    numero: str | None = None
    client_name: str | None = None
    statut: str
    start: str
    end: str
    type_mission: str | None = None
    is_subcontracted: bool = False


class DriverPlanning(BaseModel):
    driver_id: str
    driver_name: str
    agency_id: str | None = None
    conformite_statut: str | None = None
    blocks: list[TimeBlock] = []


class VehiclePlanning(BaseModel):
    vehicle_id: str
    plate: str
    categorie: str | None = None
    conformite_statut: str | None = None
    blocks: list[TimeBlock] = []


class AvailabilityCheck(BaseModel):
    driver_id: str | None = None
    vehicle_id: str | None = None
    start: str
    end: str


class AvailabilityResult(BaseModel):
    available: bool
    conflicts: list[TimeBlock] = []


class ValidationCheck(BaseModel):
    check: str
    passed: bool
    message: str


class ValidateAssignmentRequest(BaseModel):
    job_id: str
    driver_id: str | None = None
    vehicle_id: str | None = None


class ValidationResult(BaseModel):
    checks: list[ValidationCheck] = []
    can_assign: bool = True


# ---- Endpoints ----

@router.get("/drivers", response_model=list[DriverPlanning])
async def driver_planning(
    start: date = Query(...),
    end: date = Query(...),
    agency_id: str | None = Query(None),
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)

    # Get all active drivers
    dq = """
        SELECT d.id, COALESCE(d.nom || ' ' || d.prenom, d.first_name || ' ' || d.last_name, 'N/A') as driver_name,
               d.agency_id, d.conformite_statut
        FROM drivers d
        WHERE d.tenant_id = :tid AND COALESCE(d.statut, 'ACTIF') = 'ACTIF'
    """
    dparams: dict = {"tid": tid}
    if agency_id:
        dq += " AND d.agency_id = :agency_id"
        dparams["agency_id"] = agency_id
    dq += " ORDER BY d.nom, d.prenom, d.last_name"

    drivers_rows = (await db.execute(text(dq), dparams)).fetchall()

    # Get missions for the date range
    missions = (await db.execute(text("""
        SELECT j.id as job_id, j.numero, j.status, j.type_mission, j.is_subcontracted,
               j.driver_id, j.date_chargement_prevue, j.date_livraison_prevue,
               c.raison_sociale as client_name
        FROM jobs j
        LEFT JOIN customers c ON c.id = j.customer_id
        WHERE j.tenant_id = :tid
          AND j.driver_id IS NOT NULL
          AND j.date_chargement_prevue < :end_date
          AND j.date_livraison_prevue > :start_date
          AND j.status NOT IN ('ANNULEE', 'BROUILLON')
    """), {"tid": tid, "start_date": start, "end_date": end})).fetchall()

    # Group missions by driver
    driver_missions: dict[str, list] = {}
    for m in missions:
        did = str(m.driver_id)
        if did not in driver_missions:
            driver_missions[did] = []
        driver_missions[did].append(TimeBlock(
            job_id=str(m.job_id), numero=m.numero,
            client_name=m.client_name,
            statut=m.status or "BROUILLON",
            start=str(m.date_chargement_prevue) if m.date_chargement_prevue else "",
            end=str(m.date_livraison_prevue) if m.date_livraison_prevue else "",
            type_mission=m.type_mission,
            is_subcontracted=bool(m.is_subcontracted),
        ))

    return [DriverPlanning(
        driver_id=str(d.id),
        driver_name=d.driver_name,
        agency_id=str(d.agency_id) if d.agency_id else None,
        conformite_statut=d.conformite_statut,
        blocks=driver_missions.get(str(d.id), []),
    ) for d in drivers_rows]


@router.get("/vehicles", response_model=list[VehiclePlanning])
async def vehicle_planning(
    start: date = Query(...),
    end: date = Query(...),
    agency_id: str | None = Query(None),
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)

    vq = """
        SELECT v.id, COALESCE(v.immatriculation, v.plate_number, 'N/A') as plate,
               v.categorie, v.conformite_statut
        FROM vehicles v
        WHERE v.tenant_id = :tid AND COALESCE(v.statut, 'ACTIF') = 'ACTIF'
    """
    vparams: dict = {"tid": tid}
    if agency_id:
        vq += " AND v.agency_id = :agency_id"
        vparams["agency_id"] = agency_id
    vq += " ORDER BY v.immatriculation, v.plate_number"

    vehicles_rows = (await db.execute(text(vq), vparams)).fetchall()

    missions = (await db.execute(text("""
        SELECT j.id as job_id, j.numero, j.status, j.type_mission, j.is_subcontracted,
               j.vehicle_id, j.date_chargement_prevue, j.date_livraison_prevue,
               c.raison_sociale as client_name
        FROM jobs j
        LEFT JOIN customers c ON c.id = j.customer_id
        WHERE j.tenant_id = :tid
          AND j.vehicle_id IS NOT NULL
          AND j.date_chargement_prevue < :end_date
          AND j.date_livraison_prevue > :start_date
          AND j.status NOT IN ('ANNULEE', 'BROUILLON')
    """), {"tid": tid, "start_date": start, "end_date": end})).fetchall()

    vehicle_missions: dict[str, list] = {}
    for m in missions:
        vid = str(m.vehicle_id)
        if vid not in vehicle_missions:
            vehicle_missions[vid] = []
        vehicle_missions[vid].append(TimeBlock(
            job_id=str(m.job_id), numero=m.numero,
            client_name=m.client_name,
            statut=m.status or "BROUILLON",
            start=str(m.date_chargement_prevue) if m.date_chargement_prevue else "",
            end=str(m.date_livraison_prevue) if m.date_livraison_prevue else "",
            type_mission=m.type_mission,
            is_subcontracted=bool(m.is_subcontracted),
        ))

    return [VehiclePlanning(
        vehicle_id=str(v.id),
        plate=v.plate,
        categorie=v.categorie,
        conformite_statut=v.conformite_statut,
        blocks=vehicle_missions.get(str(v.id), []),
    ) for v in vehicles_rows]


@router.post("/check-availability", response_model=AvailabilityResult)
async def check_availability(
    body: AvailabilityCheck,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    conflicts: list[TimeBlock] = []

    # Convert string dates to date objects for asyncpg compatibility
    start_date = date.fromisoformat(body.start) if isinstance(body.start, str) else body.start
    end_date = date.fromisoformat(body.end) if isinstance(body.end, str) else body.end

    if body.driver_id:
        rows = (await db.execute(text("""
            SELECT j.id, j.numero, j.status, j.type_mission,
                   j.date_chargement_prevue, j.date_livraison_prevue,
                   c.raison_sociale as client_name
            FROM jobs j
            LEFT JOIN customers c ON c.id = j.customer_id
            WHERE j.tenant_id = :tid AND j.driver_id = :did
              AND j.status NOT IN ('ANNULEE', 'BROUILLON', 'CLOTUREE')
              AND j.date_chargement_prevue < :end_date
              AND j.date_livraison_prevue > :start_date
        """), {"tid": tid, "did": body.driver_id, "start_date": start_date, "end_date": end_date})).fetchall()
        for r in rows:
            conflicts.append(TimeBlock(
                job_id=str(r.id), numero=r.numero, client_name=r.client_name,
                statut=r.status, start=str(r.date_chargement_prevue), end=str(r.date_livraison_prevue),
                type_mission=r.type_mission,
            ))

    if body.vehicle_id:
        rows = (await db.execute(text("""
            SELECT j.id, j.numero, j.status, j.type_mission,
                   j.date_chargement_prevue, j.date_livraison_prevue,
                   c.raison_sociale as client_name
            FROM jobs j
            LEFT JOIN customers c ON c.id = j.customer_id
            WHERE j.tenant_id = :tid AND j.vehicle_id = :vid
              AND j.status NOT IN ('ANNULEE', 'BROUILLON', 'CLOTUREE')
              AND j.date_chargement_prevue < :end_date
              AND j.date_livraison_prevue > :start_date
        """), {"tid": tid, "vid": body.vehicle_id, "start_date": start_date, "end_date": end_date})).fetchall()
        for r in rows:
            conflicts.append(TimeBlock(
                job_id=str(r.id), numero=r.numero, client_name=r.client_name,
                statut=r.status, start=str(r.date_chargement_prevue), end=str(r.date_livraison_prevue),
                type_mission=r.type_mission,
            ))

    return AvailabilityResult(available=len(conflicts) == 0, conflicts=conflicts)


@router.post("/validate-assignment", response_model=ValidationResult)
async def validate_assignment(
    body: ValidateAssignmentRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    checks: list[ValidationCheck] = []

    # Load job
    job = (await db.execute(text(
        "SELECT * FROM jobs WHERE id = :id AND tenant_id = :tid"
    ), {"id": body.job_id, "tid": tid})).first()
    if not job:
        raise HTTPException(404, "Mission non trouvee")

    # Load goods for weight check
    goods = (await db.execute(text(
        "SELECT SUM(poids_brut_kg) as total_weight FROM mission_goods WHERE mission_id = :jid"
    ), {"jid": body.job_id})).first()
    total_weight = float(goods.total_weight) if goods and goods.total_weight else 0

    if body.driver_id:
        driver = (await db.execute(text(
            "SELECT * FROM drivers WHERE id = :id AND tenant_id = :tid"
        ), {"id": body.driver_id, "tid": tid})).first()

        if driver:
            # Check driver availability
            avail = await check_availability(
                AvailabilityCheck(
                    driver_id=body.driver_id,
                    start=str(job.date_chargement_prevue) if job.date_chargement_prevue else str(date.today()),
                    end=str(job.date_livraison_prevue) if job.date_livraison_prevue else str(date.today()),
                ),
                tenant=tenant, user=user, db=db,
            )
            checks.append(ValidationCheck(
                check="Disponibilite conducteur",
                passed=avail.available,
                message="Disponible" if avail.available else f"{len(avail.conflicts)} conflit(s) detecte(s)",
            ))

            # Check conformity
            conf = driver.conformite_statut or "OK"
            checks.append(ValidationCheck(
                check="Conformite conducteur",
                passed=conf != "BLOQUANT",
                message=f"Statut: {conf}",
            ))

            # Check license vs vehicle category
            if body.vehicle_id:
                vehicle = (await db.execute(text(
                    "SELECT * FROM vehicles WHERE id = :id AND tenant_id = :tid"
                ), {"id": body.vehicle_id, "tid": tid})).first()
                if vehicle:
                    cat = vehicle.categorie or ""
                    perms = driver.categorie_permis or []
                    if isinstance(perms, str):
                        perms = [perms]
                    needs_ce = cat in ("TRACTEUR", "SEMI_REMORQUE", "SPL")
                    needs_c = cat in ("PL_3_5T_19T", "PL_PLUS_19T")
                    license_ok = True
                    if needs_ce and "CE" not in perms:
                        license_ok = False
                    elif needs_c and "C" not in perms and "CE" not in perms:
                        license_ok = False
                    checks.append(ValidationCheck(
                        check="Permis vs categorie vehicule",
                        passed=license_ok,
                        message="Compatible" if license_ok else f"Permis {perms} insuffisant pour {cat}",
                    ))

    if body.vehicle_id:
        vehicle = (await db.execute(text(
            "SELECT * FROM vehicles WHERE id = :id AND tenant_id = :tid"
        ), {"id": body.vehicle_id, "tid": tid})).first()

        if vehicle:
            # Check vehicle availability
            avail = await check_availability(
                AvailabilityCheck(
                    vehicle_id=body.vehicle_id,
                    start=str(job.date_chargement_prevue) if job.date_chargement_prevue else str(date.today()),
                    end=str(job.date_livraison_prevue) if job.date_livraison_prevue else str(date.today()),
                ),
                tenant=tenant, user=user, db=db,
            )
            checks.append(ValidationCheck(
                check="Disponibilite vehicule",
                passed=avail.available,
                message="Disponible" if avail.available else f"{len(avail.conflicts)} conflit(s)",
            ))

            # Check conformity
            conf = vehicle.conformite_statut or "OK"
            checks.append(ValidationCheck(
                check="Conformite vehicule",
                passed=conf != "BLOQUANT",
                message=f"Statut: {conf}",
            ))

            # Check payload capacity
            capacity = float(vehicle.charge_utile_kg) if vehicle.charge_utile_kg else None
            if capacity and total_weight > 0:
                weight_ok = total_weight <= capacity
                checks.append(ValidationCheck(
                    check="Capacite de charge",
                    passed=weight_ok,
                    message=f"{total_weight:.0f} kg / {capacity:.0f} kg" if weight_ok
                            else f"Surcharge: {total_weight:.0f} kg > {capacity:.0f} kg",
                ))

    can_assign = all(c.passed for c in checks)
    return ValidationResult(checks=checks, can_assign=can_assign)
