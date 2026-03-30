from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.seed import seed
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])


class OnboardingStatus(BaseModel):
    has_customers: bool
    has_drivers: bool
    has_vehicles: bool
    has_document_types: bool
    has_pricing_rules: bool
    has_payroll_types: bool


class DemoSetupResponse(BaseModel):
    status: str
    message: str


@router.get("/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    tid = str(tenant.tenant_id)

    async def has_rows(table: str) -> bool:
        r = await db.execute(text(f"SELECT 1 FROM {table} WHERE tenant_id = :tid LIMIT 1"), {"tid": tid})
        return r.first() is not None

    return OnboardingStatus(
        has_customers=await has_rows("customers"),
        has_drivers=await has_rows("drivers"),
        has_vehicles=await has_rows("vehicles"),
        has_document_types=await has_rows("document_types"),
        has_pricing_rules=await has_rows("pricing_rules"),
        has_payroll_types=await has_rows("payroll_variable_types"),
    )


@router.post("/demo-setup", response_model=DemoSetupResponse)
async def demo_setup(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seed the tenant with demo data (drivers, customer, FR presets)."""
    await seed(db)
    return DemoSetupResponse(status="ok", message="Demo data seeded successfully")


@router.post("/fix-compliance-duplicates")
async def fix_compliance_duplicates(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove duplicate compliance_templates and add unique constraint."""
    from sqlalchemy import text
    result = await db.execute(text("""
        DELETE FROM compliance_templates
        WHERE id NOT IN (
            SELECT DISTINCT ON (tenant_id, entity_type, type_document) id
            FROM compliance_templates
            ORDER BY tenant_id, entity_type, type_document, created_at ASC
        )
    """))
    deleted = result.rowcount
    try:
        await db.execute(text("""
            ALTER TABLE compliance_templates
            ADD CONSTRAINT uq_compliance_templates_tenant_entity_doctype
            UNIQUE (tenant_id, entity_type, type_document)
        """))
        constraint_added = True
    except Exception:
        constraint_added = False
    await db.commit()
    return {"deleted_duplicates": deleted, "constraint_added": constraint_added}
