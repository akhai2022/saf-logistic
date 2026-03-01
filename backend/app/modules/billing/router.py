from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user, require_permission
from app.core.tenant import TenantContext, get_tenant
from app.modules.billing.numbering import next_invoice_number

router = APIRouter(prefix="/v1/billing", tags=["billing"])


# ---- Pricing Rules ----

class PricingRuleIn(BaseModel):
    customer_id: str | None = None
    label: str
    rule_type: str  # km | flat | surcharge
    rate: float
    min_km: float | None = None
    max_km: float | None = None


class PricingRuleOut(BaseModel):
    id: str
    customer_id: str | None = None
    label: str
    rule_type: str
    rate: float
    min_km: float | None = None
    max_km: float | None = None
    is_active: bool = True


@router.get("/pricing-rules", response_model=list[PricingRuleOut])
async def list_pricing_rules(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    customer_id: str | None = Query(None),
):
    q = "SELECT * FROM pricing_rules WHERE tenant_id = :tid AND is_active = true"
    params: dict = {"tid": str(tenant.tenant_id)}
    if customer_id:
        q += " AND (customer_id = :cid OR customer_id IS NULL)"
        params["cid"] = customer_id
    q += " ORDER BY rule_type, label"
    rows = await db.execute(text(q), params)
    return [PricingRuleOut(
        id=str(r.id), customer_id=str(r.customer_id) if r.customer_id else None,
        label=r.label, rule_type=r.rule_type, rate=float(r.rate),
        min_km=float(r.min_km) if r.min_km else None,
        max_km=float(r.max_km) if r.max_km else None,
        is_active=r.is_active,
    ) for r in rows.fetchall()]


@router.post("/pricing-rules", response_model=PricingRuleOut, status_code=201)
async def create_pricing_rule(
    body: PricingRuleIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO pricing_rules (id, tenant_id, customer_id, label, rule_type, rate, min_km, max_km)
        VALUES (:id, :tid, :cid, :label, :rtype, :rate, :mink, :maxk)
    """), {"id": str(rid), "tid": str(tenant.tenant_id), "cid": body.customer_id,
           "label": body.label, "rtype": body.rule_type, "rate": body.rate,
           "mink": body.min_km, "maxk": body.max_km})
    await db.commit()
    return PricingRuleOut(id=str(rid), customer_id=body.customer_id, label=body.label,
                          rule_type=body.rule_type, rate=body.rate,
                          min_km=body.min_km, max_km=body.max_km)


@router.put("/pricing-rules/{rule_id}", response_model=PricingRuleOut)
async def update_pricing_rule(
    rule_id: str, body: PricingRuleIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE pricing_rules SET customer_id=:cid, label=:label, rule_type=:rtype,
            rate=:rate, min_km=:mink, max_km=:maxk
        WHERE id=:id AND tenant_id=:tid RETURNING id
    """), {"id": rule_id, "tid": str(tenant.tenant_id), "cid": body.customer_id,
           "label": body.label, "rtype": body.rule_type, "rate": body.rate,
           "mink": body.min_km, "maxk": body.max_km})
    if not result.first():
        raise HTTPException(404, "Pricing rule not found")
    await db.commit()
    return PricingRuleOut(id=rule_id, customer_id=body.customer_id, label=body.label,
                          rule_type=body.rule_type, rate=body.rate,
                          min_km=body.min_km, max_km=body.max_km)


# ---- Invoices ----

class InvoiceCreateRequest(BaseModel):
    customer_id: str
    job_ids: list[str]
    tva_rate: float = 20.0
    notes: str | None = None


class InvoiceOut(BaseModel):
    id: str
    invoice_number: str | None = None
    customer_id: str | None = None
    status: str
    issue_date: str | None = None
    due_date: str | None = None
    total_ht: float
    tva_rate: float
    total_tva: float
    total_ttc: float
    pdf_s3_key: str | None = None
    notes: str | None = None
    created_at: str | None = None


class InvoiceLineOut(BaseModel):
    id: str
    job_id: str | None = None
    description: str | None = None
    quantity: float
    unit_price: float
    amount_ht: float


class InvoiceDetailOut(InvoiceOut):
    lines: list[InvoiceLineOut] = []


