from __future__ import annotations

import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user, require_permission
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
):
    rows = await db.execute(
        text("SELECT * FROM payroll_periods WHERE tenant_id = :tid ORDER BY year DESC, month DESC"),
        {"tid": str(tenant.tenant_id)},
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
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export payroll data in SILAE CSV format."""
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
