"""Route Templates (Tournée modèle) — recurring delivery route definitions."""
from __future__ import annotations

import json
import uuid
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.modules.route_templates.schemas import (
    RECURRENCE_RULES,
    TEMPLATE_STATUSES,
    GenerateRunsRequest,
    RouteTemplateCreate,
    RouteTemplateDetail,
    RouteTemplateOut,
    RouteTemplateUpdate,
    StopCreate,
    StopOut,
)

router = APIRouter(prefix="/v1/route-templates", tags=["route-templates"])


# ── Helpers ────────────────────────────────────────────────────────

def _expand_dates(recurrence: str, start: date, end: date) -> list[date]:
    """Expand recurrence pattern into concrete dates."""
    dates = []
    d = start
    while d <= end:
        wd = d.weekday()
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


def _template_from_row(r) -> RouteTemplateOut:
    return RouteTemplateOut(
        id=str(r.id), code=r.code, label=r.label,
        customer_id=str(r.customer_id) if r.customer_id else None,
        customer_name=getattr(r, "customer_name", None),
        site=r.site, status=r.status, recurrence_rule=r.recurrence_rule,
        valid_from=r.valid_from, valid_to=r.valid_to,
        default_driver_id=str(r.default_driver_id) if r.default_driver_id else None,
        default_driver_name=getattr(r, "default_driver_name", None),
        default_vehicle_id=str(r.default_vehicle_id) if r.default_vehicle_id else None,
        default_vehicle_plate=getattr(r, "default_vehicle_plate", None),
        default_mission_type=r.default_mission_type,
        default_sale_amount_ht=r.default_sale_amount_ht,
        default_purchase_amount_ht=r.default_purchase_amount_ht,
        is_subcontracted=r.is_subcontracted or False,
        nb_runs=getattr(r, "nb_runs", 0) or 0,
        nb_missions=getattr(r, "nb_missions", 0) or 0,
        created_at=r.created_at.isoformat() if r.created_at else None,
    )


_BASE_SELECT = """
    SELECT rt.*,
           c.raison_sociale AS customer_name,
           COALESCE(d.nom, d.last_name) || ' ' || COALESCE(d.prenom, d.first_name) AS default_driver_name,
           COALESCE(v.immatriculation, v.plate_number) AS default_vehicle_plate,
           (SELECT COUNT(*) FROM route_runs rr WHERE rr.route_template_id = rt.id) AS nb_runs,
           (SELECT COUNT(*) FROM jobs j WHERE j.source_route_template_id = rt.id) AS nb_missions
    FROM route_templates rt
    LEFT JOIN customers c ON rt.customer_id = c.id
    LEFT JOIN drivers d ON rt.default_driver_id = d.id
    LEFT JOIN vehicles v ON rt.default_vehicle_id = v.id
"""


# ── CRUD ───────────────────────────────────────────────────────────