class AgingItem(BaseModel):
    invoice_id: str
    invoice_number: str
    customer_name: str
    total_ttc: float
    due_date: str
    days_overdue: int


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
async def create_invoice(
    body: InvoiceCreateRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("billing.invoice.create"),
    db: AsyncSession = Depends(get_db),
):
    if not body.job_ids:
        raise HTTPException(400, "At least one job is required")

    # Load jobs
    placeholders = ", ".join(f":j{i}" for i in range(len(body.job_ids)))
    params: dict = {"tid": str(tenant.tenant_id), "cid": body.customer_id}
    for i, jid in enumerate(body.job_ids):
        params[f"j{i}"] = jid

    jobs = (await db.execute(
        text(f"SELECT * FROM jobs WHERE id IN ({placeholders}) AND tenant_id = :tid AND customer_id = :cid"),
        params,
    )).fetchall()

    if len(jobs) != len(body.job_ids):
        raise HTTPException(400, "Some jobs not found or don't belong to this customer")

    # Load pricing rules for customer
    rules = (await db.execute(
        text("""SELECT * FROM pricing_rules
                WHERE tenant_id = :tid AND is_active = true
                  AND (customer_id = :cid OR customer_id IS NULL)
                ORDER BY customer_id NULLS LAST, rule_type"""),
        {"tid": str(tenant.tenant_id), "cid": body.customer_id},
    )).fetchall()

    # Calculate lines
    inv_id = uuid.uuid4()
    total_ht = Decimal("0")
    lines_data = []

    for idx, job in enumerate(jobs):
        line_amount = Decimal("0")
        desc_parts = []

        for rule in rules:
            if rule.rule_type == "km" and job.distance_km:
                km = Decimal(str(job.distance_km))
                if rule.min_km and km < Decimal(str(rule.min_km)):
                    continue
                if rule.max_km and km > Decimal(str(rule.max_km)):
                    continue
                amt = km * Decimal(str(rule.rate))
                line_amount += amt
                desc_parts.append(f"{rule.label}: {km} km x {rule.rate} EUR")
            elif rule.rule_type == "flat":
                line_amount += Decimal(str(rule.rate))
                desc_parts.append(f"{rule.label}: {rule.rate} EUR")
            elif rule.rule_type == "surcharge":
                line_amount += Decimal(str(rule.rate))
                desc_parts.append(f"{rule.label}: {rule.rate} EUR")

        if not desc_parts:
            desc_parts.append(f"Transport {job.reference or str(job.id)[:8]}")
            line_amount = Decimal("0")

        description = f"Mission {job.reference or str(job.id)[:8]} — " + ", ".join(desc_parts)
        total_ht += line_amount
        lines_data.append({
            "id": str(uuid.uuid4()), "invoice_id": str(inv_id),
            "job_id": str(job.id), "description": description,
            "quantity": 1, "unit_price": float(line_amount),
            "amount_ht": float(line_amount), "line_order": idx,
        })

    tva = total_ht * Decimal(str(body.tva_rate)) / Decimal("100")
    ttc = total_ht + tva

    # Get customer payment terms
    cust = (await db.execute(
        text("SELECT payment_terms_days FROM customers WHERE id = :cid"),
        {"cid": body.customer_id},
    )).first()
    payment_terms = cust.payment_terms_days if cust else 30
    issue = date.today()
    due = issue + timedelta(days=payment_terms)

    await db.execute(text("""
        INSERT INTO invoices (id, tenant_id, customer_id, status, issue_date, due_date,
                              total_ht, tva_rate, total_tva, total_ttc, notes)
        VALUES (:id, :tid, :cid, 'draft', :idate, :ddate, :ht, :tva_rate, :tva, :ttc, :notes)
    """), {
        "id": str(inv_id), "tid": str(tenant.tenant_id), "cid": body.customer_id,
        "idate": issue, "ddate": due,
        "ht": float(total_ht), "tva_rate": body.tva_rate,
        "tva": float(tva), "ttc": float(ttc), "notes": body.notes,
    })

    for ld in lines_data:
        await db.execute(text("""
            INSERT INTO invoice_lines (id, invoice_id, job_id, description, quantity, unit_price, amount_ht, line_order)
            VALUES (:id, :invoice_id, :job_id, :description, :quantity, :unit_price, :amount_ht, :line_order)
        """), ld)

    await db.commit()
    return InvoiceOut(
        id=str(inv_id), status="draft", customer_id=body.customer_id,
        issue_date=str(issue), due_date=str(due),
        total_ht=float(total_ht), tva_rate=body.tva_rate,
        total_tva=float(tva), total_ttc=float(ttc), notes=body.notes,
    )


