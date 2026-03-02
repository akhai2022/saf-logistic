"""Reusable audit logger — INSERT into audit_logs table."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def log_audit(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    user_email: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Insert an immutable audit log entry. Call before commit in the same transaction."""
    import json

    await db.execute(
        text("""
            INSERT INTO audit_logs
                (id, tenant_id, user_id, user_email, action, entity_type,
                 entity_id, old_value, new_value, metadata, ip_address)
            VALUES
                (:id, :tid, :uid, :email, :action, :etype,
                 :eid, CAST(:old AS json), CAST(:new AS json),
                 CAST(:meta AS json), :ip)
        """),
        {
            "id": str(uuid.uuid4()),
            "tid": str(tenant_id),
            "uid": str(user_id) if user_id else None,
            "email": user_email,
            "action": action,
            "etype": entity_type,
            "eid": entity_id,
            "old": json.dumps(old_value) if old_value else None,
            "new": json.dumps(new_value) if new_value else None,
            "meta": json.dumps(metadata) if metadata else None,
            "ip": ip_address,
        },
    )
