"""Route Runs (Exécution / Tournée du jour) — actual operational routes for a specific date."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.modules.route_runs.schemas import (
    RUN_TRANSITIONS,
    AssignMissionRequest,
    RegulateRequest,
    RegulateResponse,
    RegulatedRunResult,
    ReorderRequest,
    RouteRunCreate,
    RouteRunDetail,
    RouteRunMissionOut,
    RouteRunOut,
    RouteRunUpdate,
)

router = APIRouter(prefix="/v1/route-runs", tags=["route-runs"])


_BASE_SELECT = """
    SELECT rr.*,
           rt.code AS template_code,
           rt.label AS template_label,
           COALESCE(d.nom, d.last_name) || ' ' || COALESCE(d.prenom, d.first_name) AS assigned_driver_name,
           COALESCE(v.immatriculation, v.plate_number) AS assigned_vehicle_plate,
           (SELECT COUNT(*) FROM route_run_missions rrm WHERE rrm.route_run_id = rr.id) AS nb_missions
    FROM route_runs rr
    LEFT JOIN route_templates rt ON rr.route_template_id = rt.id
    LEFT JOIN drivers d ON rr.assigned_driver_id = d.id
    LEFT JOIN vehicles v ON rr.assigned_vehicle_id = v.id
"""


def _run_from_row(r) -> RouteRunOut:
    return RouteRunOut(
        id=str(r.id),
        route_template_id=str(r.route_template_id) if r.route_template_id else None,
        template_code=getattr(r, "template_code", None),
        template_label=getattr(r, "template_label", None),
        code=r.code, service_date=r.service_date, status=r.status,
        assigned_driver_id=str(r.assigned_driver_id) if r.assigned_driver_id else None,
        assigned_driver_name=getattr(r, "assigned_driver_name", None),
        assigned_vehicle_id=str(r.assigned_vehicle_id) if r.assigned_vehicle_id else None,
        assigned_vehicle_plate=getattr(r, "assigned_vehicle_plate", None),
        planned_start_at=r.planned_start_at.isoformat() if r.planned_start_at else None,
        planned_end_at=r.planned_end_at.isoformat() if r.planned_end_at else None,
        actual_start_at=r.actual_start_at.isoformat() if r.actual_start_at else None,
        actual_end_at=r.actual_end_at.isoformat() if r.actual_end_at else None,
        aggregated_sale_amount_ht=r.aggregated_sale_amount_ht,
        aggregated_purchase_amount_ht=r.aggregated_purchase_amount_ht,
        aggregated_margin_ht=r.aggregated_margin_ht,
        nb_missions=getattr(r, "nb_missions", 0) or 0,
        notes=r.notes,
        created_at=r.created_at.isoformat() if r.created_at else None,
        regulated_at=r.regulated_at.isoformat() if getattr(r, "regulated_at", None) else None,
        regulated_by=str(r.regulated_by) if getattr(r, "regulated_by", None) else None,
        regulation_source=getattr(r, "regulation_source", None),
    )


# ── CRUD ───────────────────────────────────────────────────────────

@router.get("", response_model=list[RouteRunOut])
async def list_runs(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
    template_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    search: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    q = _BASE_SELECT + " WHERE rr.tenant_id = :tid"
    params: dict[str, Any] = {"tid": str(tenant.tenant_id)}
    if status:
        q += " AND rr.status = :status"
        params["status"] = status
    if template_id:
        q += " AND rr.route_template_id = :rtid"
        params["rtid"] = template_id
    if date_from:
        from datetime import date as datemod
        q += " AND rr.service_date >= :df"
        params["df"] = datemod.fromisoformat(date_from) if isinstance(date_from, str) else date_from
    if date_to:
        from datetime import date as datemod
        q += " AND rr.service_date <= :dt"
        params["dt"] = datemod.fromisoformat(date_to) if isinstance(date_to, str) else date_to
    if search:
        q += " AND (rr.code ILIKE :s OR rt.code ILIKE :s OR rt.label ILIKE :s)"
        params["s"] = f"%{search}%"
    allowed = {"service_date": "rr.service_date", "code": "rr.code", "status": "rr.status", "created_at": "rr.created_at"}
    sort_col = allowed.get(sort_by, "rr.service_date") if sort_by else "rr.service_date"
    q += f" ORDER BY {sort_col} {order} LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = (await db.execute(text(q), params)).fetchall()
    return [_run_from_row(r) for r in rows]


@router.post("", response_model=RouteRunOut, status_code=201)
async def create_run(
    body: RouteRunCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    code = body.code or f"RUN-{body.service_date.isoformat()}-{uuid.uuid4().hex[:6]}"

    run_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO route_runs (
            id, tenant_id, route_template_id, code, service_date, status,
            assigned_driver_id, assigned_vehicle_id,
            planned_start_at, planned_end_at, notes, created_by
        ) VALUES (
            :id, :tid, :rtid, :code, :sd, 'PLANNED',
            :did, :vid, :ps, :pe, :notes, :uid
        )
    """), {
        "id": str(run_id), "tid": tid, "rtid": body.route_template_id,
        "code": code, "sd": body.service_date,
        "did": body.assigned_driver_id, "vid": body.assigned_vehicle_id,
        "ps": body.planned_start_at, "pe": body.planned_end_at,
        "notes": body.notes, "uid": user.get("id"),
    })
    await db.commit()
    row = (await db.execute(text(_BASE_SELECT + " WHERE rr.id = :id"), {"id": str(run_id)})).first()
    return _run_from_row(row)


