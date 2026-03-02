"""Admin router — Super Admin (cross-tenant) + Tenant Admin (scoped) endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    get_current_user,
    hash_password,
    require_admin,
    require_super_admin,
)
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/admin", tags=["admin"])


# ── Schemas ────────────────────────────────────────────────────────


class CreateTenantRequest(BaseModel):
    name: str
    siren: str | None = None
    address: str | None = None
    admin_email: str
    admin_password: str
    admin_full_name: str
    agency_name: str = "Agence principale"
    agency_code: str = "HQ"


class UpdateTenantRequest(BaseModel):
    name: str | None = None
    siren: str | None = None
    address: str | None = None


class CreateUserRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role_id: str
    agency_id: str


class UpdateUserRequest(BaseModel):
    email: str | None = None
    full_name: str | None = None
    role_id: str | None = None
    agency_id: str | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str


# ═══════════════════════════════════════════════════════════════════
#  SUPER ADMIN ENDPOINTS (cross-tenant)
# ═══════════════════════════════════════════════════════════════════


@router.get("/tenants")
async def list_tenants(
    sa_user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        SELECT t.id, t.name, t.siren, t.address, t.created_at,
               COUNT(u.id) AS user_count
        FROM tenants t
        LEFT JOIN users u ON u.tenant_id = t.id
        GROUP BY t.id
        ORDER BY t.created_at DESC
    """))
    rows = result.all()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "siren": r.siren,
            "address": r.address,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "user_count": r.user_count,
        }
        for r in rows
    ]


