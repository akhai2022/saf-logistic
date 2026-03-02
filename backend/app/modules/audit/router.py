"""Audit log viewer — paginated, with filters."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import require_permission
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/audit-logs", tags=["audit"])


class AuditLogOut(BaseModel):
    id: str
    user_id: str | None = None
    user_email: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    old_value: dict | None = None
    new_value: dict | None = None
    metadata: dict | None = None
    ip_address: str | None = None
    created_at: str | None = None


def _audit_from_row(r) -> AuditLogOut:
    return AuditLogOut(
        id=str(r.id),
        user_id=str(r.user_id) if r.user_id else None,
        user_email=r.user_email,
        action=r.action,
        entity_type=r.entity_type,
        entity_id=r.entity_id,
        old_value=r.old_value,
        new_value=r.new_value,
        metadata=r.metadata,
        ip_address=r.ip_address,
        created_at=str(r.created_at) if r.created_at else None,
    )


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("audit.read"),
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = Query(None),
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    q = "SELECT * FROM audit_logs WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}

    if entity_type:
        q += " AND entity_type = :etype"
        params["etype"] = entity_type
    if user_id:
        q += " AND user_id = :uid"
        params["uid"] = user_id
    if action:
        q += " AND action = :action"
        params["action"] = action
    if date_from:
        q += " AND created_at >= :dfrom"
        params["dfrom"] = date_from
    if date_to:
        q += " AND created_at <= :dto"
        params["dto"] = date_to

    q += " ORDER BY created_at DESC LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset

    rows = (await db.execute(text(q), params)).fetchall()
    return [_audit_from_row(r) for r in rows]
