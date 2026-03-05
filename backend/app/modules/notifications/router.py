"""Notifications API — user's own notifications, mark as read."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: str
    title: str
    message: str | None = None
    link: str | None = None
    event_type: str | None = None
    read: bool = False
    created_at: str | None = None


class UnreadCount(BaseModel):
    unread: int


def _notif_from_row(r) -> NotificationOut:
    return NotificationOut(
        id=str(r.id), title=r.title, message=r.message,
        link=r.link, event_type=r.event_type, read=r.read,
        created_at=str(r.created_at) if r.created_at else None,
    )


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    read: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    uid = str(user["id"])
    q = "SELECT * FROM notifications WHERE user_id = :uid"
    params: dict = {"uid": uid}
    if read is not None:
        q += " AND read = :read"
        params["read"] = read
    q += " ORDER BY created_at DESC LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = (await db.execute(text(q), params)).fetchall()
    return [_notif_from_row(r) for r in rows]


@router.get("/count", response_model=UnreadCount)
async def unread_count(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = str(user["id"])
    row = (await db.execute(
        text("SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = :uid AND read = false"),
        {"uid": uid},
    )).first()
    return UnreadCount(unread=row.cnt if row else 0)


@router.patch("/{notif_id}/read", response_model=NotificationOut)
async def mark_read(
    notif_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = str(user["id"])
    result = await db.execute(text("""
        UPDATE notifications SET read = true
        WHERE id = :id AND user_id = :uid RETURNING *
    """), {"id": notif_id, "uid": uid})
    row = result.first()
    if not row:
        raise HTTPException(404, "Notification non trouvee")
    await db.commit()
    return _notif_from_row(row)


@router.post("/read-all", status_code=200)
async def mark_all_read(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = str(user["id"])
    result = await db.execute(
        text("UPDATE notifications SET read = true WHERE user_id = :uid AND read = false"),
        {"uid": uid},
    )
    await db.commit()
    return {"updated": result.rowcount}
