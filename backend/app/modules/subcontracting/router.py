from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant

router = APIRouter(prefix="/v1/subcontracting", tags=["subcontracting"])


# ---- Schemas ----

class OfferCreate(BaseModel):
    job_id: str
    subcontractor_id: str
    montant_propose: float
    date_limite_reponse: str | None = None


class OfferOut(BaseModel):
    id: str
    job_id: str
    job_numero: str | None = None
    subcontractor_id: str
    subcontractor_name: str | None = None
    montant_propose: float
    montant_contre_offre: float | None = None
    date_envoi: str | None = None
    date_limite_reponse: str | None = None
    date_reponse: str | None = None
    statut: str
    motif_refus: str | None = None
    notes: str | None = None


class RejectOffer(BaseModel):
    motif_refus: str | None = None


class CounterOffer(BaseModel):
    montant_contre_offre: float


# ---- Endpoints ----

@router.post("/offers", response_model=OfferOut, status_code=201)
async def create_offer(
    body: OfferCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    oid = uuid.uuid4()

    # Insert the offer
    await db.execute(text("""
        INSERT INTO subcontractor_offers
            (id, tenant_id, job_id, subcontractor_id, montant_propose,
             date_limite_reponse, statut, date_envoi)
        VALUES (:id, :tid, :jid, :sid, :montant, :dlr, 'ENVOYEE', NOW())
    """), {
        "id": str(oid), "tid": tid, "jid": body.job_id,
        "sid": body.subcontractor_id, "montant": body.montant_propose,
        "dlr": body.date_limite_reponse,
    })

    # Create a notification_dispatch task for the subcontractor
    task_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO tasks (id, tenant_id, category, title,
            entity_type, entity_id, status)
        VALUES (:id, :tid, 'notification_dispatch', :title,
            'subcontractor_offer', :eid, 'open')
    """), {
        "id": str(task_id), "tid": tid, "eid": str(oid),
        "title": f'Offer sent to subcontractor {body.subcontractor_id}',
    })

    await db.commit()

    # Fetch the created offer with joined data
    row = (await db.execute(text("""
        SELECT o.*, j.numero AS job_numero, s.raison_sociale AS subcontractor_name
        FROM subcontractor_offers o
        LEFT JOIN jobs j ON o.job_id = j.id
        LEFT JOIN subcontractors s ON o.subcontractor_id = s.id
        WHERE o.id = :id
    """), {"id": str(oid)})).first()

    return _offer_from_row(row)


@router.get("/offers", response_model=list[OfferOut])
async def list_offers(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    job_id: str | None = Query(None),
    subcontractor_id: str | None = Query(None),
    statut: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    q = """
        SELECT o.*, j.numero AS job_numero, s.raison_sociale AS subcontractor_name
        FROM subcontractor_offers o
        LEFT JOIN jobs j ON o.job_id = j.id
        LEFT JOIN subcontractors s ON o.subcontractor_id = s.id
        WHERE o.tenant_id = :tid
    """
    params: dict = {"tid": str(tenant.tenant_id)}
    if job_id:
        q += " AND o.job_id = :jid"
        params["jid"] = job_id
    if subcontractor_id:
        q += " AND o.subcontractor_id = :sid"
        params["sid"] = subcontractor_id
    if statut:
        q += " AND o.statut = :statut"
        params["statut"] = statut
    allowed_sorts = {"created_at": "o.created_at", "montant_propose": "o.montant_propose", "date_envoi": "o.date_envoi"}
    sort_col = allowed_sorts.get(sort_by, "o.created_at") if sort_by else "o.created_at"
    q += f" ORDER BY {sort_col} {order} LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = (await db.execute(text(q), params)).fetchall()
    return [_offer_from_row(r) for r in rows]


@router.get("/offers/{offer_id}", response_model=OfferOut)
async def get_offer(
    offer_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text("""
        SELECT o.*, j.numero AS job_numero, s.raison_sociale AS subcontractor_name
        FROM subcontractor_offers o
        LEFT JOIN jobs j ON o.job_id = j.id
        LEFT JOIN subcontractors s ON o.subcontractor_id = s.id
        WHERE o.id = :id AND o.tenant_id = :tid
    """), {"id": offer_id, "tid": str(tenant.tenant_id)})).first()
    if not row:
        raise HTTPException(404, "Offer not found")
    return _offer_from_row(row)


@router.post("/offers/{offer_id}/accept", response_model=OfferOut)
async def accept_offer(
    offer_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    row = (await db.execute(text("""
        SELECT * FROM subcontractor_offers WHERE id = :id AND tenant_id = :tid
    """), {"id": offer_id, "tid": tid})).first()
    if not row:
        raise HTTPException(404, "Offer not found")

    # Accept this offer
    await db.execute(text("""
        UPDATE subcontractor_offers
        SET statut = 'ACCEPTEE', date_reponse = NOW()
        WHERE id = :id
    """), {"id": offer_id})

    # Update the job: mark as subcontracted
    await db.execute(text("""
        UPDATE jobs
        SET is_subcontracted = true,
            subcontractor_id = :sid,
            montant_achat_ht = :montant
        WHERE id = :jid AND tenant_id = :tid
    """), {
        "sid": str(row.subcontractor_id),
        "montant": float(row.montant_propose),
        "jid": str(row.job_id),
        "tid": tid,
    })

    # Reject all other pending offers for the same job
    await db.execute(text("""
        UPDATE subcontractor_offers
        SET statut = 'REFUSEE', motif_refus = 'Autre offre acceptee'
        WHERE job_id = :jid AND tenant_id = :tid AND id != :id
          AND statut IN ('ENVOYEE', 'VUE', 'CONTRE_OFFRE')
    """), {"jid": str(row.job_id), "tid": tid, "id": offer_id})

    await db.commit()

    updated = (await db.execute(text("""
        SELECT o.*, j.numero AS job_numero, s.raison_sociale AS subcontractor_name
        FROM subcontractor_offers o
        LEFT JOIN jobs j ON o.job_id = j.id
        LEFT JOIN subcontractors s ON o.subcontractor_id = s.id
        WHERE o.id = :id
    """), {"id": offer_id})).first()
    return _offer_from_row(updated)


@router.post("/offers/{offer_id}/reject", response_model=OfferOut)
async def reject_offer(
    offer_id: str,
    body: RejectOffer,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    row = (await db.execute(text("""
        SELECT * FROM subcontractor_offers WHERE id = :id AND tenant_id = :tid
    """), {"id": offer_id, "tid": tid})).first()
    if not row:
        raise HTTPException(404, "Offer not found")

    await db.execute(text("""
        UPDATE subcontractor_offers
        SET statut = 'REFUSEE', motif_refus = :motif, date_reponse = NOW()
        WHERE id = :id
    """), {"id": offer_id, "motif": body.motif_refus})
    await db.commit()

    updated = (await db.execute(text("""
        SELECT o.*, j.numero AS job_numero, s.raison_sociale AS subcontractor_name
        FROM subcontractor_offers o
        LEFT JOIN jobs j ON o.job_id = j.id
        LEFT JOIN subcontractors s ON o.subcontractor_id = s.id
        WHERE o.id = :id
    """), {"id": offer_id})).first()
    return _offer_from_row(updated)


@router.post("/offers/{offer_id}/counter", response_model=OfferOut)
async def counter_offer(
    offer_id: str,
    body: CounterOffer,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    row = (await db.execute(text("""
        SELECT * FROM subcontractor_offers WHERE id = :id AND tenant_id = :tid
    """), {"id": offer_id, "tid": tid})).first()
    if not row:
        raise HTTPException(404, "Offer not found")

    await db.execute(text("""
        UPDATE subcontractor_offers
        SET statut = 'CONTRE_OFFRE', montant_contre_offre = :montant
        WHERE id = :id
    """), {"id": offer_id, "montant": body.montant_contre_offre})
    await db.commit()

    updated = (await db.execute(text("""
        SELECT o.*, j.numero AS job_numero, s.raison_sociale AS subcontractor_name
        FROM subcontractor_offers o
        LEFT JOIN jobs j ON o.job_id = j.id
        LEFT JOIN subcontractors s ON o.subcontractor_id = s.id
        WHERE o.id = :id
    """), {"id": offer_id})).first()
    return _offer_from_row(updated)


@router.post("/offers/{offer_id}/cancel", response_model=OfferOut)
async def cancel_offer(
    offer_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    row = (await db.execute(text("""
        SELECT * FROM subcontractor_offers WHERE id = :id AND tenant_id = :tid
    """), {"id": offer_id, "tid": tid})).first()
    if not row:
        raise HTTPException(404, "Offer not found")
    if row.statut not in ("ENVOYEE", "VUE"):
        raise HTTPException(400, "Only offers with statut ENVOYEE or VUE can be cancelled")

    await db.execute(text("""
        UPDATE subcontractor_offers SET statut = 'ANNULEE' WHERE id = :id
    """), {"id": offer_id})
    await db.commit()

    updated = (await db.execute(text("""
        SELECT o.*, j.numero AS job_numero, s.raison_sociale AS subcontractor_name
        FROM subcontractor_offers o
        LEFT JOIN jobs j ON o.job_id = j.id
        LEFT JOIN subcontractors s ON o.subcontractor_id = s.id
        WHERE o.id = :id
    """), {"id": offer_id})).first()
    return _offer_from_row(updated)


# ---- Helpers ----

def _offer_from_row(r) -> OfferOut:
    return OfferOut(
        id=str(r.id),
        job_id=str(r.job_id),
        job_numero=r.job_numero if r.job_numero else None,
        subcontractor_id=str(r.subcontractor_id),
        subcontractor_name=r.subcontractor_name if r.subcontractor_name else None,
        montant_propose=float(r.montant_propose),
        montant_contre_offre=float(r.montant_contre_offre) if r.montant_contre_offre else None,
        date_envoi=str(r.date_envoi) if r.date_envoi else None,
        date_limite_reponse=str(r.date_limite_reponse) if r.date_limite_reponse else None,
        date_reponse=str(r.date_reponse) if r.date_reponse else None,
        statut=r.statut,
        motif_refus=r.motif_refus,
        notes=r.notes if hasattr(r, "notes") and r.notes else None,
    )
