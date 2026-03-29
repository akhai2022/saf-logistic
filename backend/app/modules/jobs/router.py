"""Module C — Missions / Dossiers Transport, POD, Disputes: full CRUD."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, date as date_type
from dateutil.parser import parse as parse_dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.modules.jobs.schemas import (
    DeliveryPointCreate,
    DeliveryPointOut,
    DeliveryPointStatusChange,
    DisputeAttachmentCreate,
    DisputeAttachmentOut,
    DisputeCreate,
    DisputeOut,
    DisputeUpdate,
    GoodsCreate,
    GoodsOut,
    MissionAssign,
    MissionCreate,
    MissionDetail,
    MissionOut,
    MissionStatusChange,
    MissionUpdate,
    PodCreate,
    PodOut,
    PodValidation,
    VALID_TRANSITIONS,
)

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


# ── Helpers ───────────────────────────────────────────────────────

def _ts(val) -> str | None:
    return str(val) if val else None

def _dec(val) -> float | None:
    return float(val) if val is not None else None

def _parse_date(val) -> datetime | None:
    """Parse a date string to datetime for DB insertion."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date_type):
        return datetime(val.year, val.month, val.day, tzinfo=timezone.utc)
    try:
        return parse_dt(str(val))
    except (ValueError, TypeError):
        return None

def _json_load(val) -> dict | list | None:
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


def _mission_from_row(r) -> MissionOut:
    statut = r.status if hasattr(r, "status") else None
    # Map legacy → new
    legacy_map = {"draft": "BROUILLON", "planned": "PLANIFIEE", "assigned": "AFFECTEE",
                  "in_progress": "EN_COURS", "delivered": "LIVREE", "closed": "CLOTUREE"}
    display_statut = legacy_map.get(statut, statut) if statut else None

    return MissionOut(
        id=str(r.id),
        numero=getattr(r, "numero", None),
        reference=r.reference,
        reference_client=getattr(r, "reference_client", None),
        client_id=str(r.customer_id) if r.customer_id else None,
        client_raison_sociale=getattr(r, "client_raison_sociale", None),
        type_mission=getattr(r, "type_mission", None),
        priorite=getattr(r, "priorite", None),
        statut=display_statut,
        status=statut,  # legacy
        date_chargement_prevue=_ts(getattr(r, "date_chargement_prevue", None) or getattr(r, "pickup_date", None)),
        date_livraison_prevue=_ts(getattr(r, "date_livraison_prevue", None) or getattr(r, "delivery_date", None)),
        date_cloture=_ts(getattr(r, "date_cloture", None) or getattr(r, "closed_at", None)),
        driver_id=str(r.driver_id) if r.driver_id else None,
        vehicle_id=str(r.vehicle_id) if r.vehicle_id else None,
        trailer_id=str(r.trailer_id) if getattr(r, "trailer_id", None) else None,
        subcontractor_id=str(r.subcontractor_id) if getattr(r, "subcontractor_id", None) else None,
        is_subcontracted=bool(getattr(r, "is_subcontracted", False)),
        montant_vente_ht=_dec(getattr(r, "montant_vente_ht", None)),
        montant_achat_ht=_dec(getattr(r, "montant_achat_ht", None)),
        montant_tva=_dec(getattr(r, "montant_tva", None)),
        montant_vente_ttc=_dec(getattr(r, "montant_vente_ttc", None)),
        marge_brute=_dec(getattr(r, "marge_brute", None)),
        adresse_chargement_libre=_json_load(getattr(r, "adresse_chargement_libre", None)),
        distance_estimee_km=_dec(getattr(r, "distance_estimee_km", None)),
        distance_reelle_km=_dec(getattr(r, "distance_reelle_km", None)),
        contraintes=_json_load(getattr(r, "contraintes", None)),
        notes_exploitation=getattr(r, "notes_exploitation", None),
        pickup_address=r.pickup_address,
        delivery_address=r.delivery_address,
        distance_km=_dec(r.distance_km),
        weight_kg=_dec(r.weight_kg),
        goods_description=r.goods_description,
        notes=r.notes,
        pod_s3_key=r.pod_s3_key,
        created_at=_ts(r.created_at),
        agency_id=str(r.agency_id) if r.agency_id else None,
        source_type=getattr(r, "source_type", None),
        source_route_template_id=str(r.source_route_template_id) if getattr(r, "source_route_template_id", None) else None,
        source_route_template_code=getattr(r, "source_template_code", None),
        source_route_run_id=str(r.source_route_run_id) if getattr(r, "source_route_run_id", None) else None,
        source_route_run_code=getattr(r, "source_run_code", None),
    )


def _dp_from_row(r) -> DeliveryPointOut:
    return DeliveryPointOut(
        id=str(r.id), mission_id=str(r.mission_id), ordre=r.ordre,
        adresse_id=str(r.adresse_id) if r.adresse_id else None,
        adresse_libre=_json_load(r.adresse_libre),
        contact_nom=r.contact_nom, contact_telephone=r.contact_telephone,
        date_livraison_prevue=_ts(r.date_livraison_prevue),
        date_livraison_reelle=_ts(r.date_livraison_reelle),
        instructions=r.instructions, statut=r.statut,
        motif_echec=r.motif_echec,
    )


def _goods_from_row(r) -> GoodsOut:
    return GoodsOut(
        id=str(r.id), mission_id=str(r.mission_id),
        delivery_point_id=str(r.delivery_point_id) if r.delivery_point_id else None,
        description=r.description, nature=r.nature,
        quantite=r.quantite, unite=r.unite,
        poids_brut_kg=r.poids_brut_kg, poids_net_kg=_dec(r.poids_net_kg),
        volume_m3=_dec(r.volume_m3),
        valeur_declaree_eur=_dec(r.valeur_declaree_eur),
        adr_classe=r.adr_classe,
        temperature_min=_dec(r.temperature_min), temperature_max=_dec(r.temperature_max),
        references_colis=_json_load(r.references_colis),
    )


def _pod_from_row(r) -> PodOut:
    return PodOut(
        id=str(r.id), mission_id=str(r.mission_id),
        delivery_point_id=str(r.delivery_point_id) if r.delivery_point_id else None,
        type=r.type, fichier_s3_key=r.fichier_s3_key,
        fichier_nom_original=r.fichier_nom_original,
        fichier_taille_octets=r.fichier_taille_octets,
        fichier_mime_type=r.fichier_mime_type,
        date_upload=_ts(r.date_upload), uploaded_by=str(r.uploaded_by) if r.uploaded_by else None,
        geoloc_latitude=_dec(r.geoloc_latitude), geoloc_longitude=_dec(r.geoloc_longitude),
        has_reserves=r.has_reserves, reserves_texte=r.reserves_texte,
        reserves_categorie=r.reserves_categorie, statut=r.statut,
        date_validation=_ts(r.date_validation),
        validated_by=str(r.validated_by) if r.validated_by else None,
        motif_rejet=r.motif_rejet,
    )