# ── Regulation ────────────────────────────────────────────────────

@router.post("/regulate", response_model=RegulateResponse)
async def regulate_runs(
    body: RegulateRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bulk-regulate overdue route runs for this tenant.

    Eligible: service_date < today AND status IN (DISPATCHED, IN_PROGRESS).
    If body.run_ids is provided, only those runs are considered.
    If body.preview is True, returns eligible runs without modifying them.
    """
    tid = str(tenant.tenant_id)
    today = date.today()
    now = datetime.now(timezone.utc)

    # Build eligibility query
    q = """
        SELECT rr.id, rr.tenant_id, rr.code, rr.service_date, rr.status,
               rr.planned_start_at, rr.planned_end_at,
               rr.actual_start_at, rr.actual_end_at,
               rr.regulated_at
        FROM route_runs rr
        WHERE rr.service_date < :cutoff
          AND rr.status IN ('DISPATCHED', 'IN_PROGRESS')
          AND rr.regulated_at IS NULL
          AND rr.tenant_id = :tid
    """
    params: dict[str, Any] = {"cutoff": today, "tid": tid}
    if body.run_ids:
        q += " AND rr.id = ANY(:ids)"
        params["ids"] = body.run_ids
    q += " ORDER BY rr.service_date ASC"

    eligible = (await db.execute(text(q), params)).fetchall()

    if body.preview:
        return RegulateResponse(
            eligible=len(eligible),
            regulated=0,
            skipped=0,
            errors=0,
            details=[RegulatedRunResult(
                run_id=str(r.id), code=r.code,
                service_date=r.service_date.isoformat(),
                old_status=r.status, new_status="COMPLETED",
                aggregated_sale_amount_ht=0, aggregated_purchase_amount_ht=0,
                aggregated_margin_ht=0,
            ) for r in eligible],
        )

    user_id = user.get("id")
    regulated = []
    errors = 0

    for run in eligible:
        try:
            # Aggregate totals from assigned missions
            totals = (await db.execute(text("""
                SELECT COALESCE(SUM(j.montant_vente_ht), 0) AS sale,
                       COALESCE(SUM(j.montant_achat_ht), 0) AS purchase
                FROM route_run_missions rrm
                JOIN jobs j ON rrm.mission_id = j.id
                WHERE rrm.route_run_id = :rid
            """), {"rid": str(run.id)})).first()

            sale = float(totals.sale) if totals else 0.0
            purchase = float(totals.purchase) if totals else 0.0
            margin = sale - purchase
            service_date = run.service_date

            # Determine actual_start_at
            actual_start = run.actual_start_at
            if actual_start is None:
                actual_start = run.planned_start_at or datetime(
                    service_date.year, service_date.month, service_date.day,
                    8, 0, tzinfo=timezone.utc,
                )

            # Determine actual_end_at
            actual_end = run.actual_end_at
            if actual_end is None:
                actual_end = run.planned_end_at or datetime(
                    service_date.year, service_date.month, service_date.day,
                    23, 59, tzinfo=timezone.utc,
                )

            # Update run
            await db.execute(text("""
                UPDATE route_runs SET
                    status = 'COMPLETED',
                    actual_start_at = :start, actual_end_at = :end,
                    aggregated_sale_amount_ht = :sale,
                    aggregated_purchase_amount_ht = :purchase,
                    aggregated_margin_ht = :margin,
                    regulated_at = :now, regulated_by = :uid,
                    regulation_source = 'manual', updated_at = :now
                WHERE id = :id AND tenant_id = :tid
            """), {
                "id": str(run.id), "tid": tid,
                "start": actual_start, "end": actual_end,
                "sale": sale, "purchase": purchase, "margin": margin,
                "now": now, "uid": user_id,
            })

            # Audit log
            from app.core.audit import log_audit
            await log_audit(
                db, tenant.tenant_id,
                user_id=uuid.UUID(user_id) if user_id else None,
                user_email=user.get("email"),
                action="REGULATE",
                entity_type="route_run",
                entity_id=str(run.id),
                old_value={"status": run.status},
                new_value={
                    "status": "COMPLETED",
                    "aggregated_sale_amount_ht": sale,
                    "aggregated_purchase_amount_ht": purchase,
                },
                metadata={"regulation_source": "manual", "service_date": service_date.isoformat()},
            )

            regulated.append(RegulatedRunResult(
                run_id=str(run.id), code=run.code,
                service_date=service_date.isoformat(),
                old_status=run.status, new_status="COMPLETED",
                aggregated_sale_amount_ht=sale,
                aggregated_purchase_amount_ht=purchase,
                aggregated_margin_ht=margin,
            ))
        except Exception:
            errors += 1

    await db.commit()

    return RegulateResponse(
        eligible=len(eligible),
        regulated=len(regulated),
        skipped=0,
        errors=errors,
        details=regulated,
    )


# ── Detail / Update ──────────────────────────────────────────────

@router.get("/{run_id}", response_model=RouteRunDetail)
async def get_run(
    run_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    r = (await db.execute(text(
        _BASE_SELECT + " WHERE rr.id = :id AND rr.tenant_id = :tid"
    ), {"id": run_id, "tid": tid})).first()
    if not r:
        raise HTTPException(404, "Execution non trouvee")

    # Fetch assigned missions with sequence
    mission_rows = (await db.execute(text("""
        SELECT rrm.id, rrm.mission_id, rrm.sequence, rrm.assignment_status,
               rrm.planned_eta, rrm.actual_eta,
               j.numero AS mission_code, j.status AS mission_status,
               j.montant_vente_ht,
               c.raison_sociale AS customer_name
        FROM route_run_missions rrm
        JOIN jobs j ON rrm.mission_id = j.id
        LEFT JOIN customers c ON j.customer_id = c.id
        WHERE rrm.route_run_id = :rid
        ORDER BY rrm.sequence
    """), {"rid": run_id})).fetchall()

    base = _run_from_row(r)
    return RouteRunDetail(
        **base.model_dump(),
        missions=[RouteRunMissionOut(
            id=str(m.id), mission_id=str(m.mission_id),
            mission_code=m.mission_code, sequence=m.sequence,
            assignment_status=m.assignment_status,
            planned_eta=m.planned_eta.isoformat() if m.planned_eta else None,
            actual_eta=m.actual_eta.isoformat() if m.actual_eta else None,
            customer_name=m.customer_name,
            mission_status=m.mission_status,
            montant_vente_ht=m.montant_vente_ht,
        ) for m in mission_rows],
    )


@router.put("/{run_id}", response_model=RouteRunOut)
async def update_run(
    run_id: str, body: RouteRunUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    await db.execute(text("""
        UPDATE route_runs SET
            assigned_driver_id = :did, assigned_vehicle_id = :vid,
            planned_start_at = :ps, planned_end_at = :pe,
            notes = :notes, updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": run_id, "tid": tid,
        "did": body.assigned_driver_id, "vid": body.assigned_vehicle_id,
        "ps": body.planned_start_at, "pe": body.planned_end_at,
        "notes": body.notes,
    })
    await db.commit()
    row = (await db.execute(text(_BASE_SELECT + " WHERE rr.id = :id"), {"id": run_id})).first()
    return _run_from_row(row)


