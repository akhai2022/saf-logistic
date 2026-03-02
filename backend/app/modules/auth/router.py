from __future__ import annotations

import json
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

# ── Role → sidebar sections mapping ──────────────────────────────

SIDEBAR_BY_ROLE: dict[str, list[str]] = {
    "admin": ["exploitation", "referentiels", "finance", "flotte", "pilotage"],
    "exploitation": ["exploitation", "referentiels"],
    "compta": ["exploitation", "finance", "pilotage"],
    "flotte": ["referentiels", "flotte"],
    "rh_paie": ["exploitation", "referentiels", "finance"],
    "lecture_seule": ["exploitation", "referentiels", "finance", "flotte", "pilotage"],
    "soustraitant": ["exploitation"],
}

KPI_KEYS_BY_ROLE: dict[str, list[str]] = {
    "admin": ["ca_mensuel", "marge", "taux_conformite", "dso", "cout_km", "missions_en_cours", "litiges_ouverts"],
    "exploitation": ["missions_en_cours", "pod_delai", "taux_cloture_j1", "litiges_ouverts"],
    "compta": ["dso", "balance_agee", "nb_factures_impayees", "ecarts_soustraitants"],
    "rh_paie": ["delai_prepaie", "anomalies", "taux_correction", "conformite_conducteurs"],
    "flotte": ["taux_conformite_vehicules", "cout_km", "pannes_non_planifiees", "maintenances_a_venir"],
    "lecture_seule": ["ca_mensuel", "missions_en_cours", "taux_conformite"],
    "soustraitant": ["missions_en_cours"],
}


# ── Schemas ───────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_id: str


class TenantInfo(BaseModel):
    id: str
    name: str
    siren: str | None = None
    modules_enabled: list[str] = []


class AgencyInfo(BaseModel):
    id: str
    name: str
    code: str | None = None


class PermissionsInfo(BaseModel):
    role_name: str
    permissions: list[str] = []


class DashboardConfig(BaseModel):
    kpi_keys: list[str] = []
    sidebar_sections: list[str] = []


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    tenant: TenantInfo | None = None
    agency: AgencyInfo | None = None
    permissions: PermissionsInfo | None = None
    dashboard_config: DashboardConfig | None = None


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    tenant_id: str


# ── Helpers ───────────────────────────────────────────────────────

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


# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("""
            SELECT u.id, u.email, u.password_hash, u.is_active, u.tenant_id,
                   u.agency_id, r.name AS role_name, r.permissions AS role_permissions
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

    role_name = row.role_name or ""
    token = create_access_token(row.id, row.tenant_id, role_name)

    # Fetch tenant info
    tenant_info = None
    t_row = (await db.execute(
        text("SELECT id, name, siren FROM tenants WHERE id = :tid"),
        {"tid": body.tenant_id},
    )).first()
    if t_row:
        modules = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
        tenant_info = TenantInfo(
            id=str(t_row.id), name=t_row.name,
            siren=t_row.siren, modules_enabled=modules,
        )

    # Fetch agency info
    agency_info = None
    if row.agency_id:
        a_row = (await db.execute(
            text("SELECT id, name, code FROM agencies WHERE id = :aid"),
            {"aid": str(row.agency_id)},
        )).first()
        if a_row:
            agency_info = AgencyInfo(id=str(a_row.id), name=a_row.name, code=a_row.code)

    # Parse permissions
    perms_list = []
    if row.role_permissions:
        rp = row.role_permissions
        if isinstance(rp, str):
            rp = json.loads(rp)
        if isinstance(rp, list):
            perms_list = rp

    permissions_info = PermissionsInfo(role_name=role_name, permissions=perms_list)

    # Dashboard config
    kpi_keys = KPI_KEYS_BY_ROLE.get(role_name, [])
    sidebar = SIDEBAR_BY_ROLE.get(role_name, ["exploitation", "referentiels"])
    dashboard_config = DashboardConfig(kpi_keys=kpi_keys, sidebar_sections=sidebar)

    return LoginResponse(
        access_token=token,
        user_id=str(row.id),
        role=role_name,
        tenant=tenant_info,
        agency=agency_info,
        permissions=permissions_info,
        dashboard_config=dashboard_config,
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
