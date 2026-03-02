"""Settings router — company info, bank accounts, VAT, cost centers, notification configs."""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import require_permission
from app.core.tenant import TenantContext, get_tenant
from app.core.validators import (
    validate_code_postal,
    validate_iban,
    validate_siren,
    validate_siret,
    validate_tva_intracom,
)

router = APIRouter(prefix="/v1/settings", tags=["settings"])


# ══════════════════════════════════════════════════════════════════
# COMPANY SETTINGS
# ══════════════════════════════════════════════════════════════════

class CompanySettingsIn(BaseModel):
    siren: str | None = None
    siret: str | None = None
    tva_intracom: str | None = None
    raison_sociale: str | None = None
    adresse_ligne1: str | None = None
    adresse_ligne2: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    pays: str = "FR"
    telephone: str | None = None
    email: str | None = None
    site_web: str | None = None
    licence_transport: str | None = None


class CompanySettingsOut(CompanySettingsIn):
    id: str
    tenant_id: str
    created_at: str | None = None
    updated_at: str | None = None


def _validate_company(body: CompanySettingsIn) -> None:
    if body.siren and not validate_siren(body.siren):
        raise HTTPException(422, "SIREN invalide")
    if body.siret and not validate_siret(body.siret):
        raise HTTPException(422, "SIRET invalide")
    if body.tva_intracom and not validate_tva_intracom(body.tva_intracom):
        raise HTTPException(422, "Numero de TVA intracommunautaire invalide")
    if body.code_postal and not validate_code_postal(body.code_postal):
        raise HTTPException(422, "Code postal invalide")


