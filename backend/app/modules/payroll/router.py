from __future__ import annotations

import calendar
import csv
import io
import uuid
from collections import defaultdict
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_token, get_current_user, require_permission
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/payroll", tags=["payroll"])


class PeriodOut(BaseModel):
    id: str
    year: int
    month: int
    status: str
    created_at: str | None = None


class PayrollVarOut(BaseModel):
    id: str
    driver_id: str
    driver_name: str
    variable_type_code: str
    variable_type_label: str
    value: float


@router.get("/periods", response_model=list[PeriodOut])
async def list_periods(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    rows = await db.execute(
        text("SELECT * FROM payroll_periods WHERE tenant_id = :tid ORDER BY year DESC, month DESC LIMIT :lim OFFSET :off"),
        {"tid": str(tenant.tenant_id), "lim": limit, "off": offset},
    )
    return [PeriodOut(id=str(r.id), year=r.year, month=r.month, status=r.status,
                      created_at=str(r.created_at) if r.created_at else None) for r in rows.fetchall()]


@router.post("/periods", response_model=PeriodOut, status_code=201)
async def create_period(
    year: int, month: int,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pid = uuid.uuid4()
    try:
        await db.execute(text("""
            INSERT INTO payroll_periods (id, tenant_id, year, month)
            VALUES (:id, :tid, :y, :m)
        """), {"id": str(pid), "tid": str(tenant.tenant_id), "y": year, "m": month})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Period already exists")
    return PeriodOut(id=str(pid), year=year, month=month, status="draft")


@router.get("/periods/{period_id}/variables", response_model=list[PayrollVarOut])
async def get_period_variables(
    period_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(text("""
        SELECT pv.id, pv.driver_id,
               COALESCE(d.prenom, d.first_name, '') || ' ' || COALESCE(d.nom, d.last_name, '') AS driver_name,
               pvt.code AS variable_type_code, pvt.label AS variable_type_label, pv.value
        FROM payroll_variables pv
        JOIN drivers d ON pv.driver_id = d.id
        JOIN payroll_variable_types pvt ON pv.variable_type_id = pvt.id
        WHERE pv.period_id = :pid AND pv.tenant_id = :tid
        ORDER BY COALESCE(d.nom, d.last_name), COALESCE(d.prenom, d.first_name), pvt.code
    """), {"pid": period_id, "tid": str(tenant.tenant_id)})
    return [PayrollVarOut(
        id=str(r.id), driver_id=str(r.driver_id), driver_name=r.driver_name,
        variable_type_code=r.variable_type_code, variable_type_label=r.variable_type_label,
        value=float(r.value),
    ) for r in rows.fetchall()]


@router.post("/periods/{period_id}/import-csv")
async def import_csv(
    period_id: str,
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import payroll variables from CSV. Delimiter ;, BOM tolerant, decimal , accepted."""
    # Verify period exists and is draft
    period = (await db.execute(
        text("SELECT * FROM payroll_periods WHERE id = :id AND tenant_id = :tid"),
        {"id": period_id, "tid": str(tenant.tenant_id)},
    )).first()
    if not period:
        raise HTTPException(404, "Period not found")
    if period.status != "draft":
        raise HTTPException(400, "Can only import into draft periods")

    content = await file.read()
    # Handle BOM
    text_content = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text_content), delimiter=";")

    imported = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        matricule = (row.get("matricule") or "").strip()
        var_code = (row.get("code_variable") or row.get("variable") or "").strip()
        raw_value = (row.get("valeur") or row.get("value") or "").strip()

        if not matricule or not var_code or not raw_value:
            errors.append(f"Row {row_num}: missing required field")
            continue

        # Accept decimal comma
        raw_value = raw_value.replace(",", ".")
        try:
            value = float(raw_value)
        except ValueError:
            errors.append(f"Row {row_num}: invalid value '{raw_value}'")
            continue

        # Resolve driver
        driver = (await db.execute(
            text("SELECT id FROM drivers WHERE tenant_id = :tid AND matricule = :mat"),
            {"tid": str(tenant.tenant_id), "mat": matricule},
        )).first()
        if not driver:
            errors.append(f"Row {row_num}: driver '{matricule}' not found")
            continue

        # Resolve variable type
        vtype = (await db.execute(
            text("SELECT id FROM payroll_variable_types WHERE tenant_id = :tid AND code = :code"),
            {"tid": str(tenant.tenant_id), "code": var_code},
        )).first()
        if not vtype:
            errors.append(f"Row {row_num}: variable type '{var_code}' not found")
            continue

        # Upsert — sum duplicates
        await db.execute(text("""
            INSERT INTO payroll_variables (id, tenant_id, period_id, driver_id, variable_type_id, value)
            VALUES (:id, :tid, :pid, :did, :vtid, :val)
            ON CONFLICT ON CONSTRAINT uq_payvar_period_driver_type
            DO UPDATE SET value = payroll_variables.value + EXCLUDED.value
        """), {
            "id": str(uuid.uuid4()), "tid": str(tenant.tenant_id),
            "pid": period_id, "did": str(driver.id), "vtid": str(vtype.id), "val": value,
        })
        imported += 1

    await db.commit()
    return {"imported": imported, "errors": errors}


@router.get("/periods/{period_id}/export-silae")
async def export_silae(
    period_id: str,
    _token: str = Query(..., description="JWT token for browser-based download"),
    _tenant: str = Query(..., description="Tenant ID for browser-based download"),
    db: AsyncSession = Depends(get_db),
):
    """Export payroll data in SILAE CSV format. Auth via query params (browser opens new tab)."""
    # Authenticate from query param
    payload = decode_token(_token)
    if not payload.get("sub"):
        raise HTTPException(401, "Invalid token")

    # Resolve tenant from query param
    try:
        tid = uuid.UUID(_tenant)
    except ValueError:
        raise HTTPException(400, "Invalid _tenant param")
    tenant = TenantContext(tenant_id=tid)

    period = (await db.execute(
        text("SELECT * FROM payroll_periods WHERE id = :id AND tenant_id = :tid"),
        {"id": period_id, "tid": str(tenant.tenant_id)},
    )).first()
    if not period:
        raise HTTPException(404, "Period not found")

    rows = await db.execute(text("""
        SELECT d.matricule, pvt.code AS var_code, pv.value,
               pm.target_code, pm.target_label
        FROM payroll_variables pv
        JOIN drivers d ON pv.driver_id = d.id
        JOIN payroll_variable_types pvt ON pv.variable_type_id = pvt.id
        LEFT JOIN payroll_mappings pm ON pm.tenant_id = pv.tenant_id AND pm.variable_type_code = pvt.code
        WHERE pv.period_id = :pid AND pv.tenant_id = :tid
        ORDER BY d.matricule, pm.target_code
    """), {"pid": period_id, "tid": str(tenant.tenant_id)})

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["matricule", "code_rubrique", "libelle_rubrique", "valeur"])

    for r in rows.fetchall():
        writer.writerow([
            r.matricule,
            r.target_code or r.var_code,
            r.target_label or r.var_code,
            f"{float(r.value):.2f}".replace(".", ","),
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=silae_{period.year}-{period.month:02d}.csv"},
    )


@router.post("/periods/{period_id}/submit")
async def submit_period(
    period_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("payroll.submit"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE payroll_periods SET status='submitted', submitted_at=NOW()
        WHERE id=:id AND tenant_id=:tid AND status='draft' RETURNING id
    """), {"id": period_id, "tid": str(tenant.tenant_id)})
    if not result.first():
        raise HTTPException(400, "Period not found or not in draft status")
    await db.commit()
    return {"status": "submitted"}


@router.post("/periods/{period_id}/approve")
async def approve_period(
    period_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("payroll.approve"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE payroll_periods SET status='approved', approved_at=NOW()
        WHERE id=:id AND tenant_id=:tid AND status='submitted' RETURNING id
    """), {"id": period_id, "tid": str(tenant.tenant_id)})
    if not result.first():
        raise HTTPException(400, "Period not found or not in submitted status")
    await db.commit()
    return {"status": "approved"}


@router.post("/periods/{period_id}/lock")
async def lock_period(
    period_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("payroll.lock"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE payroll_periods SET status='locked', locked_at=NOW()
        WHERE id=:id AND tenant_id=:tid AND status='approved' RETURNING id
    """), {"id": period_id, "tid": str(tenant.tenant_id)})
    if not result.first():
        raise HTTPException(400, "Period not found or not in approved status")
    await db.commit()
    return {"status": "locked"}


# ══════════════════════════════════════════════════════════════════
# AUTO-COMPUTE FROM MISSIONS
# ══════════════════════════════════════════════════════════════════

HEURES_NORMALES_CAP = 151.67
HEURES_SUP_25_CAP = 186.67  # hours between 151.67 and 186.67 at +25%
FORFAIT_REPAS = 9.90

PAYROLL_VARIABLE_CODES = [
    "HEURES_NORMALES",
    "HEURES_SUP_25",
    "HEURES_SUP_50",
    "NB_MISSIONS",
    "KM_TOTAL",
    "PRIME_PANIER",
]


def _compute_hours(date_chargement_reelle, date_livraison_reelle) -> float:
    """Estimate worked hours from loading to delivery timestamps."""
    if not date_chargement_reelle or not date_livraison_reelle:
        return 0.0
    try:
        start = date_chargement_reelle if isinstance(date_chargement_reelle, datetime) else datetime.fromisoformat(str(date_chargement_reelle))
        end = date_livraison_reelle if isinstance(date_livraison_reelle, datetime) else datetime.fromisoformat(str(date_livraison_reelle))
        delta = (end - start).total_seconds() / 3600.0
        return max(delta, 0.0)
    except (ValueError, TypeError):
        return 0.0


@router.post("/periods/{period_id}/compute-from-missions")
async def compute_from_missions(
    period_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-compute payroll variables from closed mission data for a given period."""
    tid = str(tenant.tenant_id)

    # 1. Load period, verify status is draft
    period = (await db.execute(
        text("SELECT * FROM payroll_periods WHERE id = :id AND tenant_id = :tid"),
        {"id": period_id, "tid": tid},
    )).first()
    if not period:
        raise HTTPException(404, "Period not found")
    if period.status != "draft":
        raise HTTPException(400, "Can only compute into draft periods")

    year = period.year
    month = period.month
    # Compute period date range
    _, last_day = calendar.monthrange(year, month)
    period_start = date(year, month, 1)
    period_end = date(year, month, last_day)

    # 2. Find all closed missions for this tenant in the period
    missions = (await db.execute(text("""
        SELECT j.id, j.driver_id,
               j.date_chargement_reelle, j.date_livraison_reelle,
               j.date_cloture, j.distance_reelle_km, j.distance_estimee_km,
               j.status
        FROM jobs j
        WHERE j.tenant_id = :tid
          AND j.status IN ('CLOTUREE', 'LIVREE', 'closed', 'delivered')
          AND j.driver_id IS NOT NULL
          AND (
              COALESCE(j.date_cloture, j.date_livraison_reelle)::date >= :pstart
              AND COALESCE(j.date_cloture, j.date_livraison_reelle)::date <= :pend
          )
    """), {"tid": tid, "pstart": period_start, "pend": period_end})).fetchall()

    # 3. Group by driver_id
    driver_missions: dict[str, list] = defaultdict(list)
    for m in missions:
        driver_missions[str(m.driver_id)].append(m)

    # 4. Resolve variable type IDs
    var_types = (await db.execute(
        text("SELECT id, code FROM payroll_variable_types WHERE tenant_id = :tid AND code = ANY(:codes)"),
        {"tid": tid, "codes": PAYROLL_VARIABLE_CODES},
    )).fetchall()
    code_to_vtid: dict[str, str] = {vt.code: str(vt.id) for vt in var_types}

    missing_codes = [c for c in PAYROLL_VARIABLE_CODES if c not in code_to_vtid]
    if missing_codes:
        raise HTTPException(
            400,
            f"Missing payroll_variable_types for codes: {', '.join(missing_codes)}. "
            "Please create them first.",
        )

    # 5. DELETE existing payroll_variables for this period (allow re-computation)
    await db.execute(
        text("DELETE FROM payroll_variables WHERE period_id = :pid AND tenant_id = :tid"),
        {"pid": period_id, "tid": tid},
    )

    # 6. Compute and insert variables per driver
    summary = []
    for driver_id, driver_ms in driver_missions.items():
        # Compute totals
        total_hours = 0.0
        nb_missions = len(driver_ms)
        km_total = 0.0

        for m in driver_ms:
            total_hours += _compute_hours(m.date_chargement_reelle, m.date_livraison_reelle)
            dist = m.distance_reelle_km if m.distance_reelle_km is not None else m.distance_estimee_km
            km_total += float(dist) if dist is not None else 0.0

        heures_normales = min(total_hours, HEURES_NORMALES_CAP)
        heures_sup_25 = min(max(total_hours - HEURES_NORMALES_CAP, 0.0), HEURES_SUP_25_CAP - HEURES_NORMALES_CAP)
        heures_sup_50 = max(total_hours - HEURES_SUP_25_CAP, 0.0)
        prime_panier = nb_missions * FORFAIT_REPAS

        variables = {
            "HEURES_NORMALES": round(heures_normales, 2),
            "HEURES_SUP_25": round(heures_sup_25, 2),
            "HEURES_SUP_50": round(heures_sup_50, 2),
            "NB_MISSIONS": float(nb_missions),
            "KM_TOTAL": round(km_total, 2),
            "PRIME_PANIER": round(prime_panier, 2),
        }

        driver_vars = []
        for code, value in variables.items():
            vtid = code_to_vtid[code]
            vid = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO payroll_variables (id, tenant_id, period_id, driver_id, variable_type_id, value)
                VALUES (:id, :tid, :pid, :did, :vtid, :val)
            """), {
                "id": vid, "tid": tid, "pid": period_id,
                "did": driver_id, "vtid": vtid, "val": value,
            })
            driver_vars.append({"code": code, "value": value})

        summary.append({
            "driver_id": driver_id,
            "nb_missions": nb_missions,
            "total_hours": round(total_hours, 2),
            "variables": driver_vars,
        })

    await db.commit()
    total_variables = sum(len(d["variables"]) for d in summary)
    return {
        "period_id": period_id,
        "year": year,
        "month": month,
        "drivers_processed": len(summary),
        "variables_created": total_variables,
        "drivers": summary,
    }
