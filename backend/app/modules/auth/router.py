from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_id: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    tenant_id: str


async def _get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> dict | None:
    result = await db.execute(
        text("""
            SELECT u.id, u.email, u.full_name, u.tenant_id, u.password_hash, u.is_active,
                   r.name AS role_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.id = :uid
        """),
        {"uid": str(user_id)},
    )
    row = result.first()
    if not row:
        return None
    return {
        "id": str(row.id),
        "email": row.email,
        "full_name": row.full_name,
        "tenant_id": str(row.tenant_id),
        "password_hash": row.password_hash,
        "is_active": row.is_active,
        "role": row.role_name or "",
    }


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("""
            SELECT u.id, u.email, u.password_hash, u.is_active, u.tenant_id,
                   r.name AS role_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.email = :email AND u.tenant_id = :tid
        """),
        {"email": body.email, "tid": body.tenant_id},
    )
    row = result.first()
    if not row or not verify_password(body.password, row.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not row.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")

    token = create_access_token(row.id, row.tenant_id, row.role_name or "")
    return LoginResponse(
        access_token=token,
        user_id=str(row.id),
        role=row.role_name or "",
    )


@router.get("/me", response_model=MeResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return MeResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        role=current_user.get("role", ""),
        tenant_id=str(current_user["tenant_id"]),
    )
