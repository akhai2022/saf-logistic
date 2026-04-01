"""API router for the bulk import module.

Provides endpoints for uploading, previewing, and applying CSV/Excel
imports for drivers, vehicles, clients, and subcontractors.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.modules.imports.schemas import ApplyResult, ImportJobOut, PreviewResult
from app.modules.imports.service import (
    apply_import,
    create_import_job,
    generate_errors_csv,
    get_import_job,
    preview_import,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/imports", tags=["imports"])

# Accepted content types
_ACCEPTED_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}

# Max file size: 10 MB
_MAX_FILE_SIZE = 10 * 1024 * 1024


class ColumnMappingBody(BaseModel):
    """Optional body for preview/apply to override auto-detected mapping."""
    column_mapping: dict[str, str] | None = None


@router.post("/upload", response_model=ImportJobOut, status_code=201)
async def upload_import_file(
    entity_type: str = Query(..., description="Entity type: driver, vehicle, client, subcontractor"),
    file: UploadFile = File(...),
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImportJobOut:
    """Upload a CSV or Excel file for import.

    The file is stored in S3 and an import_jobs record is created with
    status='uploaded'. Call /preview next.
    """
    from app.modules.imports.field_maps import VALID_ENTITY_TYPES

    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            400,
            f"Type d'entite invalide: {entity_type}. "
            f"Valeurs acceptees: {', '.join(sorted(VALID_ENTITY_TYPES))}",
        )

    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(413, "Le fichier depasse la taille maximale de 10 Mo.")
    if len(content) == 0:
        raise HTTPException(400, "Le fichier est vide.")

    file_name = file.filename or "import.csv"
    content_type = file.content_type or "application/octet-stream"

    try:
        job = await create_import_job(
            db=db,
            tenant_id=tenant.tenant_id,
            user_id=uuid.UUID(str(user["id"])),
            entity_type=entity_type,
            file_name=file_name,
            content_type=content_type,
            file_content=content,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    return ImportJobOut(**job)


@router.post("/{job_id}/preview", response_model=PreviewResult)
async def preview_import_job(
    job_id: str,
    body: ColumnMappingBody | None = None,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreviewResult:
    """Preview the import: parse file, detect mapping, validate rows.

    Returns sample rows, detected column mapping, and validation errors.
    No data is written to entity tables.
    """
    try:
        result = await preview_import(
            db=db,
            tenant_id=tenant.tenant_id,
            job_id=job_id,
            user_mapping=body.column_mapping if body else None,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    return result


@router.post("/{job_id}/apply", response_model=ApplyResult)
async def apply_import_job(
    job_id: str,
    body: ColumnMappingBody | None = None,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplyResult:
    """Apply the import: validate and upsert rows into the database.

    Uses INSERT ON CONFLICT DO UPDATE with natural keys.
    Invalid rows are skipped and reported in the errors list.
    """
    try:
        result = await apply_import(
            db=db,
            tenant_id=tenant.tenant_id,
            user_id=uuid.UUID(str(user["id"])),
            job_id=job_id,
            user_mapping=body.column_mapping if body else None,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    return result


@router.get("/{job_id}", response_model=ImportJobOut)
async def get_import_job_detail(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImportJobOut:
    """Get the current state of an import job."""
    job = await get_import_job(db, tenant.tenant_id, job_id)
    if not job:
        raise HTTPException(404, "Import job introuvable.")
    return ImportJobOut(**job)


@router.get("/{job_id}/errors-csv")
async def download_errors_csv(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Download a CSV file containing all validation errors for this import."""
    job = await get_import_job(db, tenant.tenant_id, job_id)
    if not job:
        raise HTTPException(404, "Import job introuvable.")

    errors_json = job.get("errors_json") or []
    csv_bytes = generate_errors_csv(errors_json)

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="errors_{job_id}.csv"',
        },
    )