@router.post("/tenants", status_code=201)
async def create_tenant(
    body: CreateTenantRequest,
    sa_user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.core.seed import ROLES

    tenant_id = uuid.uuid4()
    agency_id = uuid.uuid4()

    # Create tenant
    await db.execute(
        text("""
            INSERT INTO tenants (id, name, siren, address)
            VALUES (:id, :name, :siren, :address)
        """),
        {"id": str(tenant_id), "name": body.name, "siren": body.siren, "address": body.address},
    )

    # Create default agency
    await db.execute(
        text("""
            INSERT INTO agencies (id, tenant_id, name, code)
            VALUES (:id, :tid, :name, :code)
        """),
        {"id": str(agency_id), "tid": str(tenant_id), "name": body.agency_name, "code": body.agency_code},
    )

    # Seed all default roles
    role_ids: dict[str, uuid.UUID] = {}
    for role_name, perms in ROLES:
        rid = uuid.uuid4()
        result = await db.execute(
            text("""
                INSERT INTO roles (id, tenant_id, name, permissions)
                VALUES (:id, :tid, :name, CAST(:perms AS jsonb))
                RETURNING id
            """),
            {"id": str(rid), "tid": str(tenant_id), "name": role_name, "perms": json.dumps(perms)},
        )
        role_ids[role_name] = result.scalar()

    # Create admin user
    admin_id = uuid.uuid4()
    await db.execute(
        text("""
            INSERT INTO users (id, tenant_id, agency_id, email, password_hash, full_name, role_id)
            VALUES (:id, :tid, :aid, :email, :pwd, :name, :rid)
        """),
        {
            "id": str(admin_id),
            "tid": str(tenant_id),
            "aid": str(agency_id),
            "email": body.admin_email,
            "pwd": hash_password(body.admin_password),
            "name": body.admin_full_name,
            "rid": str(role_ids["admin"]),
        },
    )

    await db.commit()
    return {
        "id": str(tenant_id),
        "name": body.name,
        "agency_id": str(agency_id),
        "admin_user_id": str(admin_id),
    }


@router.get("/tenants/{tenant_id}")
async def get_tenant_detail(
    tenant_id: str,
    sa_user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    t_row = (await db.execute(
        text("SELECT id, name, siren, address, created_at FROM tenants WHERE id = :tid"),
        {"tid": tenant_id},
    )).first()
    if not t_row:
        raise HTTPException(404, "Tenant not found")

    agencies = (await db.execute(
        text("SELECT id, name, code FROM agencies WHERE tenant_id = :tid ORDER BY name"),
        {"tid": tenant_id},
    )).all()

    return {
        "id": str(t_row.id),
        "name": t_row.name,
        "siren": t_row.siren,
        "address": t_row.address,
        "created_at": t_row.created_at.isoformat() if t_row.created_at else None,
        "agencies": [
            {"id": str(a.id), "name": a.name, "code": a.code} for a in agencies
        ],
    }


@router.put("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    body: UpdateTenantRequest,
    sa_user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    sets: list[str] = []
    params: dict[str, Any] = {"tid": tenant_id}
    if body.name is not None:
        sets.append("name = :name")
        params["name"] = body.name
    if body.siren is not None:
        sets.append("siren = :siren")
        params["siren"] = body.siren
    if body.address is not None:
        sets.append("address = :address")
        params["address"] = body.address
    if not sets:
        raise HTTPException(422, "Nothing to update")

    sets.append("updated_at = NOW()")
    await db.execute(
        text(f"UPDATE tenants SET {', '.join(sets)} WHERE id = :tid"),
        params,
    )
    await db.commit()
    return {"ok": True}


@router.get("/tenants/{tenant_id}/users")
async def list_tenant_users(
    tenant_id: str,
    sa_user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT u.id, u.email, u.full_name, u.is_active, u.created_at,
                   r.name AS role_name, a.name AS agency_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN agencies a ON u.agency_id = a.id
            WHERE u.tenant_id = :tid
            ORDER BY u.created_at DESC
        """),
        {"tid": tenant_id},
    )
    return [
        {
            "id": str(r.id),
            "email": r.email,
            "full_name": r.full_name,
            "is_active": r.is_active,
            "role_name": r.role_name,
            "agency_name": r.agency_name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in result.all()
    ]


# ═══════════════════════════════════════════════════════════════════
#  TENANT ADMIN ENDPOINTS (tenant-scoped)
# ═══════════════════════════════════════════════════════════════════


@router.get("/users")
async def list_users(
    q: str = Query("", description="Search term"),
    admin_user: dict = Depends(require_admin),
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    if q:
        result = await db.execute(
            text("""
                SELECT u.id, u.email, u.full_name, u.is_active, u.created_at,
                       r.name AS role_name, r.id AS role_id,
                       a.name AS agency_name, a.id AS agency_id
                FROM users u
                LEFT JOIN roles r ON u.role_id = r.id
                LEFT JOIN agencies a ON u.agency_id = a.id
                WHERE u.tenant_id = :tid
                  AND (u.email ILIKE :q OR u.full_name ILIKE :q)
                ORDER BY u.created_at DESC
            """),
            {"tid": tid, "q": f"%{q}%"},
        )
    else:
        result = await db.execute(
            text("""
                SELECT u.id, u.email, u.full_name, u.is_active, u.created_at,
                       r.name AS role_name, r.id AS role_id,
                       a.name AS agency_name, a.id AS agency_id
                FROM users u
                LEFT JOIN roles r ON u.role_id = r.id
                LEFT JOIN agencies a ON u.agency_id = a.id
                WHERE u.tenant_id = :tid
                ORDER BY u.created_at DESC
            """),
            {"tid": tid},
        )
    return [
        {
            "id": str(r.id),
            "email": r.email,
            "full_name": r.full_name,
            "is_active": r.is_active,
            "role_name": r.role_name,
            "role_id": str(r.role_id) if r.role_id else None,
            "agency_name": r.agency_name,
            "agency_id": str(r.agency_id) if r.agency_id else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in result.all()
    ]


@router.post("/users", status_code=201)
async def create_user(
    body: CreateUserRequest,
    admin_user: dict = Depends(require_admin),
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    if len(body.password) < 8:
        raise HTTPException(422, "Le mot de passe doit contenir au moins 8 caracteres")

    # Check email uniqueness within tenant
    existing = (await db.execute(
        text("SELECT id FROM users WHERE email = :email AND tenant_id = :tid"),
        {"email": body.email, "tid": tid},
    )).first()
    if existing:
        raise HTTPException(409, "Un utilisateur avec cet email existe deja")

    uid = uuid.uuid4()
    await db.execute(
        text("""
            INSERT INTO users (id, tenant_id, agency_id, email, password_hash, full_name, role_id)
            VALUES (:id, :tid, :aid, :email, :pwd, :name, :rid)
        """),
        {
            "id": str(uid),
            "tid": tid,
            "aid": body.agency_id,
            "email": body.email,
            "pwd": hash_password(body.password),
            "name": body.full_name,
            "rid": body.role_id,
        },
    )
    await db.commit()
    return {"id": str(uid), "email": body.email, "full_name": body.full_name}


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    admin_user: dict = Depends(require_admin),
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    row = (await db.execute(
        text("""
            SELECT u.id, u.email, u.full_name, u.is_active, u.created_at,
                   r.name AS role_name, r.id AS role_id,
                   a.name AS agency_name, a.id AS agency_id
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN agencies a ON u.agency_id = a.id
            WHERE u.id = :uid AND u.tenant_id = :tid
        """),
        {"uid": user_id, "tid": tid},
    )).first()
    if not row:
        raise HTTPException(404, "User not found")
    return {
        "id": str(row.id),
        "email": row.email,
        "full_name": row.full_name,
        "is_active": row.is_active,
        "role_name": row.role_name,
        "role_id": str(row.role_id) if row.role_id else None,
        "agency_name": row.agency_name,
        "agency_id": str(row.agency_id) if row.agency_id else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    admin_user: dict = Depends(require_admin),
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)

    # Safety: admin cannot deactivate themselves
    if body.is_active is False and user_id == admin_user["id"]:
        raise HTTPException(400, "Vous ne pouvez pas desactiver votre propre compte")

    # Check user belongs to tenant
    existing = (await db.execute(
        text("SELECT id FROM users WHERE id = :uid AND tenant_id = :tid"),
        {"uid": user_id, "tid": tid},
    )).first()
    if not existing:
        raise HTTPException(404, "User not found")

    sets: list[str] = []
    params: dict[str, Any] = {"uid": user_id, "tid": tid}
    if body.email is not None:
        sets.append("email = :email")
        params["email"] = body.email
    if body.full_name is not None:
        sets.append("full_name = :full_name")
        params["full_name"] = body.full_name
    if body.role_id is not None:
        sets.append("role_id = :role_id")
        params["role_id"] = body.role_id
    if body.agency_id is not None:
        sets.append("agency_id = :agency_id")
        params["agency_id"] = body.agency_id
    if body.is_active is not None:
        sets.append("is_active = :is_active")
        params["is_active"] = body.is_active
    if not sets:
        raise HTTPException(422, "Nothing to update")

    sets.append("updated_at = NOW()")
    await db.execute(
        text(f"UPDATE users SET {', '.join(sets)} WHERE id = :uid AND tenant_id = :tid"),
        params,
    )
    await db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    body: ResetPasswordRequest,
    admin_user: dict = Depends(require_admin),
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    if len(body.new_password) < 8:
        raise HTTPException(422, "Le mot de passe doit contenir au moins 8 caracteres")

    existing = (await db.execute(
        text("SELECT id FROM users WHERE id = :uid AND tenant_id = :tid"),
        {"uid": user_id, "tid": tid},
    )).first()
    if not existing:
        raise HTTPException(404, "User not found")

    await db.execute(
        text("UPDATE users SET password_hash = :pwd, updated_at = NOW() WHERE id = :uid"),
        {"pwd": hash_password(body.new_password), "uid": user_id},
    )
    await db.commit()
    return {"ok": True}


@router.get("/roles")
async def list_roles(
    admin_user: dict = Depends(require_admin),
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, name FROM roles WHERE tenant_id = :tid ORDER BY name"),
        {"tid": str(tenant.tenant_id)},
    )
    return [{"id": str(r.id), "name": r.name} for r in result.all()]


@router.get("/agencies")
async def list_agencies(
    admin_user: dict = Depends(require_admin),
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, name, code FROM agencies WHERE tenant_id = :tid ORDER BY name"),
        {"tid": str(tenant.tenant_id)},
    )
    return [{"id": str(r.id), "name": r.name, "code": r.code} for r in result.all()]
