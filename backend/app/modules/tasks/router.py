from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


class TaskOut(BaseModel):
    id: str
    category: str
    title: str
    entity_type: str | None = None
    entity_id: str | None = None
    assigned_to: str | None = None
    due_date: str | None = None
    status: str
    created_at: str | None = None


class TaskUpdateRequest(BaseModel):
    status: str  # open | in_progress | resolved | dismissed
    assigned_to: str | None = None


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    q = "SELECT * FROM tasks WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if status:
        q += " AND status = :status"
        params["status"] = status
    if category:
        q += " AND category = :cat"
        params["cat"] = category
    q += " ORDER BY CASE WHEN status = 'open' THEN 0 WHEN status = 'in_progress' THEN 1 ELSE 2 END, due_date ASC NULLS LAST LIMIT :lim"
    params["lim"] = limit

    rows = await db.execute(text(q), params)
    return [TaskOut(
        id=str(r.id), category=r.category, title=r.title,
        entity_type=r.entity_type, entity_id=r.entity_id,
        assigned_to=str(r.assigned_to) if r.assigned_to else None,
        due_date=str(r.due_date) if r.due_date else None,
        status=r.status,
        created_at=str(r.created_at) if r.created_at else None,
    ) for r in rows.fetchall()]


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str,
    body: TaskUpdateRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resolved_at = "NOW()" if body.status in ("resolved", "dismissed") else "NULL"
    result = await db.execute(text(f"""
        UPDATE tasks SET status=:status, assigned_to=:assigned,
            resolved_at={resolved_at}
        WHERE id=:id AND tenant_id=:tid
        RETURNING *
    """), {"id": task_id, "tid": str(tenant.tenant_id),
           "status": body.status, "assigned": body.assigned_to})
    row = result.first()
    if not row:
        raise HTTPException(404, "Task not found")
    await db.commit()
    return TaskOut(
        id=str(row.id), category=row.category, title=row.title,
        entity_type=row.entity_type, entity_id=row.entity_id,
        assigned_to=str(row.assigned_to) if row.assigned_to else None,
        due_date=str(row.due_date) if row.due_date else None,
        status=row.status,
        created_at=str(row.created_at) if row.created_at else None,
    )
