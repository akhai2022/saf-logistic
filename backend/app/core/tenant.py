from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Header, HTTPException


@dataclass(frozen=True)
class TenantContext:
    tenant_id: uuid.UUID
    agency_id: uuid.UUID | None = None


async def get_tenant(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_agency_id: str | None = Header(None, alias="X-Agency-ID"),
) -> TenantContext:
    try:
        tid = uuid.UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(400, "Invalid X-Tenant-ID header")
    aid = None
    if x_agency_id:
        try:
            aid = uuid.UUID(x_agency_id)
        except ValueError:
            raise HTTPException(400, "Invalid X-Agency-ID header")
    return TenantContext(tenant_id=tid, agency_id=aid)