@router.get("", response_model=list[RouteTemplateOut])
async def list_templates(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
    customer_id: str | None = Query(None),
    search: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    q = _BASE_SELECT + " WHERE rt.tenant_id = :tid"
    params: dict[str, Any] = {"tid": str(tenant.tenant_id)}
    if status:
        q += " AND rt.status = :status"
        params["status"] = status
    if customer_id:
        q += " AND rt.customer_id = :cid"
        params["cid"] = customer_id
    if search:
        q += " AND (rt.code ILIKE :s OR rt.label ILIKE :s OR rt.site ILIKE :s)"
        params["s"] = f"%{search}%"
    allowed = {"code": "rt.code", "label": "rt.label", "created_at": "rt.created_at", "status": "rt.status"}
    sort_col = allowed.get(sort_by, "rt.created_at") if sort_by else "rt.created_at"
    q += f" ORDER BY {sort_col} {order} LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = (await db.execute(text(q), params)).fetchall()
    return [_template_from_row(r) for r in rows]


@router.post("", response_model=RouteTemplateOut, status_code=201)
async def create_template(
    body: RouteTemplateCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    if body.recurrence_rule not in RECURRENCE_RULES:
        raise HTTPException(422, f"Recurrence invalide: {', '.join(sorted(RECURRENCE_RULES))}")
    existing = (await db.execute(text(
        "SELECT id FROM route_templates WHERE tenant_id = :tid AND code = :c"
    ), {"tid": tid, "c": body.code})).first()
    if existing:
        raise HTTPException(409, f"Le code {body.code} existe deja")

    rtid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO route_templates (
            id, tenant_id, agency_id, code, label, customer_id, site,
            status, recurrence_rule, valid_from, valid_to,
            default_driver_id, default_vehicle_id, is_subcontracted, default_subcontractor_id,
            default_mission_type, default_sale_amount_ht, default_purchase_amount_ht,
            default_loading_address, default_estimated_distance_km, default_constraints_json,
            notes, created_by
        ) VALUES (
            :id, :tid, :aid, :code, :label, :cid, :site,
            'ACTIVE', :rec, :vf, :vt,
            :did, :vid, :sub, :subid,
            :mtype, :sale, :purchase,
            :addr, :dist, CAST(:constraints AS jsonb),
            :notes, :uid
        )
    """), {
        "id": str(rtid), "tid": tid, "aid": body.agency_id,
        "code": body.code, "label": body.label, "cid": body.customer_id, "site": body.site,
        "rec": body.recurrence_rule, "vf": body.valid_from, "vt": body.valid_to,
        "did": body.default_driver_id, "vid": body.default_vehicle_id,
        "sub": body.is_subcontracted, "subid": body.default_subcontractor_id,
        "mtype": body.default_mission_type,
        "sale": body.default_sale_amount_ht, "purchase": body.default_purchase_amount_ht,
        "addr": body.default_loading_address, "dist": body.default_estimated_distance_km,
        "constraints": json.dumps(body.default_constraints_json) if body.default_constraints_json else None,
        "notes": body.notes, "uid": user.get("id"),
    })
    await db.commit()
    row = (await db.execute(text(_BASE_SELECT + " WHERE rt.id = :id"), {"id": str(rtid)})).first()
    return _template_from_row(row)


@router.get("/{template_id}", response_model=RouteTemplateDetail)
async def get_template(
    template_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    r = (await db.execute(text(
        _BASE_SELECT + " WHERE rt.id = :id AND rt.tenant_id = :tid"
    ), {"id": template_id, "tid": tid})).first()
    if not r:
        raise HTTPException(404, "Modele de tournee non trouve")

    stops = (await db.execute(text(
        "SELECT * FROM route_template_stops WHERE route_template_id = :tid ORDER BY sequence"
    ), {"tid": template_id})).fetchall()

    base = _template_from_row(r)
    return RouteTemplateDetail(
        **base.model_dump(),
        default_loading_address=r.default_loading_address,
        default_estimated_distance_km=r.default_estimated_distance_km,
        default_constraints_json=r.default_constraints_json,
        notes=r.notes,
        agency_id=str(r.agency_id) if r.agency_id else None,
        default_subcontractor_id=str(r.default_subcontractor_id) if r.default_subcontractor_id else None,
        stops=[StopOut(
            id=str(s.id), sequence=s.sequence, stop_type=s.stop_type,
            name=s.name, address=s.address, city=s.city, postal_code=s.postal_code,
            contact_name=s.contact_name, contact_phone=s.contact_phone, instructions=s.instructions,
        ) for s in stops],
    )


@router.put("/{template_id}", response_model=RouteTemplateOut)
async def update_template(
    template_id: str,
    body: RouteTemplateUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    existing = (await db.execute(text(
        "SELECT id FROM route_templates WHERE id = :id AND tenant_id = :tid"
    ), {"id": template_id, "tid": tid})).first()
    if not existing:
        raise HTTPException(404, "Modele non trouve")

    await db.execute(text("""
        UPDATE route_templates SET
            label = :label, customer_id = :cid, site = :site,
            recurrence_rule = :rec, valid_from = :vf, valid_to = :vt,
            default_driver_id = :did, default_vehicle_id = :vid,
            is_subcontracted = :sub, default_subcontractor_id = :subid,
            default_mission_type = :mtype,
            default_sale_amount_ht = :sale, default_purchase_amount_ht = :purchase,
            default_loading_address = :addr, default_estimated_distance_km = :dist,
            default_constraints_json = CAST(:constraints AS jsonb),
            notes = :notes, status = COALESCE(:status, status),
            updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": template_id, "tid": tid,
        "label": body.label, "cid": body.customer_id, "site": body.site,
        "rec": body.recurrence_rule, "vf": body.valid_from, "vt": body.valid_to,
        "did": body.default_driver_id, "vid": body.default_vehicle_id,
        "sub": body.is_subcontracted, "subid": body.default_subcontractor_id,
        "mtype": body.default_mission_type,
        "sale": body.default_sale_amount_ht, "purchase": body.default_purchase_amount_ht,
        "addr": body.default_loading_address, "dist": body.default_estimated_distance_km,
        "constraints": json.dumps(body.default_constraints_json) if body.default_constraints_json else None,
        "notes": body.notes, "status": body.status,
    })
    await db.commit()
    row = (await db.execute(text(_BASE_SELECT + " WHERE rt.id = :id"), {"id": template_id})).first()
    return _template_from_row(row)


# ── Status transitions ─────────────────────────────────────────────

