from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.settings import settings

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    payload = decode_token(creds.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")
    from app.modules.auth.router import _get_user_by_id

    user = await _get_user_by_id(db, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    user["role"] = payload.get("role", "")
    user["tenant_id"] = uuid.UUID(payload["tid"])
    return user


def require_permission(*perms: str):
    """Dependency factory that checks the user has at least one of the given permissions."""

    async def checker(
        current_user: dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        role = current_user.get("role", "")
        if role == "admin":
            return current_user  # admin has all permissions

        # Load role permissions from DB
        tenant_id = str(current_user.get("tenant_id", ""))
        from sqlalchemy import text as sa_text
        result = await db.execute(
            sa_text("SELECT permissions FROM roles WHERE tenant_id = :tid AND name = :name"),
            {"tid": tenant_id, "name": role},
        )
        row = result.first()
        if row:
            role_perms = row.permissions or []
            if isinstance(role_perms, str):
                import json
                role_perms = json.loads(role_perms)
            # Check wildcards and exact matches
            if "*" in role_perms or any(p in role_perms for p in perms):
                return current_user

        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")

    return Depends(checker)
