from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.infra.s3 import presign_get_url, presign_put_url

router = APIRouter(prefix="/v1/files", tags=["files"])


class PresignUploadRequest(BaseModel):
    file_name: str
    content_type: str = "application/octet-stream"
    entity_type: str  # job_pod | document | ocr
    entity_id: str | None = None


class PresignUploadResponse(BaseModel):
    upload_url: str
    s3_key: str


class PresignDownloadResponse(BaseModel):
    download_url: str


@router.post("/presign-upload", response_model=PresignUploadResponse)
async def presign_upload(
    body: PresignUploadRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
):
    ext = body.file_name.rsplit(".", 1)[-1] if "." in body.file_name else "bin"
    unique = uuid.uuid4().hex[:12]
    key = f"{tenant.tenant_id}/{body.entity_type}/{unique}.{ext}"
    url = presign_put_url(key, content_type=body.content_type)
    return PresignUploadResponse(upload_url=url, s3_key=key)


@router.post("/confirm-upload")
async def confirm_upload(
    s3_key: str,
    entity_type: str,
    entity_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate key belongs to tenant
    if not s3_key.startswith(str(tenant.tenant_id)):
        raise HTTPException(403, "Key does not belong to tenant")
    return {"status": "confirmed", "s3_key": s3_key}


@router.get("/presign-download", response_model=PresignDownloadResponse)
async def presign_download(
    s3_key: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
):
    if not s3_key.startswith(str(tenant.tenant_id)):
        raise HTTPException(403, "Key does not belong to tenant")
    url = presign_get_url(s3_key)
    return PresignDownloadResponse(download_url=url)