@router.post("/invoices/{inv_id}/validate", response_model=InvoiceOut)
async def validate_invoice(
    inv_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("billing.invoice.validate"),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT * FROM invoices WHERE id = :id AND tenant_id = :tid"),
        {"id": inv_id, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "Invoice not found")
    if row.status != "draft":
        raise HTTPException(400, "Only draft invoices can be validated")

    number = await next_invoice_number(db, tenant.tenant_id)

    await db.execute(text("""
        UPDATE invoices SET status='validated', invoice_number=:num, validated_at=NOW()
        WHERE id=:id
    """), {"id": inv_id, "num": number})
    await db.commit()

    # Trigger PDF generation
    from app.infra.celery_app import celery_app
    celery_app.send_task("app.infra.tasks.invoice_generate_pdf", args=[inv_id])

    return InvoiceOut(
        id=str(row.id), invoice_number=number, customer_id=str(row.customer_id),
        status="validated", issue_date=str(row.issue_date), due_date=str(row.due_date),
        total_ht=float(row.total_ht), tva_rate=float(row.tva_rate),
        total_tva=float(row.total_tva), total_ttc=float(row.total_ttc),
        pdf_s3_key=row.pdf_s3_key, notes=row.notes,
    )


@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
):
    q = "SELECT * FROM invoices WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if status:
        q += " AND status = :status"
        params["status"] = status
    q += " ORDER BY created_at DESC"
    rows = await db.execute(text(q), params)
    return [InvoiceOut(
        id=str(r.id), invoice_number=r.invoice_number,
        customer_id=str(r.customer_id) if r.customer_id else None,
        status=r.status, issue_date=str(r.issue_date) if r.issue_date else None,
        due_date=str(r.due_date) if r.due_date else None,
        total_ht=float(r.total_ht), tva_rate=float(r.tva_rate),
        total_tva=float(r.total_tva), total_ttc=float(r.total_ttc),
        pdf_s3_key=r.pdf_s3_key, notes=r.notes,
        created_at=str(r.created_at) if r.created_at else None,
    ) for r in rows.fetchall()]


@router.get("/invoices/{inv_id}", response_model=InvoiceDetailOut)
async def get_invoice(
    inv_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT * FROM invoices WHERE id = :id AND tenant_id = :tid"),
        {"id": inv_id, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "Invoice not found")

    lines = (await db.execute(
        text("SELECT * FROM invoice_lines WHERE invoice_id = :id ORDER BY line_order"),
        {"id": inv_id},
    )).fetchall()

    return InvoiceDetailOut(
        id=str(row.id), invoice_number=row.invoice_number,
        customer_id=str(row.customer_id) if row.customer_id else None,
        status=row.status, issue_date=str(row.issue_date) if row.issue_date else None,
        due_date=str(row.due_date) if row.due_date else None,
        total_ht=float(row.total_ht), tva_rate=float(row.tva_rate),
        total_tva=float(row.total_tva), total_ttc=float(row.total_ttc),
        pdf_s3_key=row.pdf_s3_key, notes=row.notes,
        created_at=str(row.created_at) if row.created_at else None,
        lines=[InvoiceLineOut(
            id=str(l.id), job_id=str(l.job_id) if l.job_id else None,
            description=l.description, quantity=float(l.quantity),
            unit_price=float(l.unit_price), amount_ht=float(l.amount_ht),
        ) for l in lines],
    )


@router.get("/aging", response_model=list[AgingItem])
async def ar_aging(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    rows = await db.execute(text("""
        SELECT i.id, i.invoice_number, c.name AS customer_name, i.total_ttc, i.due_date
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.tenant_id = :tid AND i.status = 'validated' AND i.due_date < :today
        ORDER BY i.due_date
    """), {"tid": str(tenant.tenant_id), "today": today})
    return [AgingItem(
        invoice_id=str(r.id), invoice_number=r.invoice_number,
        customer_name=r.customer_name, total_ttc=float(r.total_ttc),
        due_date=str(r.due_date), days_overdue=(today - r.due_date).days,
    ) for r in rows.fetchall()]