# ── Mission assignment ─────────────────────────────────────────────

@router.post("/{run_id}/assign-mission")
async def assign_mission(
    run_id: str, body: AssignMissionRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    # Auto-calculate sequence if not provided
    if body.sequence is None:
        max_seq = (await db.execute(text(
            "SELECT COALESCE(MAX(sequence), 0) FROM route_run_missions WHERE route_run_id = :rid"
        ), {"rid": run_id})).scalar()
        seq = max_seq + 1
    else:
        seq = body.sequence

    rrm_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO route_run_missions (id, tenant_id, route_run_id, mission_id, sequence)
        VALUES (:id, :tid, :rid, :mid, :seq)
    """), {"id": str(rrm_id), "tid": tid, "rid": run_id, "mid": body.mission_id, "seq": seq})
    await db.commit()
    return {"id": str(rrm_id), "sequence": seq}


@router.delete("/{run_id}/missions/{mission_id}")
async def remove_mission(
    run_id: str, mission_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text(
        "DELETE FROM route_run_missions WHERE route_run_id = :rid AND mission_id = :mid AND tenant_id = :tid"
    ), {"rid": run_id, "mid": mission_id, "tid": str(tenant.tenant_id)})
    await db.commit()
    return {"ok": True}


@router.put("/{run_id}/reorder")
async def reorder_missions(
    run_id: str, body: ReorderRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    # Temporarily set sequences to negative to avoid unique constraint conflicts
    await db.execute(text(
        "UPDATE route_run_missions SET sequence = -sequence WHERE route_run_id = :rid AND tenant_id = :tid"
    ), {"rid": run_id, "tid": tid})
    for i, mid in enumerate(body.mission_ids, 1):
        await db.execute(text(
            "UPDATE route_run_missions SET sequence = :seq WHERE route_run_id = :rid AND mission_id = :mid AND tenant_id = :tid"
        ), {"seq": i, "rid": run_id, "mid": mid, "tid": tid})
    await db.commit()
    return {"ok": True}


# ── Status transitions ─────────────────────────────────────────────

async def _transition_run(run_id: str, target: str, tenant: TenantContext, user: dict, db: AsyncSession,
                           extra_sets: str = "", extra_params: dict | None = None):
    tid = str(tenant.tenant_id)
    current = (await db.execute(text(
        "SELECT status FROM route_runs WHERE id = :id AND tenant_id = :tid"
    ), {"id": run_id, "tid": tid})).scalar()
    if not current:
        raise HTTPException(404, "Execution non trouvee")
    if target not in RUN_TRANSITIONS.get(current, set()):
        raise HTTPException(422, f"Transition {current} → {target} non autorisee")

    sets = f"status = :s, updated_at = NOW(){', ' + extra_sets if extra_sets else ''}"
    params = {"s": target, "id": run_id, "tid": tid}
    if extra_params:
        params.update(extra_params)
    await db.execute(text(f"UPDATE route_runs SET {sets} WHERE id = :id AND tenant_id = :tid"), params)
    await db.commit()
    return {"ok": True, "status": target}


@router.post("/{run_id}/dispatch")
async def dispatch_run(run_id: str, tenant: TenantContext = Depends(get_tenant),
                        user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _transition_run(run_id, "DISPATCHED", tenant, user, db)


@router.post("/{run_id}/start")
async def start_run(run_id: str, tenant: TenantContext = Depends(get_tenant),
                     user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc).isoformat()
    return await _transition_run(run_id, "IN_PROGRESS", tenant, user, db,
                                  "actual_start_at = :now", {"now": now})


@router.post("/{run_id}/complete")
async def complete_run(run_id: str, tenant: TenantContext = Depends(get_tenant),
                        user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tid = str(tenant.tenant_id)
    now = datetime.now(timezone.utc).isoformat()

    # Aggregate totals from assigned missions
    totals = (await db.execute(text("""
        SELECT COALESCE(SUM(j.montant_vente_ht), 0) AS sale,
               COALESCE(SUM(j.montant_achat_ht), 0) AS purchase
        FROM route_run_missions rrm
        JOIN jobs j ON rrm.mission_id = j.id
        WHERE rrm.route_run_id = :rid
    """), {"rid": run_id})).first()

    sale = float(totals.sale) if totals else 0
    purchase = float(totals.purchase) if totals else 0

    return await _transition_run(
        run_id, "COMPLETED", tenant, user, db,
        "actual_end_at = :now, aggregated_sale_amount_ht = :sale, aggregated_purchase_amount_ht = :purchase, aggregated_margin_ht = :margin",
        {"now": now, "sale": sale, "purchase": purchase, "margin": sale - purchase},
    )


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: str, tenant: TenantContext = Depends(get_tenant),
                      user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _transition_run(run_id, "CANCELLED", tenant, user, db)
