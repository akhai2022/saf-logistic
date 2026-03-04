from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user, require_permission
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/billing", tags=["billing"])


# ═══════════════════════════════════════════════════════════════
# Supplier Invoice Matching
# ═══════════════════════════════════════════════════════════════

class MatchSuggestion(BaseModel):
    job_id: str
    job_numero: str | None = None
    client_name: str | None = None
    date_chargement: str | None = None
    montant_achat_ht: float | None = None
    already_matched: bool = False


class MatchLineCreate(BaseModel):
    job_id: str
    montant_facture: float


class SupplierInvoiceMatchRequest(BaseModel):
    matchings: list[MatchLineCreate]


class SupplierInvoiceMatchOut(BaseModel):
    id: str
    job_id: str
    job_numero: str | None = None
    montant_attendu: float | None = None
    montant_facture: float
    ecart: float | None = None
    ecart_pourcent: float | None = None
    statut: str


class SupplierInvoiceDetailOut(BaseModel):
    id: str
    supplier_name: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    total_ht: float | None = None
    total_tva: float | None = None
    total_ttc: float | None = None
    status: str
    subcontractor_id: str | None = None
    statut_rapprochement: str | None = None
    matchings: list[SupplierInvoiceMatchOut] = []


@router.get("/supplier-invoices/{inv_id}/detail", response_model=SupplierInvoiceDetailOut)
async def get_supplier_invoice_detail(
    inv_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    row = (await db.execute(text(
        "SELECT * FROM supplier_invoices WHERE id = :id AND tenant_id = :tid"
    ), {"id": inv_id, "tid": tid})).first()
    if not row:
        raise HTTPException(404, "Facture fournisseur non trouvee")

    matchings_rows = (await db.execute(text("""
        SELECT m.*, j.numero as job_numero
        FROM supplier_invoice_matchings m
        LEFT JOIN jobs j ON j.id = m.job_id
        WHERE m.supplier_invoice_id = :inv_id AND m.tenant_id = :tid
        ORDER BY m.created_at
    """), {"inv_id": inv_id, "tid": tid})).fetchall()

    return SupplierInvoiceDetailOut(
        id=str(row.id), supplier_name=row.supplier_name,
        invoice_number=row.invoice_number,
        invoice_date=str(row.invoice_date) if row.invoice_date else None,
        total_ht=float(row.total_ht) if row.total_ht else None,
        total_tva=float(row.total_tva) if row.total_tva else None,
        total_ttc=float(row.total_ttc) if row.total_ttc else None,
        status=row.status,
        subcontractor_id=str(row.subcontractor_id) if hasattr(row, "subcontractor_id") and row.subcontractor_id else None,
        statut_rapprochement=getattr(row, "statut_rapprochement", None),
        matchings=[SupplierInvoiceMatchOut(
            id=str(m.id), job_id=str(m.job_id), job_numero=m.job_numero,
            montant_attendu=float(m.montant_attendu) if m.montant_attendu else None,
            montant_facture=float(m.montant_facture),
            ecart=float(m.ecart) if m.ecart else None,
            ecart_pourcent=float(m.ecart_pourcent) if m.ecart_pourcent else None,
            statut=m.statut,
        ) for m in matchings_rows],
    )


@router.get("/supplier-invoices/{inv_id}/suggested-matches", response_model=list[MatchSuggestion])
async def suggest_matches(
    inv_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    inv = (await db.execute(text(
        "SELECT * FROM supplier_invoices WHERE id = :id AND tenant_id = :tid"
    ), {"id": inv_id, "tid": tid})).first()
    if not inv:
        raise HTTPException(404)

    inv_date = inv.invoice_date or date.today()
    start = inv_date - timedelta(days=30)
    end = inv_date + timedelta(days=7)

    missions = (await db.execute(text("""
        SELECT j.id, j.numero, j.montant_achat_ht, j.date_chargement_prevue,
               c.raison_sociale as client_name, j.subcontractor_id
        FROM jobs j
        LEFT JOIN customers c ON c.id = j.customer_id
        WHERE j.tenant_id = :tid
          AND j.is_subcontracted = true
          AND COALESCE(j.statut, j.status) IN ('LIVREE', 'CLOTUREE')
          AND j.date_chargement_prevue BETWEEN :start AND :end
        ORDER BY j.date_chargement_prevue DESC
    """), {"tid": tid, "start": start, "end": end})).fetchall()

    # Check which are already matched
    already_matched = set()
    matched_rows = (await db.execute(text(
        "SELECT job_id FROM supplier_invoice_matchings WHERE supplier_invoice_id = :inv_id"
    ), {"inv_id": inv_id})).fetchall()
    for mr in matched_rows:
        already_matched.add(str(mr.job_id))

    return [MatchSuggestion(
        job_id=str(m.id), job_numero=m.numero,
        client_name=m.client_name,
        date_chargement=str(m.date_chargement_prevue) if m.date_chargement_prevue else None,
        montant_achat_ht=float(m.montant_achat_ht) if m.montant_achat_ht else None,
        already_matched=str(m.id) in already_matched,
    ) for m in missions]


@router.post("/supplier-invoices/{inv_id}/match")
async def match_supplier_invoice(
    inv_id: str,
    body: SupplierInvoiceMatchRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)

    for m in body.matchings:
        job = (await db.execute(text(
            "SELECT montant_achat_ht FROM jobs WHERE id = :id AND tenant_id = :tid"
        ), {"id": m.job_id, "tid": tid})).first()

        montant_attendu = float(job.montant_achat_ht) if job and job.montant_achat_ht else None
        ecart = m.montant_facture - montant_attendu if montant_attendu is not None else None
        ecart_pct = (ecart / montant_attendu * 100) if montant_attendu and montant_attendu > 0 and ecart is not None else None

        await db.execute(text("""
            INSERT INTO supplier_invoice_matchings
                (id, tenant_id, supplier_invoice_id, job_id,
                 montant_attendu, montant_facture, ecart, ecart_pourcent)
            VALUES (:id, :tid, :inv_id, :job_id, :attendu, :facture, :ecart, :pct)
        """), {
            "id": str(uuid.uuid4()), "tid": tid, "inv_id": inv_id,
            "job_id": m.job_id, "attendu": montant_attendu,
            "facture": m.montant_facture, "ecart": ecart, "pct": ecart_pct,
        })

    await db.execute(text("""
        UPDATE supplier_invoices SET statut_rapprochement = 'RAPPROCHEE'
        WHERE id = :id AND tenant_id = :tid
    """), {"id": inv_id, "tid": tid})
    await db.commit()
    return {"status": "matched", "count": len(body.matchings)}


@router.post("/supplier-invoices/{inv_id}/approve")
async def approve_supplier_invoice(
    inv_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    row = (await db.execute(text(
        "SELECT statut_rapprochement FROM supplier_invoices WHERE id = :id AND tenant_id = :tid"
    ), {"id": inv_id, "tid": tid})).first()
    if not row:
        raise HTTPException(404)
    if row.statut_rapprochement != "RAPPROCHEE":
        raise HTTPException(400, "Facture doit etre rapprochee avant approbation")

    await db.execute(text("""
        UPDATE supplier_invoices
        SET status = 'approved', statut_rapprochement = 'APPROUVEE'
        WHERE id = :id AND tenant_id = :tid
    """), {"id": inv_id, "tid": tid})
    await db.commit()
    return {"status": "approved"}


# ═══════════════════════════════════════════════════════════════
# Dunning (Relances)
# ═══════════════════════════════════════════════════════════════

class DunningLevelIn(BaseModel):
    niveau: int
    libelle: str
    jours_apres_echeance: int
    template_objet: str | None = None
    template_texte: str | None = None


class DunningLevelOut(BaseModel):
    id: str
    niveau: int
    libelle: str
    jours_apres_echeance: int
    template_objet: str | None = None
    template_texte: str | None = None
    is_active: bool = True


class DunningActionCreate(BaseModel):
    invoice_id: str
    customer_id: str
    dunning_level_id: str | None = None
    mode: str = "EMAIL"
    notes: str | None = None


class DunningActionOut(BaseModel):
    id: str
    invoice_id: str
    invoice_number: str | None = None
    customer_id: str
    customer_name: str | None = None
    dunning_level_id: str | None = None
    niveau: int | None = None
    date_relance: str
    mode: str
    notes: str | None = None
    created_at: str | None = None


class OverdueInvoiceItem(BaseModel):
    invoice_id: str
    invoice_number: str
    customer_name: str
    total_ttc: float
    due_date: str
    days_overdue: int
    last_relance_date: str | None = None
    last_relance_niveau: int | None = None
    nb_relances: int = 0


@router.get("/dunning/levels", response_model=list[DunningLevelOut])
async def list_dunning_levels(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text("""
        SELECT * FROM dunning_levels
        WHERE tenant_id = :tid AND is_active = true
        ORDER BY niveau
    """), {"tid": str(tenant.tenant_id)})).fetchall()
    return [DunningLevelOut(
        id=str(r.id), niveau=r.niveau, libelle=r.libelle,
        jours_apres_echeance=r.jours_apres_echeance,
        template_objet=r.template_objet, template_texte=r.template_texte,
        is_active=r.is_active,
    ) for r in rows]


@router.post("/dunning/levels", response_model=DunningLevelOut, status_code=201)
async def create_dunning_level(
    body: DunningLevelIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO dunning_levels (id, tenant_id, niveau, libelle,
            jours_apres_echeance, template_objet, template_texte)
        VALUES (:id, :tid, :niveau, :libelle, :jours, :objet, :texte)
    """), {
        "id": str(lid), "tid": str(tenant.tenant_id),
        "niveau": body.niveau, "libelle": body.libelle,
        "jours": body.jours_apres_echeance,
        "objet": body.template_objet, "texte": body.template_texte,
    })
    await db.commit()
    return DunningLevelOut(
        id=str(lid), niveau=body.niveau, libelle=body.libelle,
        jours_apres_echeance=body.jours_apres_echeance,
        template_objet=body.template_objet, template_texte=body.template_texte,
    )


@router.put("/dunning/levels/{level_id}", response_model=DunningLevelOut)
async def update_dunning_level(
    level_id: str,
    body: DunningLevelIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE dunning_levels SET niveau=:niveau, libelle=:libelle,
            jours_apres_echeance=:jours, template_objet=:objet, template_texte=:texte
        WHERE id=:id AND tenant_id=:tid RETURNING id
    """), {
        "id": level_id, "tid": str(tenant.tenant_id),
        "niveau": body.niveau, "libelle": body.libelle,
        "jours": body.jours_apres_echeance,
        "objet": body.template_objet, "texte": body.template_texte,
    })
    if not result.first():
        raise HTTPException(404)
    await db.commit()
    return DunningLevelOut(
        id=level_id, niveau=body.niveau, libelle=body.libelle,
        jours_apres_echeance=body.jours_apres_echeance,
        template_objet=body.template_objet, template_texte=body.template_texte,
    )


@router.get("/dunning/overdue", response_model=list[OverdueInvoiceItem])
async def list_overdue_invoices(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    today = date.today()
    rows = (await db.execute(text("""
        SELECT i.id as invoice_id, i.invoice_number,
               COALESCE(c.raison_sociale, c.name) as customer_name,
               i.total_ttc, i.due_date,
               (SELECT MAX(da.date_relance) FROM dunning_actions da WHERE da.invoice_id = i.id) as last_relance_date,
               (SELECT dl.niveau FROM dunning_actions da2
                JOIN dunning_levels dl ON dl.id = da2.dunning_level_id
                WHERE da2.invoice_id = i.id
                ORDER BY da2.date_relance DESC LIMIT 1) as last_relance_niveau,
               (SELECT COUNT(*) FROM dunning_actions da3 WHERE da3.invoice_id = i.id) as nb_relances
        FROM invoices i
        JOIN customers c ON c.id = i.customer_id
        WHERE i.tenant_id = :tid AND i.status = 'validated' AND i.due_date < :today
        ORDER BY i.due_date
    """), {"tid": tid, "today": today})).fetchall()

    return [OverdueInvoiceItem(
        invoice_id=str(r.invoice_id), invoice_number=r.invoice_number or "",
        customer_name=r.customer_name or "",
        total_ttc=float(r.total_ttc),
        due_date=str(r.due_date),
        days_overdue=(today - r.due_date).days,
        last_relance_date=str(r.last_relance_date) if r.last_relance_date else None,
        last_relance_niveau=r.last_relance_niveau,
        nb_relances=r.nb_relances or 0,
    ) for r in rows]


@router.get("/dunning/actions", response_model=list[DunningActionOut])
async def list_dunning_actions(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    customer_id: str | None = Query(None),
    invoice_id: str | None = Query(None),
):
    tid = str(tenant.tenant_id)
    q = """
        SELECT da.*, i.invoice_number,
               COALESCE(c.raison_sociale, c.name) as customer_name,
               dl.niveau
        FROM dunning_actions da
        LEFT JOIN invoices i ON i.id = da.invoice_id
        LEFT JOIN customers c ON c.id = da.customer_id
        LEFT JOIN dunning_levels dl ON dl.id = da.dunning_level_id
        WHERE da.tenant_id = :tid
    """
    params: dict = {"tid": tid}
    if customer_id:
        q += " AND da.customer_id = :cid"
        params["cid"] = customer_id
    if invoice_id:
        q += " AND da.invoice_id = :iid"
        params["iid"] = invoice_id
    q += " ORDER BY da.date_relance DESC"

    rows = (await db.execute(text(q), params)).fetchall()
    return [DunningActionOut(
        id=str(r.id), invoice_id=str(r.invoice_id),
        invoice_number=r.invoice_number,
        customer_id=str(r.customer_id),
        customer_name=r.customer_name,
        dunning_level_id=str(r.dunning_level_id) if r.dunning_level_id else None,
        niveau=r.niveau,
        date_relance=str(r.date_relance),
        mode=r.mode or "EMAIL",
        notes=r.notes,
        created_at=str(r.created_at) if r.created_at else None,
    ) for r in rows]


@router.post("/dunning/actions", response_model=DunningActionOut, status_code=201)
async def create_dunning_action(
    body: DunningActionCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    aid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO dunning_actions (id, tenant_id, invoice_id, customer_id,
            dunning_level_id, date_relance, mode, notes, created_by)
        VALUES (:id, :tid, :iid, :cid, :lid, :date, :mode, :notes, :uid)
    """), {
        "id": str(aid), "tid": tid, "iid": body.invoice_id,
        "cid": body.customer_id, "lid": body.dunning_level_id,
        "date": date.today(), "mode": body.mode, "notes": body.notes,
        "uid": user.get("id") if isinstance(user, dict) else None,
    })
    await db.commit()
    return DunningActionOut(
        id=str(aid), invoice_id=body.invoice_id, customer_id=body.customer_id,
        dunning_level_id=body.dunning_level_id,
        date_relance=str(date.today()), mode=body.mode, notes=body.notes,
    )


# ═══════════════════════════════════════════════════════════════
# Purchase Pricing Rules (Tarifs Achat)
# ═══════════════════════════════════════════════════════════════

class PurchasePricingRuleIn(BaseModel):
    subcontractor_id: str | None = None
    label: str
    rule_type: str  # km | flat | surcharge
    rate: float
    min_km: float | None = None
    max_km: float | None = None


class PurchasePricingRuleOut(BaseModel):
    id: str
    subcontractor_id: str | None = None
    label: str
    rule_type: str
    rate: float
    min_km: float | None = None
    max_km: float | None = None
    direction: str = "ACHAT"
    is_active: bool = True


@router.get("/purchase-pricing-rules", response_model=list[PurchasePricingRuleOut])
async def list_purchase_pricing_rules(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    subcontractor_id: str | None = Query(None),
):
    q = "SELECT * FROM pricing_rules WHERE tenant_id = :tid AND direction = 'ACHAT' AND is_active = true"
    params: dict = {"tid": str(tenant.tenant_id)}
    if subcontractor_id:
        q += " AND (subcontractor_id = :sid OR subcontractor_id IS NULL)"
        params["sid"] = subcontractor_id
    q += " ORDER BY rule_type, label"
    rows = (await db.execute(text(q), params)).fetchall()
    return [PurchasePricingRuleOut(
        id=str(r.id), subcontractor_id=str(r.subcontractor_id) if r.subcontractor_id else None,
        label=r.label, rule_type=r.rule_type, rate=float(r.rate),
        min_km=float(r.min_km) if r.min_km else None,
        max_km=float(r.max_km) if r.max_km else None,
        direction="ACHAT",
    ) for r in rows]


@router.post("/purchase-pricing-rules", response_model=PurchasePricingRuleOut, status_code=201)
async def create_purchase_pricing_rule(
    body: PurchasePricingRuleIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO pricing_rules (id, tenant_id, subcontractor_id, label, rule_type,
            rate, min_km, max_km, direction)
        VALUES (:id, :tid, :sid, :label, :rtype, :rate, :mink, :maxk, 'ACHAT')
    """), {
        "id": str(rid), "tid": str(tenant.tenant_id),
        "sid": body.subcontractor_id, "label": body.label,
        "rtype": body.rule_type, "rate": body.rate,
        "mink": body.min_km, "maxk": body.max_km,
    })
    await db.commit()
    return PurchasePricingRuleOut(
        id=str(rid), subcontractor_id=body.subcontractor_id,
        label=body.label, rule_type=body.rule_type, rate=body.rate,
        min_km=body.min_km, max_km=body.max_km,
    )


@router.put("/purchase-pricing-rules/{rule_id}", response_model=PurchasePricingRuleOut)
async def update_purchase_pricing_rule(
    rule_id: str, body: PurchasePricingRuleIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE pricing_rules SET subcontractor_id=:sid, label=:label, rule_type=:rtype,
            rate=:rate, min_km=:mink, max_km=:maxk
        WHERE id=:id AND tenant_id=:tid AND direction='ACHAT' RETURNING id
    """), {
        "id": rule_id, "tid": str(tenant.tenant_id),
        "sid": body.subcontractor_id, "label": body.label,
        "rtype": body.rule_type, "rate": body.rate,
        "mink": body.min_km, "maxk": body.max_km,
    })
    if not result.first():
        raise HTTPException(404)
    await db.commit()
    return PurchasePricingRuleOut(
        id=rule_id, subcontractor_id=body.subcontractor_id,
        label=body.label, rule_type=body.rule_type, rate=body.rate,
        min_km=body.min_km, max_km=body.max_km,
    )


@router.delete("/purchase-pricing-rules/{rule_id}")
async def delete_purchase_pricing_rule(
    rule_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE pricing_rules SET is_active = false
        WHERE id=:id AND tenant_id=:tid AND direction='ACHAT' RETURNING id
    """), {"id": rule_id, "tid": str(tenant.tenant_id)})
    if not result.first():
        raise HTTPException(404)
    await db.commit()
    return {"deleted": True}