@router.patch("/{template_id}/activate")
async def activate_template(template_id: str, tenant: TenantContext = Depends(get_tenant),
                             user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _set_status(template_id, "ACTIVE", tenant, db)
    return {"ok": True, "status": "ACTIVE"}

@router.patch("/{template_id}/suspend")
async def suspend_template(template_id: str, tenant: TenantContext = Depends(get_tenant),
                            user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _set_status(template_id, "SUSPENDED", tenant, db)
    return {"ok": True, "status": "SUSPENDED"}

@router.patch("/{template_id}/archive")
async def archive_template(template_id: str, tenant: TenantContext = Depends(get_tenant),
                            user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _set_status(template_id, "ARCHIVED", tenant, db)
    return {"ok": True, "status": "ARCHIVED"}

async def _set_status(template_id: str, status: str, tenant: TenantContext, db: AsyncSession):
    await db.execute(text(
        "UPDATE route_templates SET status = :s, updated_at = NOW() WHERE id = :id AND tenant_id = :tid"
    ), {"s": status, "id": template_id, "tid": str(tenant.tenant_id)})
    await db.commit()


# ── Stops management ───────────────────────────────────────────────

@router.post("/{template_id}/stops", status_code=201)
async def add_stop(
    template_id: str, body: StopCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO route_template_stops (id, tenant_id, route_template_id, sequence, stop_type,
            name, address, city, postal_code, contact_name, contact_phone, instructions)
        VALUES (:id, :tid, :rtid, :seq, :type, :name, :addr, :city, :cp, :cn, :cp2, :instr)
    """), {
        "id": str(sid), "tid": str(tenant.tenant_id), "rtid": template_id,
        "seq": body.sequence, "type": body.stop_type, "name": body.name,
        "addr": body.address, "city": body.city, "cp": body.postal_code,
        "cn": body.contact_name, "cp2": body.contact_phone, "instr": body.instructions,
    })
    await db.commit()
    return {"id": str(sid)}


@router.delete("/{template_id}/stops/{stop_id}")
async def delete_stop(
    template_id: str, stop_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text(
        "DELETE FROM route_template_stops WHERE id = :sid AND route_template_id = :rtid AND tenant_id = :tid"
    ), {"sid": stop_id, "rtid": template_id, "tid": str(tenant.tenant_id)})
    await db.commit()
    return {"ok": True}


# ── Generation ─────────────────────────────────────────────────────

@router.post("/{template_id}/generate-runs")
async def generate_runs(
    template_id: str,
    body: GenerateRunsRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate route_runs (and optionally missions) from a template for a date range."""
    tid = str(tenant.tenant_id)

    tmpl = (await db.execute(text(
        "SELECT * FROM route_templates WHERE id = :id AND tenant_id = :tid AND status = 'ACTIVE'"
    ), {"id": template_id, "tid": tid})).first()
    if not tmpl:
        raise HTTPException(404, "Modele non trouve ou inactif")

    exec_dates = _expand_dates(tmpl.recurrence_rule, body.start_date, body.end_date)
    if not exec_dates:
        raise HTTPException(422, "Aucune date pour cette periode et cette recurrence")

    driver_id = body.override_driver_id or (str(tmpl.default_driver_id) if tmpl.default_driver_id else None)
    vehicle_id = body.override_vehicle_id or (str(tmpl.default_vehicle_id) if tmpl.default_vehicle_id else None)

    created_runs = []
    for exec_date in exec_dates:
        run_code = f"RUN-{tmpl.code}-{exec_date.isoformat()}"

        # Idempotency: skip if run already exists for this template+date
        existing = (await db.execute(text(
            "SELECT id FROM route_runs WHERE route_template_id = :rtid AND service_date = :d AND tenant_id = :tid"
        ), {"rtid": template_id, "d": exec_date, "tid": tid})).first()
        if existing:
            continue

        run_id = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO route_runs (
                id, tenant_id, route_template_id, code, service_date, status,
                assigned_driver_id, assigned_vehicle_id, notes, created_by
            ) VALUES (
                :id, :tid, :rtid, :code, :sd, 'PLANNED',
                :did, :vid, :notes, :uid
            )
        """), {
            "id": str(run_id), "tid": tid, "rtid": template_id,
            "code": run_code, "sd": exec_date,
            "did": driver_id, "vid": vehicle_id,
            "notes": f"Genere depuis modele {tmpl.code}",
            "uid": user.get("id"),
        })

        mission_id = None
        if body.auto_create_missions:
            mission_id = uuid.uuid4()
            mission_code = f"MIS-{exec_date.year}-{exec_date.month:02d}-{exec_date.day:02d}-{tmpl.code}"

            await db.execute(text("""
                INSERT INTO jobs (
                    id, tenant_id, numero, customer_id, type_mission,
                    date_chargement_prevue, date_livraison_prevue,
                    driver_id, vehicle_id,
                    is_subcontracted, subcontractor_id,
                    montant_vente_ht, montant_achat_ht,
                    notes_exploitation, source_type,
                    source_route_template_id, source_route_run_id,
                    status, created_by
                ) VALUES (
                    :id, :tid, :num, :cid, :type,
                    :date_charge, :date_livre,
                    :did, :vid,
                    :sub, :subid,
                    :sale, :purchase,
                    :notes, 'GENERATED_FROM_TEMPLATE',
                    :rtid, :rrid,
                    'planned', :uid
                )
            """), {
                "id": str(mission_id), "tid": tid, "num": mission_code,
                "cid": str(tmpl.customer_id) if tmpl.customer_id else None,
                "type": tmpl.default_mission_type,
                "date_charge": exec_date, "date_livre": exec_date,
                "did": driver_id, "vid": vehicle_id,
                "sub": tmpl.is_subcontracted,
                "subid": str(tmpl.default_subcontractor_id) if tmpl.default_subcontractor_id else None,
                "sale": tmpl.default_sale_amount_ht, "purchase": tmpl.default_purchase_amount_ht,
                "notes": f"Generee depuis modele {tmpl.code}",
                "rtid": template_id, "rrid": str(run_id),
                "uid": user.get("id"),
            })

            # Link mission to run
            await db.execute(text("""
                INSERT INTO route_run_missions (id, tenant_id, route_run_id, mission_id, sequence)
                VALUES (:id, :tid, :rrid, :mid, 1)
            """), {
                "id": str(uuid.uuid4()), "tid": tid,
                "rrid": str(run_id), "mid": str(mission_id),
            })

        created_runs.append({
            "run_id": str(run_id), "code": run_code, "date": exec_date.isoformat(),
            "mission_id": str(mission_id) if mission_id else None,
        })

    await db.commit()
    return {"generated": len(created_runs), "runs": created_runs}


# ── List runs/missions from template ───────────────────────────────

@router.get("/{template_id}/runs")
async def list_template_runs(
    template_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    tid = str(tenant.tenant_id)
    rows = (await db.execute(text("""
        SELECT rr.*,
               COALESCE(d.nom, d.last_name) || ' ' || COALESCE(d.prenom, d.first_name) AS driver_name,
               COALESCE(v.immatriculation, v.plate_number) AS vehicle_plate,
               (SELECT COUNT(*) FROM route_run_missions rrm WHERE rrm.route_run_id = rr.id) AS nb_missions
        FROM route_runs rr
        LEFT JOIN drivers d ON rr.assigned_driver_id = d.id
        LEFT JOIN vehicles v ON rr.assigned_vehicle_id = v.id
        WHERE rr.route_template_id = :rtid AND rr.tenant_id = :tid
        ORDER BY rr.service_date DESC
        LIMIT :lim OFFSET :off
    """), {"rtid": template_id, "tid": tid, "lim": limit, "off": offset})).fetchall()
    return [{
        "id": str(r.id), "code": r.code, "service_date": r.service_date.isoformat(),
        "status": r.status,
        "driver_name": r.driver_name, "vehicle_plate": r.vehicle_plate,
        "nb_missions": r.nb_missions,
        "aggregated_sale_amount_ht": float(r.aggregated_sale_amount_ht) if r.aggregated_sale_amount_ht else None,
    } for r in rows]


@router.get("/{template_id}/missions")
async def list_template_missions(
    template_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    tid = str(tenant.tenant_id)
    rows = (await db.execute(text("""
        SELECT j.id, j.numero, j.status, j.date_chargement_prevue,
               j.montant_vente_ht, j.montant_achat_ht,
               COALESCE(d.nom, d.last_name) || ' ' || COALESCE(d.prenom, d.first_name) AS driver_name,
               COALESCE(v.immatriculation, v.plate_number) AS vehicle_plate
        FROM jobs j
        LEFT JOIN drivers d ON j.driver_id = d.id
        LEFT JOIN vehicles v ON j.vehicle_id = v.id
        WHERE j.source_route_template_id = :rtid AND j.tenant_id = :tid
        ORDER BY j.date_chargement_prevue DESC
        LIMIT :lim OFFSET :off
    """), {"rtid": template_id, "tid": tid, "lim": limit, "off": offset})).fetchall()
    return [{
        "id": str(r.id), "numero": r.numero, "status": r.status,
        "date": r.date_chargement_prevue.isoformat() if r.date_chargement_prevue else None,
        "montant_vente_ht": float(r.montant_vente_ht) if r.montant_vente_ht else None,
        "driver_name": r.driver_name, "vehicle_plate": r.vehicle_plate,
    } for r in rows]