def _dispute_from_row(r) -> DisputeOut:
    return DisputeOut(
        id=str(r.id), numero=r.numero, mission_id=str(r.mission_id),
        type=r.type, description=r.description,
        responsabilite=r.responsabilite,
        responsable_entity_id=str(r.responsable_entity_id) if r.responsable_entity_id else None,
        montant_estime_eur=_dec(r.montant_estime_eur),
        montant_retenu_eur=_dec(r.montant_retenu_eur),
        statut=r.statut, date_ouverture=_ts(r.date_ouverture),
        date_resolution=_ts(r.date_resolution),
        resolution_texte=r.resolution_texte,
        impact_facturation=r.impact_facturation,
        opened_by=str(r.opened_by) if r.opened_by else None,
        assigned_to=str(r.assigned_to) if r.assigned_to else None,
        notes_internes=r.notes_internes,
        created_at=_ts(r.created_at),
    )


async def _gen_mission_numero(db: AsyncSession, tid: str) -> str:
    """Generate next mission number: MIS-YYYY-MM-NNNNN."""
    now = datetime.now(timezone.utc)
    prefix = f"MIS-{now.year}-{now.month:02d}-"
    row = (await db.execute(text("""
        SELECT COUNT(*) + 1 as seq FROM jobs WHERE tenant_id = :tid AND numero LIKE :prefix
    """), {"tid": tid, "prefix": f"{prefix}%"})).first()
    seq = row.seq if row else 1
    return f"{prefix}{seq:05d}"


async def _gen_dispute_numero(db: AsyncSession, tid: str) -> str:
    """Generate next dispute number: LIT-YYYY-NNNNN."""
    now = datetime.now(timezone.utc)
    prefix = f"LIT-{now.year}-"
    row = (await db.execute(text("""
        SELECT COUNT(*) + 1 as seq FROM disputes WHERE tenant_id = :tid AND numero LIKE :prefix
    """), {"tid": tid, "prefix": f"{prefix}%"})).first()
    seq = row.seq if row else 1
    return f"{prefix}{seq:05d}"


# ══════════════════════════════════════════════════════════════════
# MISSIONS CRUD
# ══════════════════════════════════════════════════════════════════

@router.get("", response_model=list[MissionOut])
async def list_missions(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
    statut: str | None = Query(None),
    client_id: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    sort_by: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    q = """SELECT j.*, rt.code AS source_template_code, rt.code AS route_numero, rr.code AS source_run_code
           FROM jobs j LEFT JOIN route_templates rt ON j.source_route_template_id = rt.id
           LEFT JOIN route_runs rr ON j.source_route_run_id = rr.id WHERE j.tenant_id = :tid"""
    params: dict = {"tid": str(tenant.tenant_id)}

    effective_status = statut or status
    if effective_status:
        # Match both legacy lowercase and new uppercase status values in DB
        new_to_legacy = {"BROUILLON": "draft", "PLANIFIEE": "planned", "AFFECTEE": "assigned",
                         "EN_COURS": "in_progress", "LIVREE": "delivered", "CLOTUREE": "closed"}
        legacy_to_new = {v: k for k, v in new_to_legacy.items()}
        if effective_status in new_to_legacy:
            # Caller sent uppercase → match both uppercase and legacy lowercase
            q += " AND j.status IN (:st1, :st2)"
            params["st1"] = effective_status
            params["st2"] = new_to_legacy[effective_status]
        elif effective_status in legacy_to_new:
            # Caller sent lowercase → match both lowercase and new uppercase
            q += " AND j.status IN (:st1, :st2)"
            params["st1"] = effective_status
            params["st2"] = legacy_to_new[effective_status]
        else:
            # Unknown status (e.g. FACTUREE, ANNULEE) — exact match
            q += " AND j.status = :status"
            params["status"] = effective_status

    if client_id:
        q += " AND j.customer_id = :cid"
        params["cid"] = client_id
    if search:
        q += " AND (j.reference ILIKE :search OR j.numero ILIKE :search OR j.reference_client ILIKE :search OR j.client_raison_sociale ILIKE :search)"
        params["search"] = f"%{search}%"

    allowed_sorts = {"created_at": "j.created_at", "numero": "j.numero", "montant_vente_ht": "j.montant_vente_ht", "date_chargement_prevue": "j.date_chargement_prevue", "date_livraison_prevue": "j.date_livraison_prevue"}
    sort_col = allowed_sorts.get(sort_by, "j.created_at")
    q += f" ORDER BY {sort_col} {order} LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_mission_from_row(r) for r in rows.fetchall()]


# Cross-mission disputes listing (must be before /{job_id} to avoid route conflict)
@router.get("/disputes", response_model=list[DisputeOut])
async def list_all_disputes(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    q = "SELECT * FROM disputes WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    q += " ORDER BY created_at DESC LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_dispute_from_row(r) for r in rows.fetchall()]


# Standalone dispute endpoint (must be before /{job_id} to avoid route conflict)
@router.get("/disputes/{dispute_id}", response_model=DisputeOut, include_in_schema=False)
async def get_dispute_standalone(
    dispute_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text(
        "SELECT * FROM disputes WHERE id = :id AND tenant_id = :tid"
    ), {"id": dispute_id, "tid": str(tenant.tenant_id)})).first()
    if not row:
        raise HTTPException(404, "Litige non trouve")
    return _dispute_from_row(row)