@router.get("/company", response_model=CompanySettingsOut | None)
async def get_company(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.read"),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT * FROM company_settings WHERE tenant_id = :tid"),
        {"tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        return None
    return CompanySettingsOut(
        id=str(row.id), tenant_id=str(row.tenant_id),
        siren=row.siren, siret=row.siret, tva_intracom=row.tva_intracom,
        raison_sociale=row.raison_sociale,
        adresse_ligne1=row.adresse_ligne1, adresse_ligne2=row.adresse_ligne2,
        code_postal=row.code_postal, ville=row.ville, pays=row.pays,
        telephone=row.telephone, email=row.email, site_web=row.site_web,
        licence_transport=row.licence_transport,
        created_at=str(row.created_at) if row.created_at else None,
        updated_at=str(row.updated_at) if row.updated_at else None,
    )


@router.put("/company", response_model=CompanySettingsOut)
async def upsert_company(
    body: CompanySettingsIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    _validate_company(body)
    tid = str(tenant.tenant_id)
    sid = str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO company_settings (id, tenant_id, siren, siret, tva_intracom,
            raison_sociale, adresse_ligne1, adresse_ligne2, code_postal, ville, pays,
            telephone, email, site_web, licence_transport)
        VALUES (:id, :tid, :siren, :siret, :tva, :rs, :al1, :al2, :cp, :ville, :pays,
                :tel, :email, :web, :lic)
        ON CONFLICT ON CONSTRAINT uq_company_settings_tenant
        DO UPDATE SET
            siren = :siren, siret = :siret, tva_intracom = :tva,
            raison_sociale = :rs, adresse_ligne1 = :al1, adresse_ligne2 = :al2,
            code_postal = :cp, ville = :ville, pays = :pays,
            telephone = :tel, email = :email, site_web = :web,
            licence_transport = :lic, updated_at = now()
    """), {
        "id": sid, "tid": tid, "siren": body.siren, "siret": body.siret,
        "tva": body.tva_intracom, "rs": body.raison_sociale,
        "al1": body.adresse_ligne1, "al2": body.adresse_ligne2,
        "cp": body.code_postal, "ville": body.ville, "pays": body.pays,
        "tel": body.telephone, "email": body.email, "web": body.site_web,
        "lic": body.licence_transport,
    })
    await db.commit()

    row = (await db.execute(
        text("SELECT * FROM company_settings WHERE tenant_id = :tid"), {"tid": tid}
    )).first()
    return CompanySettingsOut(
        id=str(row.id), tenant_id=str(row.tenant_id),
        siren=row.siren, siret=row.siret, tva_intracom=row.tva_intracom,
        raison_sociale=row.raison_sociale,
        adresse_ligne1=row.adresse_ligne1, adresse_ligne2=row.adresse_ligne2,
        code_postal=row.code_postal, ville=row.ville, pays=row.pays,
        telephone=row.telephone, email=row.email, site_web=row.site_web,
        licence_transport=row.licence_transport,
        created_at=str(row.created_at) if row.created_at else None,
        updated_at=str(row.updated_at) if row.updated_at else None,
    )


# ══════════════════════════════════════════════════════════════════
# BANK ACCOUNTS
# ══════════════════════════════════════════════════════════════════

class BankAccountIn(BaseModel):
    label: str
    iban: str
    bic: str | None = None
    bank_name: str | None = None
    is_default: bool = False


class BankAccountOut(BankAccountIn):
    id: str
    created_at: str | None = None


def _bank_from_row(r) -> BankAccountOut:
    return BankAccountOut(
        id=str(r.id), label=r.label, iban=r.iban, bic=r.bic,
        bank_name=r.bank_name, is_default=r.is_default,
        created_at=str(r.created_at) if r.created_at else None,
    )


@router.get("/bank-accounts", response_model=list[BankAccountOut])
async def list_bank_accounts(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.read"),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        text("SELECT * FROM bank_accounts WHERE tenant_id = :tid ORDER BY is_default DESC, label"),
        {"tid": str(tenant.tenant_id)},
    )).fetchall()
    return [_bank_from_row(r) for r in rows]


@router.post("/bank-accounts", response_model=BankAccountOut, status_code=201)
async def create_bank_account(
    body: BankAccountIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    if not validate_iban(body.iban):
        raise HTTPException(422, "IBAN invalide")
    tid = str(tenant.tenant_id)
    bid = uuid.uuid4()

    if body.is_default:
        await db.execute(
            text("UPDATE bank_accounts SET is_default = false WHERE tenant_id = :tid"),
            {"tid": tid},
        )

    await db.execute(text("""
        INSERT INTO bank_accounts (id, tenant_id, label, iban, bic, bank_name, is_default)
        VALUES (:id, :tid, :label, :iban, :bic, :bank, :def)
    """), {
        "id": str(bid), "tid": tid, "label": body.label, "iban": body.iban,
        "bic": body.bic, "bank": body.bank_name, "def": body.is_default,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM bank_accounts WHERE id = :id"), {"id": str(bid)})).first()
    return _bank_from_row(row)


@router.put("/bank-accounts/{ba_id}", response_model=BankAccountOut)
async def update_bank_account(
    ba_id: str,
    body: BankAccountIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    if not validate_iban(body.iban):
        raise HTTPException(422, "IBAN invalide")
    tid = str(tenant.tenant_id)

    if body.is_default:
        await db.execute(
            text("UPDATE bank_accounts SET is_default = false WHERE tenant_id = :tid"),
            {"tid": tid},
        )

    result = await db.execute(text("""
        UPDATE bank_accounts SET label=:label, iban=:iban, bic=:bic, bank_name=:bank,
            is_default=:def, updated_at=now()
        WHERE id=:id AND tenant_id=:tid RETURNING id
    """), {
        "id": ba_id, "tid": tid, "label": body.label, "iban": body.iban,
        "bic": body.bic, "bank": body.bank_name, "def": body.is_default,
    })
    if not result.first():
        raise HTTPException(404, "Compte bancaire non trouve")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM bank_accounts WHERE id = :id"), {"id": ba_id})).first()
    return _bank_from_row(row)


@router.delete("/bank-accounts/{ba_id}", status_code=204)
async def delete_bank_account(
    ba_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("DELETE FROM bank_accounts WHERE id = :id AND tenant_id = :tid RETURNING id"),
        {"id": ba_id, "tid": str(tenant.tenant_id)},
    )
    if not result.first():
        raise HTTPException(404, "Compte bancaire non trouve")
    await db.commit()


# ══════════════════════════════════════════════════════════════════
# VAT CONFIGS
# ══════════════════════════════════════════════════════════════════

class VatConfigIn(BaseModel):
    rate: float
    label: str
    mention_legale: str | None = None
    is_default: bool = False
    is_active: bool = True


class VatConfigOut(VatConfigIn):
    id: str
    created_at: str | None = None


def _vat_from_row(r) -> VatConfigOut:
    return VatConfigOut(
        id=str(r.id), rate=float(r.rate), label=r.label,
        mention_legale=r.mention_legale, is_default=r.is_default,
        is_active=r.is_active,
        created_at=str(r.created_at) if r.created_at else None,
    )


@router.get("/vat", response_model=list[VatConfigOut])
async def list_vat_configs(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.read"),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        text("SELECT * FROM vat_configs WHERE tenant_id = :tid ORDER BY rate"),
        {"tid": str(tenant.tenant_id)},
    )).fetchall()
    return [_vat_from_row(r) for r in rows]


@router.post("/vat", response_model=VatConfigOut, status_code=201)
async def create_vat_config(
    body: VatConfigIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    vid = uuid.uuid4()
    if body.is_default:
        await db.execute(
            text("UPDATE vat_configs SET is_default = false WHERE tenant_id = :tid"),
            {"tid": tid},
        )
    await db.execute(text("""
        INSERT INTO vat_configs (id, tenant_id, rate, label, mention_legale, is_default, is_active)
        VALUES (:id, :tid, :rate, :label, :mention, :def, :active)
    """), {
        "id": str(vid), "tid": tid, "rate": body.rate, "label": body.label,
        "mention": body.mention_legale, "def": body.is_default, "active": body.is_active,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vat_configs WHERE id = :id"), {"id": str(vid)})).first()
    return _vat_from_row(row)


@router.put("/vat/{vat_id}", response_model=VatConfigOut)
async def update_vat_config(
    vat_id: str,
    body: VatConfigIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    if body.is_default:
        await db.execute(
            text("UPDATE vat_configs SET is_default = false WHERE tenant_id = :tid"),
            {"tid": tid},
        )
    result = await db.execute(text("""
        UPDATE vat_configs SET rate=:rate, label=:label, mention_legale=:mention,
            is_default=:def, is_active=:active, updated_at=now()
        WHERE id=:id AND tenant_id=:tid RETURNING id
    """), {
        "id": vat_id, "tid": tid, "rate": body.rate, "label": body.label,
        "mention": body.mention_legale, "def": body.is_default, "active": body.is_active,
    })
    if not result.first():
        raise HTTPException(404, "Configuration TVA non trouvee")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vat_configs WHERE id = :id"), {"id": vat_id})).first()
    return _vat_from_row(row)


@router.delete("/vat/{vat_id}", status_code=204)
async def delete_vat_config(
    vat_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("DELETE FROM vat_configs WHERE id = :id AND tenant_id = :tid RETURNING id"),
        {"id": vat_id, "tid": str(tenant.tenant_id)},
    )
    if not result.first():
        raise HTTPException(404, "Configuration TVA non trouvee")
    await db.commit()


# ══════════════════════════════════════════════════════════════════
# COST CENTERS
# ══════════════════════════════════════════════════════════════════

class CostCenterIn(BaseModel):
    code: str
    label: str
    is_active: bool = True


class CostCenterOut(CostCenterIn):
    id: str
    created_at: str | None = None


def _cc_from_row(r) -> CostCenterOut:
    return CostCenterOut(
        id=str(r.id), code=r.code, label=r.label, is_active=r.is_active,
        created_at=str(r.created_at) if r.created_at else None,
    )


@router.get("/cost-centers", response_model=list[CostCenterOut])
async def list_cost_centers(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.read"),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        text("SELECT * FROM cost_centers WHERE tenant_id = :tid ORDER BY code"),
        {"tid": str(tenant.tenant_id)},
    )).fetchall()
    return [_cc_from_row(r) for r in rows]


@router.post("/cost-centers", response_model=CostCenterOut, status_code=201)
async def create_cost_center(
    body: CostCenterIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    cid = uuid.uuid4()
    existing = (await db.execute(
        text("SELECT id FROM cost_centers WHERE tenant_id = :tid AND code = :code"),
        {"tid": tid, "code": body.code},
    )).first()
    if existing:
        raise HTTPException(409, "Ce code de centre de couts existe deja")
    await db.execute(text("""
        INSERT INTO cost_centers (id, tenant_id, code, label, is_active)
        VALUES (:id, :tid, :code, :label, :active)
    """), {"id": str(cid), "tid": tid, "code": body.code, "label": body.label, "active": body.is_active})
    await db.commit()
    row = (await db.execute(text("SELECT * FROM cost_centers WHERE id = :id"), {"id": str(cid)})).first()
    return _cc_from_row(row)


@router.put("/cost-centers/{cc_id}", response_model=CostCenterOut)
async def update_cost_center(
    cc_id: str,
    body: CostCenterIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    result = await db.execute(text("""
        UPDATE cost_centers SET code=:code, label=:label, is_active=:active, updated_at=now()
        WHERE id=:id AND tenant_id=:tid RETURNING id
    """), {"id": cc_id, "tid": tid, "code": body.code, "label": body.label, "active": body.is_active})
    if not result.first():
        raise HTTPException(404, "Centre de couts non trouve")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM cost_centers WHERE id = :id"), {"id": cc_id})).first()
    return _cc_from_row(row)


@router.delete("/cost-centers/{cc_id}", status_code=204)
async def delete_cost_center(
    cc_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("DELETE FROM cost_centers WHERE id = :id AND tenant_id = :tid RETURNING id"),
        {"id": cc_id, "tid": str(tenant.tenant_id)},
    )
    if not result.first():
        raise HTTPException(404, "Centre de couts non trouve")
    await db.commit()


# ══════════════════════════════════════════════════════════════════
# NOTIFICATION CONFIGS
# ══════════════════════════════════════════════════════════════════

class NotificationConfigIn(BaseModel):
    event_type: str
    channels: list[str] = ["IN_APP"]
    recipients: list[str] = []
    delay_hours: int = 0
    is_active: bool = True


class NotificationConfigOut(NotificationConfigIn):
    id: str
    created_at: str | None = None


def _notif_cfg_from_row(r) -> NotificationConfigOut:
    return NotificationConfigOut(
        id=str(r.id), event_type=r.event_type,
        channels=list(r.channels) if r.channels else ["IN_APP"],
        recipients=list(r.recipients) if r.recipients else [],
        delay_hours=r.delay_hours or 0, is_active=r.is_active,
        created_at=str(r.created_at) if r.created_at else None,
    )


@router.get("/notifications", response_model=list[NotificationConfigOut])
async def list_notification_configs(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.read"),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        text("SELECT * FROM notification_configs WHERE tenant_id = :tid ORDER BY event_type"),
        {"tid": str(tenant.tenant_id)},
    )).fetchall()
    return [_notif_cfg_from_row(r) for r in rows]


@router.post("/notifications", response_model=NotificationConfigOut, status_code=201)
async def create_notification_config(
    body: NotificationConfigIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    nid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO notification_configs (id, tenant_id, event_type, channels, recipients, delay_hours, is_active)
        VALUES (:id, :tid, :event, :channels, :recipients, :delay, :active)
    """), {
        "id": str(nid), "tid": tid, "event": body.event_type,
        "channels": body.channels, "recipients": body.recipients,
        "delay": body.delay_hours, "active": body.is_active,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM notification_configs WHERE id = :id"), {"id": str(nid)})).first()
    return _notif_cfg_from_row(row)


@router.put("/notifications/{nc_id}", response_model=NotificationConfigOut)
async def update_notification_config(
    nc_id: str,
    body: NotificationConfigIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    result = await db.execute(text("""
        UPDATE notification_configs SET event_type=:event, channels=:channels,
            recipients=:recipients, delay_hours=:delay, is_active=:active, updated_at=now()
        WHERE id=:id AND tenant_id=:tid RETURNING id
    """), {
        "id": nc_id, "tid": tid, "event": body.event_type,
        "channels": body.channels, "recipients": body.recipients,
        "delay": body.delay_hours, "active": body.is_active,
    })
    if not result.first():
        raise HTTPException(404, "Configuration de notification non trouvee")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM notification_configs WHERE id = :id"), {"id": nc_id})).first()
    return _notif_cfg_from_row(row)


@router.delete("/notifications/{nc_id}", status_code=204)
async def delete_notification_config(
    nc_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = require_permission("settings.update"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("DELETE FROM notification_configs WHERE id = :id AND tenant_id = :tid RETURNING id"),
        {"id": nc_id, "tid": str(tenant.tenant_id)},
    )
    if not result.first():
        raise HTTPException(404, "Configuration de notification non trouvee")
    await db.commit()
