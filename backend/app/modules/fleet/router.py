"""Router for Module H — Fleet & Maintenance (19 endpoints)."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.modules.fleet.schemas import (
    CATEGORIES_COUT,
    RESPONSABILITES,
    STATUTS_MAINTENANCE,
    STATUTS_SINISTRE,
    TYPES_MAINTENANCE,
    TYPES_SINISTRE,
    ClaimCreate,
    ClaimOut,
    ClaimUpdate,
    CostCreate,
    CostOut,
    CostSummary,
    CostUpdate,
    FleetDashboardStats,
    MaintenanceCreate,
    MaintenanceOut,
    MaintenanceUpdate,
    ScheduleCreate,
    ScheduleOut,
    ScheduleUpdate,
    StatusChange,
)

router = APIRouter(prefix="/v1/fleet", tags=["fleet"])


def _schedule_from_row(r) -> ScheduleOut:
    return ScheduleOut(
        id=str(r.id), vehicle_id=str(r.vehicle_id),
        type_maintenance=r.type_maintenance, libelle=r.libelle,
        description=r.description,
        frequence_jours=r.frequence_jours, frequence_km=r.frequence_km,
        derniere_date_realisation=r.derniere_date_realisation,
        dernier_km_realisation=r.dernier_km_realisation,
        prochaine_date_prevue=r.prochaine_date_prevue,
        prochain_km_prevu=r.prochain_km_prevu,
        prestataire_par_defaut=r.prestataire_par_defaut,
        cout_estime=r.cout_estime,
        alerte_jours_avant=r.alerte_jours_avant,
        alerte_km_avant=r.alerte_km_avant,
        is_active=r.is_active, notes=r.notes,
        created_at=r.created_at, updated_at=r.updated_at,
    )


def _maint_from_row(r) -> MaintenanceOut:
    return MaintenanceOut(
        id=str(r.id), vehicle_id=str(r.vehicle_id),
        schedule_id=str(r.schedule_id) if r.schedule_id else None,
        type_maintenance=r.type_maintenance, libelle=r.libelle,
        description=r.description,
        date_debut=r.date_debut, date_fin=r.date_fin,
        km_vehicule=r.km_vehicule,
        prestataire=r.prestataire, lieu=r.lieu,
        cout_pieces_ht=r.cout_pieces_ht, cout_main_oeuvre_ht=r.cout_main_oeuvre_ht,
        cout_total_ht=r.cout_total_ht, cout_tva=r.cout_tva,
        cout_total_ttc=r.cout_total_ttc,
        facture_ref=r.facture_ref,
        is_planifie=r.is_planifie, statut=r.statut,
        resultat=r.resultat, notes=r.notes,
        created_by=str(r.created_by) if r.created_by else None,
        created_at=r.created_at, updated_at=r.updated_at,
    )


def _cost_from_row(r) -> CostOut:
    return CostOut(
        id=str(r.id), vehicle_id=str(r.vehicle_id),
        maintenance_record_id=str(r.maintenance_record_id) if r.maintenance_record_id else None,
        categorie=r.categorie, sous_categorie=r.sous_categorie,
        libelle=r.libelle, date_cout=r.date_cout,
        montant_ht=r.montant_ht, montant_tva=r.montant_tva,
        montant_ttc=r.montant_ttc,
        km_vehicule=r.km_vehicule,
        quantite=r.quantite, unite=r.unite,
        fournisseur=r.fournisseur, facture_ref=r.facture_ref,
        notes=r.notes,
        created_by=str(r.created_by) if r.created_by else None,
        created_at=r.created_at, updated_at=r.updated_at,
    )


def _claim_from_row(r) -> ClaimOut:
    return ClaimOut(
        id=str(r.id), vehicle_id=str(r.vehicle_id),
        numero=r.numero,
        date_sinistre=r.date_sinistre, heure_sinistre=r.heure_sinistre,
        lieu=r.lieu, type_sinistre=r.type_sinistre,
        description=r.description,
        driver_id=str(r.driver_id) if r.driver_id else None,
        tiers_implique=r.tiers_implique, tiers_nom=r.tiers_nom,
        tiers_immatriculation=r.tiers_immatriculation,
        tiers_assurance=r.tiers_assurance, tiers_police=r.tiers_police,
        constat_s3_key=r.constat_s3_key,
        assurance_ref=r.assurance_ref,
        assurance_declaration_date=r.assurance_declaration_date,
        responsabilite=r.responsabilite,
        cout_reparation_ht=r.cout_reparation_ht,
        franchise=r.franchise, indemnisation_recue=r.indemnisation_recue,
        cout_immobilisation_estime=r.cout_immobilisation_estime,
        jours_immobilisation=r.jours_immobilisation,
        statut=r.statut, date_cloture=r.date_cloture,
        notes=r.notes,
        created_by=str(r.created_by) if r.created_by else None,
        created_at=r.created_at, updated_at=r.updated_at,
    )


async def _check_vehicle(db: AsyncSession, vid: str, tid: str) -> None:
    row = (await db.execute(
        text("SELECT id FROM vehicles WHERE id = :id AND tenant_id = :tid"),
        {"id": vid, "tid": tid},
    )).first()
    if not row:
        raise HTTPException(404, "Vehicle not found")


# =====================================================================
# Maintenance Schedules
# =====================================================================

@router.get("/vehicles/{vid}/schedules", response_model=list[ScheduleOut])
async def list_schedules(
    vid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True),
):
    await _check_vehicle(db, vid, str(tenant.tenant_id))
    q = "SELECT * FROM maintenance_schedules WHERE tenant_id = :tid AND vehicle_id = :vid"
    params: dict = {"tid": str(tenant.tenant_id), "vid": vid}
    if active_only:
        q += " AND is_active = true"
    q += " ORDER BY prochaine_date_prevue ASC NULLS LAST"
    rows = await db.execute(text(q), params)
    return [_schedule_from_row(r) for r in rows.fetchall()]


@router.post("/vehicles/{vid}/schedules", response_model=ScheduleOut, status_code=201)
async def create_schedule(
    vid: str,
    body: ScheduleCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    await _check_vehicle(db, vid, tid)
    if body.type_maintenance not in TYPES_MAINTENANCE:
        raise HTTPException(422, f"Type invalide. Valeurs: {', '.join(sorted(TYPES_MAINTENANCE))}")
    sid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO maintenance_schedules (
            id, tenant_id, vehicle_id, type_maintenance, libelle, description,
            frequence_jours, frequence_km, derniere_date_realisation, dernier_km_realisation,
            prochaine_date_prevue, prochain_km_prevu,
            prestataire_par_defaut, cout_estime, alerte_jours_avant, alerte_km_avant, notes
        ) VALUES (
            :id, :tid, :vid, :tm, :lib, :desc,
            :fj, :fkm, :ddr, :dkr,
            :pdp, :pkp,
            :prest, :cout, :aja, :aka, :notes
        )
    """), {
        "id": str(sid), "tid": tid, "vid": vid,
        "tm": body.type_maintenance, "lib": body.libelle, "desc": body.description,
        "fj": body.frequence_jours, "fkm": body.frequence_km,
        "ddr": body.derniere_date_realisation, "dkr": body.dernier_km_realisation,
        "pdp": body.prochaine_date_prevue, "pkp": body.prochain_km_prevu,
        "prest": body.prestataire_par_defaut, "cout": body.cout_estime,
        "aja": body.alerte_jours_avant, "aka": body.alerte_km_avant,
        "notes": body.notes,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM maintenance_schedules WHERE id = :id"), {"id": str(sid)})).first()
    return _schedule_from_row(row)


@router.put("/vehicles/schedules/{sid}", response_model=ScheduleOut)
async def update_schedule(
    sid: str,
    body: ScheduleUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    existing = (await db.execute(
        text("SELECT id FROM maintenance_schedules WHERE id = :id AND tenant_id = :tid"),
        {"id": sid, "tid": tid},
    )).first()
    if not existing:
        raise HTTPException(404, "Schedule not found")
    if body.type_maintenance and body.type_maintenance not in TYPES_MAINTENANCE:
        raise HTTPException(422, f"Type invalide. Valeurs: {', '.join(sorted(TYPES_MAINTENANCE))}")
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(422, "No fields to update")
    sets = ", ".join(f"{k} = :{k}" for k in data)
    data["id"] = sid
    data["tid"] = tid
    await db.execute(text(f"UPDATE maintenance_schedules SET {sets}, updated_at = now() WHERE id = :id AND tenant_id = :tid"), data)
    await db.commit()
    row = (await db.execute(text("SELECT * FROM maintenance_schedules WHERE id = :id"), {"id": sid})).first()
    return _schedule_from_row(row)


@router.delete("/vehicles/schedules/{sid}", status_code=204)
async def deactivate_schedule(
    sid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    result = await db.execute(text("""
        UPDATE maintenance_schedules SET is_active = false, updated_at = now()
        WHERE id = :id AND tenant_id = :tid RETURNING id
    """), {"id": sid, "tid": tid})
    if not result.first():
        raise HTTPException(404, "Schedule not found")
    await db.commit()


# =====================================================================
# Maintenance Records
# =====================================================================

@router.get("/vehicles/{vid}/maintenance", response_model=list[MaintenanceOut])
async def list_maintenance(
    vid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    await _check_vehicle(db, vid, str(tenant.tenant_id))
    q = "SELECT * FROM maintenance_records WHERE tenant_id = :tid AND vehicle_id = :vid"
    params: dict = {"tid": str(tenant.tenant_id), "vid": vid}
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    q += " ORDER BY date_debut DESC LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_maint_from_row(r) for r in rows.fetchall()]


@router.post("/vehicles/{vid}/maintenance", response_model=MaintenanceOut, status_code=201)
async def create_maintenance(
    vid: str,
    body: MaintenanceCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    await _check_vehicle(db, vid, tid)
    if body.type_maintenance not in TYPES_MAINTENANCE:
        raise HTTPException(422, f"Type invalide. Valeurs: {', '.join(sorted(TYPES_MAINTENANCE))}")
    if body.statut not in STATUTS_MAINTENANCE:
        raise HTTPException(422, f"Statut invalide. Valeurs: {', '.join(sorted(STATUTS_MAINTENANCE))}")
    mid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO maintenance_records (
            id, tenant_id, vehicle_id, schedule_id,
            type_maintenance, libelle, description,
            date_debut, date_fin, km_vehicule,
            prestataire, lieu,
            cout_pieces_ht, cout_main_oeuvre_ht, cout_total_ht, cout_tva, cout_total_ttc,
            facture_ref, is_planifie, statut, resultat, notes, created_by
        ) VALUES (
            :id, :tid, :vid, :sid,
            :tm, :lib, :desc,
            :dd, :df, :km,
            :prest, :lieu,
            :cph, :cmh, :cth, :ctva, :cttc,
            :fref, :plan, :statut, :res, :notes, :uid
        )
    """), {
        "id": str(mid), "tid": tid, "vid": vid,
        "sid": body.schedule_id,
        "tm": body.type_maintenance, "lib": body.libelle, "desc": body.description,
        "dd": body.date_debut, "df": body.date_fin, "km": body.km_vehicule,
        "prest": body.prestataire, "lieu": body.lieu,
        "cph": body.cout_pieces_ht, "cmh": body.cout_main_oeuvre_ht,
        "cth": body.cout_total_ht, "ctva": body.cout_tva, "cttc": body.cout_total_ttc,
        "fref": body.facture_ref,
        "plan": body.is_planifie, "statut": body.statut,
        "res": body.resultat, "notes": body.notes,
        "uid": user["id"],
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM maintenance_records WHERE id = :id"), {"id": str(mid)})).first()
    return _maint_from_row(row)


@router.put("/maintenance/{mid}", response_model=MaintenanceOut)
async def update_maintenance(
    mid: str,
    body: MaintenanceUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    existing = (await db.execute(
        text("SELECT id FROM maintenance_records WHERE id = :id AND tenant_id = :tid"),
        {"id": mid, "tid": tid},
    )).first()
    if not existing:
        raise HTTPException(404, "Maintenance record not found")
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(422, "No fields to update")
    if "type_maintenance" in data and data["type_maintenance"] not in TYPES_MAINTENANCE:
        raise HTTPException(422, f"Type invalide. Valeurs: {', '.join(sorted(TYPES_MAINTENANCE))}")
    sets = ", ".join(f"{k} = :{k}" for k in data)
    data["id"] = mid
    data["tid"] = tid
    await db.execute(text(f"UPDATE maintenance_records SET {sets}, updated_at = now() WHERE id = :id AND tenant_id = :tid"), data)
    await db.commit()
    row = (await db.execute(text("SELECT * FROM maintenance_records WHERE id = :id"), {"id": mid})).first()
    return _maint_from_row(row)


@router.patch("/maintenance/{mid}/status", response_model=MaintenanceOut)
async def change_maintenance_status(
    mid: str,
    body: StatusChange,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    if body.statut not in STATUTS_MAINTENANCE:
        raise HTTPException(422, f"Statut invalide. Valeurs: {', '.join(sorted(STATUTS_MAINTENANCE))}")
    record = (await db.execute(
        text("SELECT * FROM maintenance_records WHERE id = :id AND tenant_id = :tid"),
        {"id": mid, "tid": tid},
    )).first()
    if not record:
        raise HTTPException(404, "Maintenance record not found")

    await db.execute(text("""
        UPDATE maintenance_records SET statut = :statut, updated_at = now()
        WHERE id = :id AND tenant_id = :tid
    """), {"statut": body.statut, "id": mid, "tid": tid})

    # Business logic: when TERMINE, update schedule + auto-create cost
    if body.statut == "TERMINE" and record.schedule_id:
        update_fields = {"sid": str(record.schedule_id), "tid": tid}
        set_parts = ["derniere_date_realisation = :ddr", "updated_at = now()"]
        update_fields["ddr"] = record.date_fin or record.date_debut
        if record.km_vehicule:
            set_parts.append("dernier_km_realisation = :dkr")
            update_fields["dkr"] = record.km_vehicule
        # Recalculate next dates
        sched = (await db.execute(
            text("SELECT * FROM maintenance_schedules WHERE id = :sid"),
            {"sid": str(record.schedule_id)},
        )).first()
        if sched:
            base_date = record.date_fin or record.date_debut
            if sched.frequence_jours and base_date:
                set_parts.append("prochaine_date_prevue = :pdp")
                update_fields["pdp"] = base_date + timedelta(days=sched.frequence_jours)
            if sched.frequence_km and record.km_vehicule:
                set_parts.append("prochain_km_prevu = :pkp")
                update_fields["pkp"] = record.km_vehicule + sched.frequence_km

        await db.execute(text(
            f"UPDATE maintenance_schedules SET {', '.join(set_parts)} WHERE id = :sid AND tenant_id = :tid"
        ), update_fields)

    # Auto-create cost entry when maintenance is completed with costs
    if body.statut == "TERMINE" and record.cout_total_ht:
        cost_id = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO vehicle_costs (
                id, tenant_id, vehicle_id, maintenance_record_id,
                categorie, libelle, date_cout, montant_ht, montant_tva, montant_ttc,
                km_vehicule, fournisseur, facture_ref, created_by
            ) VALUES (
                :id, :tid, :vid, :mid,
                :cat, :lib, :dc, :mht, :mtva, :mttc,
                :km, :fourn, :fref, :uid
            )
        """), {
            "id": str(cost_id), "tid": tid, "vid": str(record.vehicle_id),
            "mid": mid,
            "cat": "ENTRETIEN", "lib": record.libelle,
            "dc": record.date_fin or record.date_debut,
            "mht": record.cout_total_ht, "mtva": record.cout_tva,
            "mttc": record.cout_total_ttc,
            "km": record.km_vehicule,
            "fourn": record.prestataire, "fref": record.facture_ref,
            "uid": user["id"],
        })

    await db.commit()
    row = (await db.execute(text("SELECT * FROM maintenance_records WHERE id = :id"), {"id": mid})).first()
    return _maint_from_row(row)


@router.get("/maintenance/upcoming", response_model=list[MaintenanceOut])
async def upcoming_maintenance(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    cutoff = date.today() + timedelta(days=days)
    rows = await db.execute(text("""
        SELECT * FROM maintenance_records
        WHERE tenant_id = :tid AND statut = 'PLANIFIE' AND date_debut <= :cutoff
        ORDER BY date_debut ASC
    """), {"tid": str(tenant.tenant_id), "cutoff": cutoff})
    return [_maint_from_row(r) for r in rows.fetchall()]


# =====================================================================
# Vehicle Costs
# =====================================================================

@router.get("/vehicles/{vid}/costs", response_model=list[CostOut])
async def list_costs(
    vid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    categorie: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    await _check_vehicle(db, vid, str(tenant.tenant_id))
    q = "SELECT * FROM vehicle_costs WHERE tenant_id = :tid AND vehicle_id = :vid"
    params: dict = {"tid": str(tenant.tenant_id), "vid": vid}
    if categorie:
        q += " AND categorie = :cat"
        params["cat"] = categorie
    if date_from:
        q += " AND date_cout >= :df"
        params["df"] = date_from
    if date_to:
        q += " AND date_cout <= :dt"
        params["dt"] = date_to
    q += " ORDER BY date_cout DESC LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_cost_from_row(r) for r in rows.fetchall()]


@router.post("/vehicles/{vid}/costs", response_model=CostOut, status_code=201)
async def create_cost(
    vid: str,
    body: CostCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    await _check_vehicle(db, vid, tid)
    if body.categorie not in CATEGORIES_COUT:
        raise HTTPException(422, f"Categorie invalide. Valeurs: {', '.join(sorted(CATEGORIES_COUT))}")
    cid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO vehicle_costs (
            id, tenant_id, vehicle_id,
            categorie, sous_categorie, libelle, date_cout,
            montant_ht, montant_tva, montant_ttc,
            km_vehicule, quantite, unite, fournisseur, facture_ref,
            notes, created_by
        ) VALUES (
            :id, :tid, :vid,
            :cat, :scat, :lib, :dc,
            :mht, :mtva, :mttc,
            :km, :qty, :unite, :fourn, :fref,
            :notes, :uid
        )
    """), {
        "id": str(cid), "tid": tid, "vid": vid,
        "cat": body.categorie, "scat": body.sous_categorie,
        "lib": body.libelle, "dc": body.date_cout,
        "mht": body.montant_ht, "mtva": body.montant_tva, "mttc": body.montant_ttc,
        "km": body.km_vehicule, "qty": body.quantite,
        "unite": body.unite, "fourn": body.fournisseur, "fref": body.facture_ref,
        "notes": body.notes, "uid": user["id"],
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vehicle_costs WHERE id = :id"), {"id": str(cid)})).first()
    return _cost_from_row(row)


@router.put("/costs/{cid}", response_model=CostOut)
async def update_cost(
    cid: str,
    body: CostUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    existing = (await db.execute(
        text("SELECT id FROM vehicle_costs WHERE id = :id AND tenant_id = :tid"),
        {"id": cid, "tid": tid},
    )).first()
    if not existing:
        raise HTTPException(404, "Cost not found")
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(422, "No fields to update")
    if "categorie" in data and data["categorie"] not in CATEGORIES_COUT:
        raise HTTPException(422, f"Categorie invalide. Valeurs: {', '.join(sorted(CATEGORIES_COUT))}")
    sets = ", ".join(f"{k} = :{k}" for k in data)
    data["id"] = cid
    data["tid"] = tid
    await db.execute(text(f"UPDATE vehicle_costs SET {sets}, updated_at = now() WHERE id = :id AND tenant_id = :tid"), data)
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vehicle_costs WHERE id = :id"), {"id": cid})).first()
    return _cost_from_row(row)


@router.delete("/costs/{cid}", status_code=204)
async def delete_cost(
    cid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    result = await db.execute(text(
        "DELETE FROM vehicle_costs WHERE id = :id AND tenant_id = :tid RETURNING id"
    ), {"id": cid, "tid": tid})
    if not result.first():
        raise HTTPException(404, "Cost not found")
    await db.commit()


@router.get("/vehicles/{vid}/costs/summary", response_model=list[CostSummary])
async def cost_summary(
    vid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
):
    await _check_vehicle(db, vid, str(tenant.tenant_id))
    q = """
        SELECT categorie, COALESCE(SUM(montant_ht), 0) AS total_ht,
               COALESCE(SUM(montant_ttc), 0) AS total_ttc, COUNT(*) AS count
        FROM vehicle_costs WHERE tenant_id = :tid AND vehicle_id = :vid
    """
    params: dict = {"tid": str(tenant.tenant_id), "vid": vid}
    if date_from:
        q += " AND date_cout >= :df"
        params["df"] = date_from
    if date_to:
        q += " AND date_cout <= :dt"
        params["dt"] = date_to
    q += " GROUP BY categorie ORDER BY total_ht DESC"
    rows = await db.execute(text(q), params)
    return [CostSummary(categorie=r.categorie, total_ht=r.total_ht,
                        total_ttc=r.total_ttc, count=r.count)
            for r in rows.fetchall()]


# =====================================================================
# Vehicle Claims (Sinistres)
# =====================================================================

@router.get("/vehicles/{vid}/claims", response_model=list[ClaimOut])
async def list_claims(
    vid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    await _check_vehicle(db, vid, str(tenant.tenant_id))
    q = "SELECT * FROM vehicle_claims WHERE tenant_id = :tid AND vehicle_id = :vid"
    params: dict = {"tid": str(tenant.tenant_id), "vid": vid}
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    q += " ORDER BY date_sinistre DESC LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_claim_from_row(r) for r in rows.fetchall()]


@router.post("/vehicles/{vid}/claims", response_model=ClaimOut, status_code=201)
async def create_claim(
    vid: str,
    body: ClaimCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    await _check_vehicle(db, vid, tid)
    if body.type_sinistre not in TYPES_SINISTRE:
        raise HTTPException(422, f"Type invalide. Valeurs: {', '.join(sorted(TYPES_SINISTRE))}")
    if body.responsabilite not in RESPONSABILITES:
        raise HTTPException(422, f"Responsabilite invalide. Valeurs: {', '.join(sorted(RESPONSABILITES))}")

    # Generate unique numero per tenant
    cnt = (await db.execute(text(
        "SELECT COUNT(*) FROM vehicle_claims WHERE tenant_id = :tid"
    ), {"tid": tid})).scalar() or 0
    numero = f"SIN-{cnt + 1:04d}"

    cid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO vehicle_claims (
            id, tenant_id, vehicle_id, numero,
            date_sinistre, heure_sinistre, lieu, type_sinistre, description,
            driver_id, tiers_implique, tiers_nom, tiers_immatriculation,
            tiers_assurance, tiers_police,
            assurance_ref, assurance_declaration_date,
            responsabilite, cout_reparation_ht, franchise,
            cout_immobilisation_estime, jours_immobilisation,
            notes, created_by
        ) VALUES (
            :id, :tid, :vid, :num,
            :ds, :hs, :lieu, :ts, :desc,
            :did, :ti, :tn, :timmat,
            :tass, :tpol,
            :aref, :adecl,
            :resp, :crh, :franch,
            :cie, :ji,
            :notes, :uid
        )
    """), {
        "id": str(cid), "tid": tid, "vid": vid, "num": numero,
        "ds": body.date_sinistre, "hs": body.heure_sinistre,
        "lieu": body.lieu, "ts": body.type_sinistre, "desc": body.description,
        "did": body.driver_id, "ti": body.tiers_implique,
        "tn": body.tiers_nom, "timmat": body.tiers_immatriculation,
        "tass": body.tiers_assurance, "tpol": body.tiers_police,
        "aref": body.assurance_ref, "adecl": body.assurance_declaration_date,
        "resp": body.responsabilite, "crh": body.cout_reparation_ht,
        "franch": body.franchise,
        "cie": body.cout_immobilisation_estime, "ji": body.jours_immobilisation,
        "notes": body.notes, "uid": user["id"],
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vehicle_claims WHERE id = :id"), {"id": str(cid)})).first()
    return _claim_from_row(row)


@router.put("/claims/{cid}", response_model=ClaimOut)
async def update_claim(
    cid: str,
    body: ClaimUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    existing = (await db.execute(
        text("SELECT id FROM vehicle_claims WHERE id = :id AND tenant_id = :tid"),
        {"id": cid, "tid": tid},
    )).first()
    if not existing:
        raise HTTPException(404, "Claim not found")
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(422, "No fields to update")
    if "type_sinistre" in data and data["type_sinistre"] not in TYPES_SINISTRE:
        raise HTTPException(422, f"Type invalide.")
    if "responsabilite" in data and data["responsabilite"] not in RESPONSABILITES:
        raise HTTPException(422, f"Responsabilite invalide.")
    sets = ", ".join(f"{k} = :{k}" for k in data)
    data["id"] = cid
    data["tid"] = tid
    await db.execute(text(f"UPDATE vehicle_claims SET {sets}, updated_at = now() WHERE id = :id AND tenant_id = :tid"), data)
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vehicle_claims WHERE id = :id"), {"id": cid})).first()
    return _claim_from_row(row)


@router.patch("/claims/{cid}/status", response_model=ClaimOut)
async def change_claim_status(
    cid: str,
    body: StatusChange,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    if body.statut not in STATUTS_SINISTRE:
        raise HTTPException(422, f"Statut invalide. Valeurs: {', '.join(sorted(STATUTS_SINISTRE))}")
    result = await db.execute(text("""
        UPDATE vehicle_claims SET statut = :statut, updated_at = now(),
            date_cloture = CASE WHEN :statut IN ('CLOS', 'REMBOURSE') THEN CURRENT_DATE ELSE date_cloture END
        WHERE id = :id AND tenant_id = :tid RETURNING id
    """), {"statut": body.statut, "id": cid, "tid": tid})
    if not result.first():
        raise HTTPException(404, "Claim not found")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vehicle_claims WHERE id = :id"), {"id": cid})).first()
    return _claim_from_row(row)


# =====================================================================
# All Claims (global list — avoids N+1 on frontend)
# =====================================================================

@router.get("/claims", response_model=list[ClaimOut])
async def list_all_claims(
    statut: str | None = Query(None),
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    tid = str(tenant.tenant_id)
    q = "SELECT * FROM vehicle_claims WHERE tenant_id = :tid"
    params: dict = {"tid": tid}
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    allowed_sorts = {"date_sinistre", "cout_reparation_ht", "created_at"}
    sort_col = sort_by if sort_by in allowed_sorts else "date_sinistre"
    q += f" ORDER BY {sort_col} {order} LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = (await db.execute(text(q), params)).fetchall()
    return [_claim_from_row(r) for r in rows]


# =====================================================================
# Fleet Dashboard
# =====================================================================

@router.get("/dashboard", response_model=FleetDashboardStats)
async def fleet_dashboard(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)

    # Vehicle counts
    veh = (await db.execute(text("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE statut = 'ACTIF') AS actifs,
            COUNT(*) FILTER (WHERE statut = 'EN_MAINTENANCE') AS en_maintenance,
            COUNT(*) FILTER (WHERE statut = 'IMMOBILISE') AS immobilises
        FROM vehicles WHERE tenant_id = :tid
    """), {"tid": tid})).first()

    total = veh.total if veh else 0
    actifs = veh.actifs if veh else 0
    en_maint = veh.en_maintenance if veh else 0
    immob = veh.immobilises if veh else 0
    dispo = (actifs / total * 100) if total > 0 else 0

    # Upcoming maintenance (next 30 days)
    cutoff = date.today() + timedelta(days=30)
    upcoming = (await db.execute(text("""
        SELECT COUNT(*) FROM maintenance_records
        WHERE tenant_id = :tid AND statut = 'PLANIFIE' AND date_debut <= :cutoff
    """), {"tid": tid, "cutoff": cutoff})).scalar() or 0

    # Overdue maintenance
    overdue = (await db.execute(text("""
        SELECT COUNT(*) FROM maintenance_records
        WHERE tenant_id = :tid AND statut = 'PLANIFIE' AND date_debut < CURRENT_DATE
    """), {"tid": tid})).scalar() or 0

    # Open claims
    open_claims = (await db.execute(text("""
        SELECT COUNT(*) FROM vehicle_claims
        WHERE tenant_id = :tid AND statut NOT IN ('CLOS', 'REMBOURSE')
    """), {"tid": tid})).scalar() or 0

    # Current month costs
    first_of_month = date.today().replace(day=1)
    month_cost = (await db.execute(text("""
        SELECT COALESCE(SUM(montant_ht), 0) FROM vehicle_costs
        WHERE tenant_id = :tid AND date_cout >= :fom
    """), {"tid": tid, "fom": first_of_month})).scalar() or 0

    return FleetDashboardStats(
        total_vehicles=total,
        vehicles_actifs=actifs,
        vehicles_en_maintenance=en_maint,
        vehicles_immobilises=immob,
        taux_disponibilite=round(dispo, 1),
        maintenances_a_venir_30j=upcoming,
        maintenances_en_retard=overdue,
        sinistres_ouverts=open_claims,
        cout_total_mois_ht=month_cost,
    )


# =====================================================================
# Vehicle Assignments — where is each vehicle and what does it do
# =====================================================================

@router.get("/assignments")
async def list_vehicle_assignments(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """For each active vehicle: current assigned route, driver, site."""
    tid = str(tenant.tenant_id)
    rows = (await db.execute(text("""
        SELECT
            v.id AS vehicle_id,
            COALESCE(v.immatriculation, v.plate_number) AS immatriculation,
            v.marque, v.modele, v.statut AS vehicle_statut,
            v.categorie,
            -- Current route assignment
            r.id AS route_id,
            r.numero AS route_numero,
            r.libelle AS route_libelle,
            r.site AS route_site,
            r.recurrence AS route_recurrence,
            -- Driver from route
            COALESCE(rd.nom, rd.last_name) || ' ' || COALESCE(rd.prenom, rd.first_name) AS route_driver_name,
            rd.telephone_mobile AS route_driver_tel,
            -- Current/latest mission
            latest_job.id AS current_mission_id,
            latest_job.numero AS current_mission_numero,
            latest_job.status AS current_mission_statut,
            latest_job.date_chargement_prevue AS current_mission_date,
            -- Client from route
            c.raison_sociale AS client_name
        FROM vehicles v
        LEFT JOIN LATERAL (
            SELECT * FROM routes rt
            WHERE rt.vehicle_id = v.id AND rt.statut = 'ACTIF'
            ORDER BY rt.created_at DESC LIMIT 1
        ) r ON true
        LEFT JOIN drivers rd ON r.driver_id = rd.id
        LEFT JOIN customers c ON r.client_id = c.id
        LEFT JOIN LATERAL (
            SELECT * FROM jobs j
            WHERE j.vehicle_id = v.id AND j.tenant_id = :tid
              AND j.status NOT IN ('ANNULEE', 'draft')
            ORDER BY j.date_chargement_prevue DESC NULLS LAST LIMIT 1
        ) latest_job ON true
        WHERE v.tenant_id = :tid AND v.statut = 'ACTIF'
        ORDER BY v.immatriculation
    """), {"tid": tid})).fetchall()

    return [
        {
            "vehicle_id": str(r.vehicle_id),
            "immatriculation": r.immatriculation,
            "marque": r.marque,
            "modele": r.modele,
            "categorie": r.categorie,
            "vehicle_statut": r.vehicle_statut,
            "route_id": str(r.route_id) if r.route_id else None,
            "route_numero": r.route_numero,
            "route_libelle": r.route_libelle,
            "route_site": r.route_site,
            "route_recurrence": r.route_recurrence,
            "route_driver_name": r.route_driver_name,
            "route_driver_tel": r.route_driver_tel,
            "client_name": r.client_name,
            "current_mission_id": str(r.current_mission_id) if r.current_mission_id else None,
            "current_mission_numero": r.current_mission_numero,
            "current_mission_statut": r.current_mission_statut,
            "current_mission_date": r.current_mission_date.isoformat() if r.current_mission_date else None,
        }
        for r in rows
    ]