@router.get("/{job_id}", response_model=MissionDetail)
async def get_mission(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text("""
        SELECT j.*, rt.code AS source_template_code, rt.code AS route_numero, rr.code AS source_run_code
        FROM jobs j LEFT JOIN route_templates rt ON j.source_route_template_id = rt.id
        LEFT JOIN route_runs rr ON j.source_route_run_id = rr.id
        WHERE j.id = :id AND j.tenant_id = :tid
    """), {"id": job_id, "tid": str(tenant.tenant_id)})).first()
    if not row:
        raise HTTPException(404, "Mission non trouvee")

    base = _mission_from_row(row)

    # Load sub-entities
    dp_rows = (await db.execute(text(
        "SELECT * FROM mission_delivery_points WHERE mission_id = :mid AND tenant_id = :tid ORDER BY ordre"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).fetchall()

    goods_rows = (await db.execute(text(
        "SELECT * FROM mission_goods WHERE mission_id = :mid AND tenant_id = :tid"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).fetchall()

    pod_rows = (await db.execute(text(
        "SELECT * FROM proof_of_delivery WHERE mission_id = :mid AND tenant_id = :tid ORDER BY date_upload DESC"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).fetchall()

    dispute_rows = (await db.execute(text(
        "SELECT * FROM disputes WHERE mission_id = :mid AND tenant_id = :tid ORDER BY date_ouverture DESC"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).fetchall()

    return MissionDetail(
        **base.model_dump(),
        date_chargement_reelle=_ts(getattr(row, "date_chargement_reelle", None)),
        date_livraison_reelle=_ts(getattr(row, "date_livraison_reelle", None)),
        adresse_chargement_id=str(row.adresse_chargement_id) if getattr(row, "adresse_chargement_id", None) else None,
        adresse_chargement_contact=getattr(row, "adresse_chargement_contact", None),
        adresse_chargement_instructions=getattr(row, "adresse_chargement_instructions", None),
        notes_internes=getattr(row, "notes_internes", None),
        delivery_points=[_dp_from_row(r) for r in dp_rows],
        goods=[_goods_from_row(r) for r in goods_rows],
        pods=[_pod_from_row(r) for r in pod_rows],
        disputes=[_dispute_from_row(r) for r in dispute_rows],
    )


@router.post("", response_model=MissionOut, status_code=201)
async def create_mission(
    body: MissionCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    jid = uuid.uuid4()
    numero = await _gen_mission_numero(db, tid)

    # Resolve client name for denormalization
    client_rs = None
    cid = body.client_id
    if cid:
        crow = (await db.execute(text(
            "SELECT raison_sociale, name, statut FROM customers WHERE id = :id AND tenant_id = :tid"
        ), {"id": cid, "tid": tid})).first()
        if crow:
            # RG-C-001: client must be ACTIVE
            client_statut = getattr(crow, "statut", None) or "ACTIF"
            if client_statut not in ("ACTIF", None):
                raise HTTPException(400, "Ce client n'est pas actif. Impossible de creer une mission.")
            client_rs = crow.raison_sociale or crow.name

    await db.execute(text("""
        INSERT INTO jobs (
            id, tenant_id, agency_id, numero, reference, reference_client,
            customer_id, client_raison_sociale, type_mission, priorite, status,
            date_chargement_prevue, date_livraison_prevue,
            adresse_chargement_id, adresse_chargement_libre,
            adresse_chargement_contact, adresse_chargement_instructions,
            distance_estimee_km, montant_vente_ht,
            contraintes, notes_exploitation, notes_internes,
            pickup_address, delivery_address, pickup_date, delivery_date,
            distance_km, weight_kg, goods_description, notes,
            created_by, updated_by
        ) VALUES (
            :id, :tid, :aid, :numero, :ref, :ref_client,
            :cid, :crs, :type_m, :prio, 'BROUILLON',
            :dcp, :dlp,
            :aci, :acl, :acc, :aci2,
            :dek, :mvh,
            :contraintes, :ne, :ni,
            :pa, :da, :pd, :dd,
            :dk, :wk, :gd, :notes,
            :uid, :uid2
        )
    """), {
        "id": str(jid), "tid": tid,
        "aid": str(tenant.agency_id) if tenant.agency_id else None,
        "numero": numero, "ref": body.reference or body.reference_client,
        "ref_client": body.reference_client,
        "cid": cid, "crs": client_rs,
        "type_m": body.type_mission, "prio": body.priorite,
        "dcp": _parse_date(body.date_chargement_prevue or body.pickup_date),
        "dlp": _parse_date(body.date_livraison_prevue or body.delivery_date),
        "aci": body.adresse_chargement_id,
        "acl": json.dumps(body.adresse_chargement_libre) if body.adresse_chargement_libre else None,
        "acc": body.adresse_chargement_contact,
        "aci2": body.adresse_chargement_instructions,
        "dek": float(body.distance_estimee_km) if body.distance_estimee_km else (body.distance_km),
        "mvh": float(body.montant_vente_ht) if body.montant_vente_ht else None,
        "contraintes": json.dumps(body.contraintes) if body.contraintes else None,
        "ne": body.notes_exploitation, "ni": body.notes_internes,
        "pa": body.pickup_address, "da": body.delivery_address,
        "pd": _parse_date(body.pickup_date or body.date_chargement_prevue),
        "dd": _parse_date(body.delivery_date or body.date_livraison_prevue),
        "dk": body.distance_km or (float(body.distance_estimee_km) if body.distance_estimee_km else None),
        "wk": body.weight_kg, "gd": body.goods_description, "notes": body.notes,
        "uid": str(user["id"]) if isinstance(user, dict) and "id" in user else None,
        "uid2": str(user["id"]) if isinstance(user, dict) and "id" in user else None,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM jobs WHERE id = :id"), {"id": str(jid)})).first()
    return _mission_from_row(row)


@router.put("/{job_id}", response_model=MissionOut)
async def update_mission(
    job_id: str, body: MissionUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE jobs SET
            reference = COALESCE(:ref, reference),
            reference_client = COALESCE(:ref_client, reference_client),
            customer_id = COALESCE(:cid, customer_id),
            type_mission = COALESCE(:type_m, type_mission),
            priorite = COALESCE(:prio, priorite),
            date_chargement_prevue = COALESCE(:dcp, date_chargement_prevue),
            date_livraison_prevue = COALESCE(:dlp, date_livraison_prevue),
            adresse_chargement_libre = COALESCE(:acl, adresse_chargement_libre),
            adresse_chargement_contact = COALESCE(:acc, adresse_chargement_contact),
            adresse_chargement_instructions = COALESCE(:aci, adresse_chargement_instructions),
            distance_estimee_km = COALESCE(:dek, distance_estimee_km),
            montant_vente_ht = COALESCE(:mvh, montant_vente_ht),
            contraintes = COALESCE(:contraintes, contraintes),
            notes_exploitation = COALESCE(:ne, notes_exploitation),
            notes_internes = COALESCE(:ni, notes_internes),
            pickup_address = COALESCE(:pa, pickup_address),
            delivery_address = COALESCE(:da, delivery_address),
            pickup_date = COALESCE(:pd, pickup_date),
            delivery_date = COALESCE(:dd, delivery_date),
            distance_km = COALESCE(:dk, distance_km),
            weight_kg = COALESCE(:wk, weight_kg),
            goods_description = COALESCE(:gd, goods_description),
            notes = COALESCE(:notes, notes),
            updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid AND status IN ('draft', 'planned', 'BROUILLON', 'PLANIFIEE')
        RETURNING id
    """), {
        "id": job_id, "tid": str(tenant.tenant_id),
        "ref": body.reference, "ref_client": body.reference_client,
        "cid": body.client_id, "type_m": body.type_mission, "prio": body.priorite,
        "dcp": _parse_date(body.date_chargement_prevue), "dlp": _parse_date(body.date_livraison_prevue),
        "acl": json.dumps(body.adresse_chargement_libre) if body.adresse_chargement_libre else None,
        "acc": body.adresse_chargement_contact, "aci": body.adresse_chargement_instructions,
        "dek": float(body.distance_estimee_km) if body.distance_estimee_km else None,
        "mvh": float(body.montant_vente_ht) if body.montant_vente_ht else None,
        "contraintes": json.dumps(body.contraintes) if body.contraintes else None,
        "ne": body.notes_exploitation, "ni": body.notes_internes,
        "pa": body.pickup_address, "da": body.delivery_address,
        "pd": _parse_date(body.pickup_date), "dd": _parse_date(body.delivery_date),
        "dk": body.distance_km, "wk": body.weight_kg,
        "gd": body.goods_description, "notes": body.notes,
    })
    if not result.first():
        raise HTTPException(400, "Mission non trouvee ou ne peut pas etre modifiee dans ce statut")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM jobs WHERE id = :id"), {"id": job_id})).first()
    return _mission_from_row(row)


@router.post("/{job_id}/assign")
async def assign_mission(
    job_id: str,
    body: MissionAssign | None = None,
    driver_id: str | None = Query(None),
    vehicle_id: str | None = Query(None),
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Assign driver/vehicle or subcontractor. Supports both body and query params (legacy)."""
    tid = str(tenant.tenant_id)
    did = (body.driver_id if body else None) or driver_id
    vid = (body.vehicle_id if body else None) or vehicle_id
    trid = body.trailer_id if body else None
    sub_id = body.subcontractor_id if body else None
    is_sub = body.is_subcontracted if body else False
    montant_achat = float(body.montant_achat_ht) if body and body.montant_achat_ht else None

    # Check mission exists and is assignable
    mission = (await db.execute(text(
        "SELECT * FROM jobs WHERE id = :id AND tenant_id = :tid"
    ), {"id": job_id, "tid": tid})).first()
    if not mission:
        raise HTTPException(404, "Mission non trouvee")
    if mission.status not in ("planned", "assigned", "draft", "PLANIFIEE", "AFFECTEE", "BROUILLON"):
        raise HTTPException(400, "La mission ne peut pas etre affectee dans ce statut")

    # RG-C-016: subcontracted needs purchase amount
    if is_sub and not montant_achat:
        raise HTTPException(400, "Le montant d'achat sous-traitant est obligatoire.")

    # RG-C-010/011: check driver/vehicle are ACTIF
    if did:
        drv = (await db.execute(text(
            "SELECT statut, conformite_statut FROM drivers WHERE id = :id AND tenant_id = :tid"
        ), {"id": did, "tid": tid})).first()
        if drv:
            drv_statut = getattr(drv, "statut", None)
            if drv_statut and drv_statut != "ACTIF":
                raise HTTPException(400, "Ce conducteur ne peut pas etre affecte.")
    if vid:
        veh = (await db.execute(text(
            "SELECT statut, conformite_statut FROM vehicles WHERE id = :id AND tenant_id = :tid"
        ), {"id": vid, "tid": tid})).first()
        if veh:
            veh_statut = getattr(veh, "statut", None)
            if veh_statut and veh_statut != "ACTIF":
                raise HTTPException(400, "Ce vehicule ne peut pas etre affecte.")

    # RG-C: Check driver/vehicle overlap — non-blocking warnings
    warnings = []
    if did:
        overlap_drv = (await db.execute(text("""
            SELECT id, reference FROM jobs
            WHERE tenant_id = :tid AND driver_id = :did AND id != :jid
              AND status IN ('assigned','in_progress','AFFECTEE','EN_COURS')
              AND (date_chargement_prevue, COALESCE(date_livraison_prevue, date_chargement_prevue))
                  OVERLAPS
                  (
                    (SELECT date_chargement_prevue FROM jobs WHERE id = :jid),
                    (SELECT COALESCE(date_livraison_prevue, date_chargement_prevue) FROM jobs WHERE id = :jid)
                  )
        """), {"tid": tid, "did": did, "jid": job_id})).fetchall()
        for ov in overlap_drv:
            warnings.append(f"Conducteur deja affecte sur mission {ov.reference or str(ov.id)[:8]}")
    if vid:
        overlap_veh = (await db.execute(text("""
            SELECT id, reference FROM jobs
            WHERE tenant_id = :tid AND vehicle_id = :vid AND id != :jid
              AND status IN ('assigned','in_progress','AFFECTEE','EN_COURS')
              AND (date_chargement_prevue, COALESCE(date_livraison_prevue, date_chargement_prevue))
                  OVERLAPS
                  (
                    (SELECT date_chargement_prevue FROM jobs WHERE id = :jid),
                    (SELECT COALESCE(date_livraison_prevue, date_chargement_prevue) FROM jobs WHERE id = :jid)
                  )
        """), {"tid": tid, "vid": vid, "jid": job_id})).fetchall()
        for ov in overlap_veh:
            warnings.append(f"Vehicule deja affecte sur mission {ov.reference or str(ov.id)[:8]}")

    # Calculate margin if we have both amounts
    vente = float(mission.montant_vente_ht) if mission.montant_vente_ht else None
    marge = None
    if vente and montant_achat:
        marge = vente - montant_achat

    await db.execute(text("""
        UPDATE jobs SET
            driver_id = COALESCE(:did, driver_id),
            vehicle_id = COALESCE(:vid, vehicle_id),
            trailer_id = COALESCE(:trid, trailer_id),
            subcontractor_id = COALESCE(:sub_id, subcontractor_id),
            is_subcontracted = :is_sub,
            montant_achat_ht = COALESCE(:mah, montant_achat_ht),
            marge_brute = COALESCE(:marge, marge_brute),
            status = 'AFFECTEE',
            updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": job_id, "tid": tid,
        "did": did, "vid": vid, "trid": trid, "sub_id": sub_id,
        "is_sub": is_sub, "mah": montant_achat, "marge": marge,
    })
    await db.commit()
    result = {"status": "AFFECTEE", "statut": "AFFECTEE"}
    if warnings:
        result["warnings"] = warnings
    return result


@router.delete("/{job_id}/assign")
async def unassign_mission(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE jobs SET driver_id = NULL, vehicle_id = NULL, trailer_id = NULL,
            subcontractor_id = NULL, is_subcontracted = false,
            status = 'PLANIFIEE', updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid AND status IN ('assigned', 'AFFECTEE')
        RETURNING id
    """), {"id": job_id, "tid": str(tenant.tenant_id)})
    if not result.first():
        raise HTTPException(400, "Mission non trouvee ou ne peut pas etre desaffectee")
    await db.commit()
    return {"status": "PLANIFIEE", "statut": "PLANIFIEE"}


@router.post("/{job_id}/transition")
async def transition_mission(
    job_id: str,
    target_status: str | None = Query(None),
    body: MissionStatusChange | None = None,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change mission status. Supports both query param and body."""
    target = (body.statut if body else None) or target_status
    if not target:
        raise HTTPException(400, "Statut cible requis")

    tid = str(tenant.tenant_id)
    row = (await db.execute(
        text("SELECT status, pod_s3_key FROM jobs WHERE id = :id AND tenant_id = :tid"),
        {"id": job_id, "tid": tid},
    )).first()
    if not row:
        raise HTTPException(404, "Mission non trouvee")

    current = row.status
    # Normalize current status to uppercase for transition lookup
    legacy_to_new = {"draft": "BROUILLON", "planned": "PLANIFIEE", "assigned": "AFFECTEE",
                     "in_progress": "EN_COURS", "delivered": "LIVREE", "closed": "CLOTUREE"}
    current_norm = legacy_to_new.get(current, current)
    target_norm = legacy_to_new.get(target, target)

    # Check transitions using both normalized and raw forms
    allowed = VALID_TRANSITIONS.get(current_norm, VALID_TRANSITIONS.get(current, []))
    if target_norm not in allowed and target not in allowed:
        raise HTTPException(400, f"Transition impossible de {current_norm} vers {target_norm}")

    # Always write uppercase status
    target = target_norm

    # RG-C-024: close requires valid POD
    if target in ("closed", "CLOTUREE"):
        pod_row = (await db.execute(text(
            "SELECT id FROM proof_of_delivery WHERE mission_id = :mid AND tenant_id = :tid AND statut = 'VALIDE'"
        ), {"mid": job_id, "tid": tid})).first()
        has_legacy_pod = row.pod_s3_key
        if not pod_row and not has_legacy_pod:
            raise HTTPException(400, "Un POD valide est requis pour cloturer la mission.")

    extra_sql = ""
    if target in ("delivered", "LIVREE"):
        extra_sql = ", date_livraison_reelle = NOW()"
    elif target in ("closed", "CLOTUREE"):
        extra_sql = ", closed_at = NOW(), date_cloture = NOW()"
    elif target in ("in_progress", "EN_COURS"):
        extra_sql = ", date_chargement_reelle = NOW()"

    await db.execute(text(f"""
        UPDATE jobs SET status = :s, updated_at = NOW(){extra_sql} WHERE id = :id
    """), {"id": job_id, "s": target})

    # Audit trail for status transitions
    from app.core.audit import log_audit
    import uuid as _uuid
    await log_audit(
        db, tenant_id=_uuid.UUID(tid),
        user_id=_uuid.UUID(user["id"]) if user.get("id") else None,
        user_email=user.get("email"),
        action="mission_transition",
        entity_type="mission",
        entity_id=job_id,
        old_value={"status": current},
        new_value={"status": target},
    )

    await db.commit()

    return {"status": target, "statut": target}


# Legacy close endpoint
@router.post("/{job_id}/close")
async def close_mission(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT status, pod_s3_key FROM jobs WHERE id = :id AND tenant_id = :tid"),
        {"id": job_id, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "Mission non trouvee")
    if row.status not in ("delivered", "LIVREE"):
        raise HTTPException(400, "La mission doit etre au statut 'livree' pour etre cloturee")

    # Check for valid POD (new system or legacy)
    pod_row = (await db.execute(text(
        "SELECT id FROM proof_of_delivery WHERE mission_id = :mid AND tenant_id = :tid AND statut = 'VALIDE'"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).first()
    if not pod_row and not row.pod_s3_key:
        raise HTTPException(400, "POD must be uploaded before closing the job")

    await db.execute(text("""
        UPDATE jobs SET status='CLOTUREE', closed_at=NOW(), date_cloture=NOW(), updated_at=NOW() WHERE id=:id
    """), {"id": job_id})
    await db.commit()
    return {"status": "CLOTUREE", "statut": "CLOTUREE"}


# Legacy POD upload (simple s3_key)
@router.post("/{job_id}/pod")
async def upload_pod_legacy(
    job_id: str,
    s3_key: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE jobs SET pod_s3_key=:key, pod_uploaded_at=NOW(), updated_at=NOW()
        WHERE id=:id AND tenant_id=:tid AND status IN ('in_progress','delivered','EN_COURS','LIVREE')
        RETURNING id
    """), {"id": job_id, "tid": str(tenant.tenant_id), "key": s3_key})
    if not result.first():
        raise HTTPException(400, "Mission non trouvee ou POD ne peut pas etre uploade dans ce statut")
    await db.commit()
    return {"status": "pod_uploaded"}


# ══════════════════════════════════════════════════════════════════
# DELIVERY POINTS
# ══════════════════════════════════════════════════════════════════

@router.get("/{job_id}/delivery-points", response_model=list[DeliveryPointOut])
async def list_delivery_points(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text(
        "SELECT * FROM mission_delivery_points WHERE mission_id = :mid AND tenant_id = :tid ORDER BY ordre"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).fetchall()
    return [_dp_from_row(r) for r in rows]


@router.post("/{job_id}/delivery-points", response_model=DeliveryPointOut, status_code=201)
async def add_delivery_point(
    job_id: str, body: DeliveryPointCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    dpid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO mission_delivery_points (
            id, tenant_id, mission_id, ordre, adresse_id, adresse_libre,
            contact_nom, contact_telephone, date_livraison_prevue, instructions
        ) VALUES (:id, :tid, :mid, :ordre, :aid, :al, :cn, :ct, :dlp, :inst)
    """), {
        "id": str(dpid), "tid": tid, "mid": job_id,
        "ordre": body.ordre, "aid": body.adresse_id,
        "al": json.dumps(body.adresse_libre) if body.adresse_libre else None,
        "cn": body.contact_nom, "ct": body.contact_telephone,
        "dlp": _parse_date(body.date_livraison_prevue), "inst": body.instructions,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM mission_delivery_points WHERE id = :id"), {"id": str(dpid)})).first()
    return _dp_from_row(row)


@router.patch("/{job_id}/delivery-points/{dp_id}/status")
async def update_dp_status(
    job_id: str, dp_id: str, body: DeliveryPointStatusChange,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    extra = ""
    params = {"id": dp_id, "tid": str(tenant.tenant_id), "s": body.statut, "mf": body.motif_echec}
    if body.statut == "LIVRE":
        extra = ", date_livraison_reelle = NOW()"
    await db.execute(text(f"""
        UPDATE mission_delivery_points SET statut = :s, motif_echec = :mf, updated_at = NOW(){extra}
        WHERE id = :id AND tenant_id = :tid
    """), params)
    await db.commit()
    return {"statut": body.statut}


# ══════════════════════════════════════════════════════════════════
# GOODS
# ══════════════════════════════════════════════════════════════════

@router.get("/{job_id}/goods", response_model=list[GoodsOut])
async def list_goods(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text(
        "SELECT * FROM mission_goods WHERE mission_id = :mid AND tenant_id = :tid"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).fetchall()
    return [_goods_from_row(r) for r in rows]


@router.post("/{job_id}/goods", response_model=GoodsOut, status_code=201)
async def add_goods(
    job_id: str, body: GoodsCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    gid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO mission_goods (
            id, tenant_id, mission_id, delivery_point_id,
            description, nature, quantite, unite, poids_brut_kg, poids_net_kg,
            volume_m3, longueur_m, largeur_m, hauteur_m,
            valeur_declaree_eur, adr_classe, adr_numero_onu, adr_designation,
            temperature_min, temperature_max, references_colis
        ) VALUES (
            :id, :tid, :mid, :dpid,
            :desc, :nat, :qty, :unit, :pbk, :pnk,
            :vol, :lm, :wm, :hm,
            :vd, :adrc, :adrn, :adrd,
            :tmin, :tmax, :refs
        )
    """), {
        "id": str(gid), "tid": tid, "mid": job_id,
        "dpid": body.delivery_point_id,
        "desc": body.description, "nat": body.nature,
        "qty": float(body.quantite), "unit": body.unite,
        "pbk": float(body.poids_brut_kg),
        "pnk": float(body.poids_net_kg) if body.poids_net_kg else None,
        "vol": float(body.volume_m3) if body.volume_m3 else None,
        "lm": float(body.longueur_m) if body.longueur_m else None,
        "wm": float(body.largeur_m) if body.largeur_m else None,
        "hm": float(body.hauteur_m) if body.hauteur_m else None,
        "vd": float(body.valeur_declaree_eur) if body.valeur_declaree_eur else None,
        "adrc": body.adr_classe, "adrn": body.adr_numero_onu, "adrd": body.adr_designation,
        "tmin": float(body.temperature_min) if body.temperature_min else None,
        "tmax": float(body.temperature_max) if body.temperature_max else None,
        "refs": json.dumps(body.references_colis) if body.references_colis else None,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM mission_goods WHERE id = :id"), {"id": str(gid)})).first()
    return _goods_from_row(row)


# ══════════════════════════════════════════════════════════════════
# POD (Proof of Delivery)
# ══════════════════════════════════════════════════════════════════

@router.get("/{job_id}/pods", response_model=list[PodOut])
async def list_pods(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text(
        "SELECT * FROM proof_of_delivery WHERE mission_id = :mid AND tenant_id = :tid ORDER BY date_upload DESC"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).fetchall()
    return [_pod_from_row(r) for r in rows]


@router.post("/{job_id}/pods", response_model=PodOut, status_code=201)
async def create_pod(
    job_id: str, body: PodCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    # RG-C-022: only LIVREE or EN_COURS
    mission = (await db.execute(text(
        "SELECT status FROM jobs WHERE id = :id AND tenant_id = :tid"
    ), {"id": job_id, "tid": tid})).first()
    if not mission:
        raise HTTPException(404, "Mission non trouvee")
    if mission.status not in ("in_progress", "delivered", "EN_COURS", "LIVREE"):
        raise HTTPException(400, "La mission n'est pas dans un statut permettant l'upload de POD.")

    pid = uuid.uuid4()
    uid = str(user["id"]) if isinstance(user, dict) and "id" in user else str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO proof_of_delivery (
            id, tenant_id, mission_id, delivery_point_id,
            type, fichier_s3_key, fichier_nom_original,
            fichier_taille_octets, fichier_mime_type,
            uploaded_by, uploaded_by_role,
            geoloc_latitude, geoloc_longitude, geoloc_precision_m,
            has_reserves, reserves_texte, reserves_categorie
        ) VALUES (
            :id, :tid, :mid, :dpid,
            :type, :s3k, :fname, :fsize, :fmime,
            :uid, :role,
            :glat, :glon, :gprec,
            :hr, :rt, :rc
        )
    """), {
        "id": str(pid), "tid": tid, "mid": job_id, "dpid": body.delivery_point_id,
        "type": body.type, "s3k": body.fichier_s3_key, "fname": body.fichier_nom_original,
        "fsize": body.fichier_taille_octets, "fmime": body.fichier_mime_type,
        "uid": uid, "role": "EXPLOITATION",
        "glat": float(body.geoloc_latitude) if body.geoloc_latitude else None,
        "glon": float(body.geoloc_longitude) if body.geoloc_longitude else None,
        "gprec": body.geoloc_precision_m,
        "hr": body.has_reserves, "rt": body.reserves_texte, "rc": body.reserves_categorie,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM proof_of_delivery WHERE id = :id"), {"id": str(pid)})).first()
    return _pod_from_row(row)


@router.patch("/{job_id}/pods/{pod_id}", response_model=PodOut)
async def validate_pod(
    job_id: str, pod_id: str, body: PodValidation,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = str(user["id"]) if isinstance(user, dict) and "id" in user else None
    await db.execute(text("""
        UPDATE proof_of_delivery SET
            statut = :s, date_validation = NOW(), validated_by = :uid,
            motif_rejet = :mr, updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": pod_id, "tid": str(tenant.tenant_id),
        "s": body.statut, "uid": uid, "mr": body.motif_rejet,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM proof_of_delivery WHERE id = :id"), {"id": pod_id})).first()
    return _pod_from_row(row)


# ══════════════════════════════════════════════════════════════════
# DISPUTES
# ══════════════════════════════════════════════════════════════════

@router.get("/{job_id}/disputes", response_model=list[DisputeOut])
async def list_disputes(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text(
        "SELECT * FROM disputes WHERE mission_id = :mid AND tenant_id = :tid ORDER BY date_ouverture DESC"
    ), {"mid": job_id, "tid": str(tenant.tenant_id)})).fetchall()
    return [_dispute_from_row(r) for r in rows]


@router.post("/{job_id}/disputes", response_model=DisputeOut, status_code=201)
async def create_dispute(
    job_id: str, body: DisputeCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    # RG-C-030: only on LIVREE, CLOTUREE, FACTUREE
    mission = (await db.execute(text(
        "SELECT status, montant_vente_ht FROM jobs WHERE id = :id AND tenant_id = :tid"
    ), {"id": job_id, "tid": tid})).first()
    if not mission:
        raise HTTPException(404, "Mission non trouvee")
    if mission.status not in ("delivered", "closed", "LIVREE", "CLOTUREE", "FACTUREE", "invoiced"):
        raise HTTPException(400, "Un litige ne peut etre cree que sur une mission livree ou cloturee.")

    # RG-C-031: amount <= mission sale amount
    if body.montant_estime_eur and mission.montant_vente_ht:
        if float(body.montant_estime_eur) > float(mission.montant_vente_ht):
            raise HTTPException(400, "Le montant estime du litige depasse le montant de la mission.")

    did = uuid.uuid4()
    numero = await _gen_dispute_numero(db, tid)
    uid = str(user["id"]) if isinstance(user, dict) and "id" in user else str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO disputes (
            id, tenant_id, numero, mission_id,
            type, description, responsabilite, responsable_entity_id,
            montant_estime_eur, opened_by, assigned_to, notes_internes
        ) VALUES (
            :id, :tid, :num, :mid,
            :type, :desc, :resp, :reid,
            :me, :uid, :ato, :ni
        )
    """), {
        "id": str(did), "tid": tid, "num": numero, "mid": job_id,
        "type": body.type, "desc": body.description,
        "resp": body.responsabilite,
        "reid": body.responsable_entity_id,
        "me": float(body.montant_estime_eur) if body.montant_estime_eur else None,
        "uid": uid, "ato": body.assigned_to, "ni": body.notes_internes,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM disputes WHERE id = :id"), {"id": str(did)})).first()
    return _dispute_from_row(row)


@router.patch("/{job_id}/disputes/{dispute_id}", response_model=DisputeOut)
async def update_dispute(
    job_id: str, dispute_id: str, body: DisputeUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)

    # RG-C-032: closed disputes cannot be reopened
    existing = (await db.execute(text(
        "SELECT statut FROM disputes WHERE id = :id AND tenant_id = :tid"
    ), {"id": dispute_id, "tid": tid})).first()
    if not existing:
        raise HTTPException(404, "Litige non trouve")
    closed_statuts = {"CLOS_ACCEPTE", "CLOS_REFUSE", "CLOS_SANS_SUITE"}
    if existing.statut in closed_statuts and body.statut and body.statut not in closed_statuts:
        raise HTTPException(400, "Un litige clos ne peut pas etre rouvert.")

    extra_date = ""
    if body.statut and body.statut in closed_statuts:
        extra_date = ", date_resolution = NOW()"

    await db.execute(text(f"""
        UPDATE disputes SET
            statut = COALESCE(:s, statut),
            description = COALESCE(:desc, description),
            responsabilite = COALESCE(:resp, responsabilite),
            montant_estime_eur = COALESCE(:me, montant_estime_eur),
            montant_retenu_eur = COALESCE(:mr, montant_retenu_eur),
            resolution_texte = COALESCE(:rt, resolution_texte),
            impact_facturation = COALESCE(:impact, impact_facturation),
            assigned_to = COALESCE(:ato, assigned_to),
            notes_internes = COALESCE(:ni, notes_internes),
            updated_at = NOW(){extra_date}
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": dispute_id, "tid": tid,
        "s": body.statut, "desc": body.description, "resp": body.responsabilite,
        "me": float(body.montant_estime_eur) if body.montant_estime_eur else None,
        "mr": float(body.montant_retenu_eur) if body.montant_retenu_eur else None,
        "rt": body.resolution_texte, "impact": body.impact_facturation,
        "ato": body.assigned_to, "ni": body.notes_internes,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM disputes WHERE id = :id"), {"id": dispute_id})).first()
    return _dispute_from_row(row)


@router.post("/{job_id}/disputes/{dispute_id}/attachments", response_model=DisputeAttachmentOut, status_code=201)
async def add_dispute_attachment(
    job_id: str, dispute_id: str, body: DisputeAttachmentCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    aid = uuid.uuid4()
    uid = str(user["id"]) if isinstance(user, dict) and "id" in user else str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO dispute_attachments (
            id, tenant_id, dispute_id,
            fichier_s3_key, fichier_nom_original,
            fichier_taille_octets, fichier_mime_type,
            description, uploaded_by
        ) VALUES (:id, :tid, :did, :s3k, :fname, :fsize, :fmime, :desc, :uid)
    """), {
        "id": str(aid), "tid": tid, "did": dispute_id,
        "s3k": body.fichier_s3_key, "fname": body.fichier_nom_original,
        "fsize": body.fichier_taille_octets, "fmime": body.fichier_mime_type,
        "desc": body.description, "uid": uid,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM dispute_attachments WHERE id = :id"), {"id": str(aid)})).first()
    return DisputeAttachmentOut(
        id=str(row.id), dispute_id=str(row.dispute_id),
        fichier_s3_key=row.fichier_s3_key, fichier_nom_original=row.fichier_nom_original,
        fichier_taille_octets=row.fichier_taille_octets, fichier_mime_type=row.fichier_mime_type,
        description=row.description,
        uploaded_by=str(row.uploaded_by) if row.uploaded_by else None,
        created_at=_ts(row.created_at),
    )


# ── Planning endpoints ───────────────────────────────────────────

@router.get("/planning/drivers")
async def planning_drivers(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
):
    """Return drivers with their assigned missions in a date range."""
    tid = str(tenant.tenant_id)
    params: dict = {"tid": tid}
    date_filter = ""
    if date_from:
        date_filter += " AND j.date_chargement_prevue >= :dfrom"
        params["dfrom"] = date_from
    if date_to:
        date_filter += " AND j.date_livraison_prevue <= :dto"
        params["dto"] = date_to

    rows = await db.execute(text(f"""
        SELECT d.id AS driver_id,
               COALESCE(d.nom, d.last_name, '') AS driver_nom,
               COALESCE(d.prenom, d.first_name, '') AS driver_prenom,
               j.id AS mission_id, j.numero, j.status,
               j.date_chargement_prevue, j.date_livraison_prevue,
               j.client_raison_sociale
        FROM drivers d
        LEFT JOIN jobs j ON j.driver_id = d.id AND j.tenant_id = :tid
            AND j.status NOT IN ('draft', 'BROUILLON', 'ANNULEE')
            {date_filter}
        WHERE d.tenant_id = :tid AND COALESCE(d.statut, 'ACTIF') = 'ACTIF'
        ORDER BY d.nom, j.date_chargement_prevue
    """), params)

    drivers_map: dict = {}
    for r in rows.fetchall():
        did = str(r.driver_id)
        if did not in drivers_map:
            drivers_map[did] = {
                "driver_id": did,
                "nom": r.driver_nom,
                "prenom": r.driver_prenom,
                "missions": [],
            }
        if r.mission_id:
            drivers_map[did]["missions"].append({
                "mission_id": str(r.mission_id),
                "numero": r.numero,
                "status": r.status,
                "date_chargement_prevue": _ts(r.date_chargement_prevue),
                "date_livraison_prevue": _ts(r.date_livraison_prevue),
                "client": r.client_raison_sociale,
            })
    return list(drivers_map.values())


@router.get("/planning/vehicles")
async def planning_vehicles(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
):
    """Return vehicles with their assigned missions in a date range."""
    tid = str(tenant.tenant_id)
    params: dict = {"tid": tid}
    date_filter = ""
    if date_from:
        date_filter += " AND j.date_chargement_prevue >= :dfrom"
        params["dfrom"] = date_from
    if date_to:
        date_filter += " AND j.date_livraison_prevue <= :dto"
        params["dto"] = date_to

    rows = await db.execute(text(f"""
        SELECT v.id AS vehicle_id,
               COALESCE(v.immatriculation, v.plate_number, '') AS immatriculation,
               v.marque, v.modele,
               j.id AS mission_id, j.numero, j.status,
               j.date_chargement_prevue, j.date_livraison_prevue,
               j.client_raison_sociale
        FROM vehicles v
        LEFT JOIN jobs j ON j.vehicle_id = v.id AND j.tenant_id = :tid
            AND j.status NOT IN ('draft', 'BROUILLON', 'ANNULEE')
            {date_filter}
        WHERE v.tenant_id = :tid AND COALESCE(v.statut, 'ACTIF') = 'ACTIF'
        ORDER BY v.immatriculation, j.date_chargement_prevue
    """), params)

    vehicles_map: dict = {}
    for r in rows.fetchall():
        vid = str(r.vehicle_id)
        if vid not in vehicles_map:
            vehicles_map[vid] = {
                "vehicle_id": vid,
                "immatriculation": r.immatriculation,
                "marque": r.marque,
                "modele": r.modele,
                "missions": [],
            }
        if r.mission_id:
            vehicles_map[vid]["missions"].append({
                "mission_id": str(r.mission_id),
                "numero": r.numero,
                "status": r.status,
                "date_chargement_prevue": _ts(r.date_chargement_prevue),
                "date_livraison_prevue": _ts(r.date_livraison_prevue),
                "client": r.client_raison_sociale,
            })
    return list(vehicles_map.values())


# ══════════════════════════════════════════════════════════════════
# CMR (LETTRE DE VOITURE) GENERATION
# ══════════════════════════════════════════════════════════════════

@router.post("/{job_id}/generate-cmr")
async def generate_cmr(
    job_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a CMR (Lettre de Voiture) PDF for a mission, upload to S3, and return the key."""
    tid = str(tenant.tenant_id)

    # Load mission
    mission = (await db.execute(
        text("SELECT * FROM jobs WHERE id = :id AND tenant_id = :tid"),
        {"id": job_id, "tid": tid},
    )).first()
    if not mission:
        raise HTTPException(404, "Mission not found")

    # Load delivery points
    delivery_points = (await db.execute(
        text("SELECT * FROM mission_delivery_points WHERE mission_id = :mid AND tenant_id = :tid ORDER BY ordre"),
        {"mid": job_id, "tid": tid},
    )).fetchall()

    # Load goods
    goods = (await db.execute(
        text("SELECT * FROM mission_goods WHERE mission_id = :mid AND tenant_id = :tid ORDER BY created_at"),
        {"mid": job_id, "tid": tid},
    )).fetchall()

    # Load customer
    customer = None
    if mission.customer_id:
        customer = (await db.execute(
            text("SELECT * FROM customers WHERE id = :id"),
            {"id": str(mission.customer_id)},
        )).first()

    # Load company settings (prefer company_settings over tenants for full details)
    company = (await db.execute(
        text("SELECT * FROM company_settings WHERE tenant_id = :id"),
        {"id": tid},
    )).first()
    if not company:
        company = (await db.execute(
            text("SELECT * FROM tenants WHERE id = :id"),
            {"id": tid},
        )).first()

    # Load driver
    driver = None
    if mission.driver_id:
        driver = (await db.execute(
            text("SELECT * FROM drivers WHERE id = :id"),
            {"id": str(mission.driver_id)},
        )).first()

    # Load vehicle
    vehicle = None
    if mission.vehicle_id:
        vehicle = (await db.execute(
            text("SELECT * FROM vehicles WHERE id = :id"),
            {"id": str(mission.vehicle_id)},
        )).first()

    # Generate CMR numero
    cmr_numero = getattr(mission, "cmr_numero", None)
    if not cmr_numero:
        mission_numero = getattr(mission, "numero", None) or getattr(mission, "reference", "") or ""
        cmr_numero = f"CMR-{mission_numero}" if mission_numero else f"CMR-{job_id[:8].upper()}"

    # Generate PDF
    from app.modules.jobs.cmr_service import generate_cmr_pdf
    pdf_bytes = generate_cmr_pdf(mission, delivery_points, goods, customer, company, driver, vehicle)

    # Upload to S3
    from app.infra.s3 import _get_s3_client
    from app.core.settings import settings
    s3 = _get_s3_client()
    s3_key = f"{tid}/cmr/{cmr_numero}.pdf"
    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=s3_key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )

    # Update mission with CMR info
    await db.execute(text("""
        UPDATE jobs SET cmr_s3_key = :s3key, cmr_numero = :num, updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid
    """), {"s3key": s3_key, "num": cmr_numero, "id": job_id, "tid": tid})
    await db.commit()

    return {
        "cmr_numero": cmr_numero,
        "s3_key": s3_key,
        "mission_id": job_id,
    }
