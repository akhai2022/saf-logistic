from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.settings import settings
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/ocr", tags=["ocr"])


class OcrJobCreate(BaseModel):
    s3_key: str
    file_name: str


class OcrJobOut(BaseModel):
    id: str
    s3_key: str
    file_name: str | None
    status: str
    provider: str | None
    extracted_data: dict | None = None
    confidence: float | None = None
    doc_type: str | None = None
    doc_type_confidence: float | None = None
    extracted_fields: dict | None = None
    field_confidences: dict | None = None
    global_confidence: float | None = None
    extraction_errors: list[str] | None = None
    supplier_invoice_id: str | None = None
    created_at: str | None = None


class OcrValidateRequest(BaseModel):
    supplier_id: str | None = None
    supplier_name: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    total_ht: float | None = None
    total_tva: float | None = None
    total_ttc: float | None = None


def _mask_iban_in_fields(fields: dict | None) -> dict | None:
    """Mask IBAN values in extracted fields for API responses."""
    if not fields:
        return fields
    from app.modules.ocr.extractors.validators import mask_iban
    result = dict(fields)
    if "iban" in result and result["iban"]:
        result["iban_masked"] = mask_iban(result["iban"])
    return result


def _row_to_out(r) -> OcrJobOut:
    """Convert a DB row to OcrJobOut with IBAN masking."""
    extracted_fields = r.extracted_fields if hasattr(r, "extracted_fields") else None
    extraction_errors = r.extraction_errors if hasattr(r, "extraction_errors") else None

    return OcrJobOut(
        id=str(r.id),
        s3_key=r.s3_key,
        file_name=r.file_name,
        status=r.status,
        provider=r.provider,
        extracted_data=r.extracted_data,
        confidence=float(r.confidence) if r.confidence else None,
        doc_type=r.doc_type if hasattr(r, "doc_type") else None,
        doc_type_confidence=float(r.doc_type_confidence) if hasattr(r, "doc_type_confidence") and r.doc_type_confidence else None,
        extracted_fields=_mask_iban_in_fields(extracted_fields),
        field_confidences=r.field_confidences if hasattr(r, "field_confidences") else None,
        global_confidence=float(r.global_confidence) if hasattr(r, "global_confidence") and r.global_confidence else None,
        extraction_errors=extraction_errors if extraction_errors else None,
        supplier_invoice_id=str(r.supplier_invoice_id) if r.supplier_invoice_id else None,
        created_at=str(r.created_at) if r.created_at else None,
    )


@router.post("/jobs", response_model=OcrJobOut, status_code=201)
async def create_ocr_job(
    body: OcrJobCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO ocr_jobs (id, tenant_id, s3_key, file_name, provider)
        VALUES (:id, :tid, :s3, :fname, :provider)
    """), {
        "id": str(job_id), "tid": str(tenant.tenant_id),
        "s3": body.s3_key, "fname": body.file_name,
        "provider": settings.OCR_PROVIDER,
    })
    await db.commit()

    # Dispatch Celery task
    from app.infra.celery_app import celery_app
    celery_app.send_task("app.infra.tasks.ocr_process_job", args=[str(job_id)])

    return OcrJobOut(
        id=str(job_id), s3_key=body.s3_key, file_name=body.file_name,
        status="pending", provider=settings.OCR_PROVIDER,
    )


@router.get("/jobs", response_model=list[OcrJobOut])
async def list_ocr_jobs(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
):
    q = "SELECT * FROM ocr_jobs WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if status:
        q += " AND status = :status"
        params["status"] = status
    q += " ORDER BY created_at DESC"
    rows = await db.execute(text(q), params)
    return [_row_to_out(r) for r in rows.fetchall()]


@router.get("/jobs/{job_id}", response_model=OcrJobOut)
async def get_ocr_job(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT * FROM ocr_jobs WHERE id = :id AND tenant_id = :tid"),
        {"id": job_id, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "OCR job not found")
    return _row_to_out(row)


@router.post("/jobs/{job_id}/validate")
async def validate_ocr_job(
    job_id: str,
    body: OcrValidateRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate OCR extraction and create a supplier invoice."""
    row = (await db.execute(
        text("SELECT * FROM ocr_jobs WHERE id = :id AND tenant_id = :tid"),
        {"id": job_id, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "OCR job not found")
    if row.status != "needs_review":
        raise HTTPException(400, "OCR job is not in needs_review status")

    # Create supplier invoice
    si_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO supplier_invoices (id, tenant_id, supplier_id, invoice_number, invoice_date,
                                       total_ht, total_tva, total_ttc, s3_key, status)
        VALUES (:id, :tid, :sid, :inum, :idate, :ht, :tva, :ttc, :s3, 'validated')
    """), {
        "id": str(si_id), "tid": str(tenant.tenant_id),
        "sid": body.supplier_id, "inum": body.invoice_number,
        "idate": body.invoice_date, "ht": body.total_ht,
        "tva": body.total_tva, "ttc": body.total_ttc,
        "s3": row.s3_key,
    })

    await db.execute(text("""
        UPDATE ocr_jobs SET status='validated', supplier_invoice_id=:siid WHERE id=:id
    """), {"id": job_id, "siid": str(si_id)})
    await db.commit()

    return {"status": "validated", "supplier_invoice_id": str(si_id)}
