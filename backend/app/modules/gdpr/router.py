"""GDPR — data export and deletion request."""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/v1/gdpr", tags=["gdpr"])


@router.post("/export")
async def export_user_data(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a JSON archive of the user's personal data."""
    uid = str(user["id"])
    tid = str(user["tenant_id"])

    # Collect user record
    u_row = (await db.execute(
        text("SELECT id, email, full_name, created_at FROM users WHERE id = :uid"),
        {"uid": uid},
    )).first()

    # Collect audit actions by this user
    audits = (await db.execute(
        text("SELECT action, entity_type, entity_id, created_at FROM audit_logs WHERE user_id = :uid ORDER BY created_at DESC LIMIT 500"),
        {"uid": uid},
    )).fetchall()

    # Collect notifications
    notifs = (await db.execute(
        text("SELECT title, message, event_type, created_at, read FROM notifications WHERE user_id = :uid ORDER BY created_at DESC"),
        {"uid": uid},
    )).fetchall()

    return {
        "user": {
            "id": str(u_row.id) if u_row else uid,
            "email": u_row.email if u_row else user.get("email"),
            "full_name": u_row.full_name if u_row else user.get("full_name"),
            "created_at": str(u_row.created_at) if u_row and u_row.created_at else None,
        },
        "audit_actions": [
            {"action": a.action, "entity_type": a.entity_type,
             "entity_id": a.entity_id, "created_at": str(a.created_at) if a.created_at else None}
            for a in audits
        ],
        "notifications": [
            {"title": n.title, "message": n.message, "event_type": n.event_type,
             "read": n.read, "created_at": str(n.created_at) if n.created_at else None}
            for n in notifs
        ],
    }


@router.post("/delete-request")
async def request_deletion(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Flag the user's account for deletion. A human process completes the actual deletion."""
    uid = str(user["id"])

    await db.execute(
        text("UPDATE users SET is_active = false, updated_at = now() WHERE id = :uid"),
        {"uid": uid},
    )

    # Log the request in audit
    from app.core.audit import log_audit
    await log_audit(
        db, user["tenant_id"], uuid.UUID(uid), user.get("email"),
        action="gdpr_delete_request", entity_type="user", entity_id=uid,
    )
    await db.commit()

    return {"status": "deletion_requested", "message": "Votre demande de suppression a ete enregistree."}
