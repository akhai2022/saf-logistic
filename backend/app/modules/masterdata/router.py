"""Module B — Referentiels Metier: full CRUD for Clients, Subcontractors, Drivers, Vehicles."""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.core.validators import validate_nir, validate_vin
from app.modules.masterdata.schemas import (
    ClientAddressCreate,
    ClientAddressOut,
    ClientContactCreate,
    ClientContactOut,
    ClientCreate,
    ClientDetail,
    ClientOut,
    ClientUpdate,
    DriverCreate,
    DriverDetail,
    DriverOut,
    DriverUpdate,
    StatusChange,
    SubcontractorContractCreate,
    SubcontractorContractOut,
    SubcontractorCreate,
    SubcontractorDetail,
    SubcontractorOut,
    SubcontractorUpdate,
    VehicleCreate,
    VehicleDetail,
    VehicleOut,
    VehicleUpdate,
)

router = APIRouter(prefix="/v1/masterdata", tags=["masterdata"])


# ══════════════════════════════════════════════════════════════════
# CLIENTS
# ══════════════════════════════════════════════════════════════════

def _client_from_row(r) -> ClientOut:
    return ClientOut(
        id=str(r.id),
        code=r.code,
        raison_sociale=r.raison_sociale,
        nom_commercial=getattr(r, "nom_commercial", None),
        siret=getattr(r, "siret", None),
        siren=r.siren,
        tva_intracom=getattr(r, "tva_intracom", None),
        code_naf=getattr(r, "code_naf", None),
        adresse_facturation_ligne1=getattr(r, "adresse_facturation_ligne1", None),
        adresse_facturation_ligne2=getattr(r, "adresse_facturation_ligne2", None),
        adresse_facturation_cp=getattr(r, "adresse_facturation_cp", None),
        adresse_facturation_ville=getattr(r, "adresse_facturation_ville", None),
        adresse_facturation_pays=getattr(r, "adresse_facturation_pays", None),
        telephone=getattr(r, "telephone", None),
        email=getattr(r, "email", None),
        site_web=getattr(r, "site_web", None),
        delai_paiement_jours=getattr(r, "delai_paiement_jours", None) or r.payment_terms_days,
        mode_paiement=getattr(r, "mode_paiement", None),
        condition_paiement_texte=getattr(r, "condition_paiement_texte", None),
        escompte_pourcent=getattr(r, "escompte_pourcent", None),
        penalite_retard_pourcent=getattr(r, "penalite_retard_pourcent", None),
        indemnite_recouvrement=getattr(r, "indemnite_recouvrement", None),
        plafond_encours=getattr(r, "plafond_encours", None),
        statut=getattr(r, "statut", None) or ("ACTIF" if r.is_active else "INACTIF"),
        notes=getattr(r, "notes", None),
        date_debut_relation=getattr(r, "date_debut_relation", None),
        agency_ids=getattr(r, "agency_ids", None),
        created_at=getattr(r, "created_at", None),
        updated_at=getattr(r, "updated_at", None),
        # Legacy
        name=r.name,
        is_active=r.is_active,
    )


@router.get("/clients", response_model=list[ClientOut])
@router.get("/customers", response_model=list[ClientOut], include_in_schema=False)
async def list_clients(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    search: str | None = Query(None),
    agency_id: str | None = Query(None),
    active_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    q = "SELECT * FROM customers WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    elif active_only:
        q += " AND is_active = true"
    if search:
        q += " AND (raison_sociale ILIKE :search OR name ILIKE :search OR code ILIKE :search OR siret ILIKE :search)"
        params["search"] = f"%{search}%"
    if agency_id:
        q += " AND agency_ids @> CAST(:agency_id AS jsonb)"
        params["agency_id"] = json.dumps([agency_id])
    q += " ORDER BY COALESCE(raison_sociale, name) LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_client_from_row(r) for r in rows.fetchall()]


@router.get("/clients/{cid}", response_model=ClientDetail)
@router.get("/customers/{cid}", response_model=ClientDetail, include_in_schema=False)
async def get_client(
    cid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT * FROM customers WHERE id = :id AND tenant_id = :tid"),
        {"id": cid, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "Client not found")
    # Get contacts
    contacts_rows = (await db.execute(
        text("SELECT * FROM client_contacts WHERE client_id = :cid AND tenant_id = :tid ORDER BY is_contact_principal DESC, nom"),
        {"cid": cid, "tid": str(tenant.tenant_id)},
    )).fetchall()
    contacts = [
        ClientContactOut(
            id=str(c.id), client_id=str(c.client_id),
            civilite=c.civilite, nom=c.nom, prenom=c.prenom, fonction=c.fonction,
            email=c.email, telephone_fixe=c.telephone_fixe, telephone_mobile=c.telephone_mobile,
            is_contact_principal=c.is_contact_principal, is_contact_facturation=c.is_contact_facturation,
            is_contact_exploitation=c.is_contact_exploitation, notes=c.notes, is_active=c.is_active,
            created_at=c.created_at, updated_at=c.updated_at,
        ) for c in contacts_rows
    ]
    # Get addresses
    addr_rows = (await db.execute(
        text("SELECT * FROM client_addresses WHERE client_id = :cid AND tenant_id = :tid ORDER BY libelle"),
        {"cid": cid, "tid": str(tenant.tenant_id)},
    )).fetchall()
    addresses = [
        ClientAddressOut(
            id=str(a.id), client_id=str(a.client_id),
            libelle=a.libelle, type=a.type, adresse_ligne1=a.adresse_ligne1,
            adresse_ligne2=a.adresse_ligne2, code_postal=a.code_postal, ville=a.ville,
            pays=a.pays, latitude=a.latitude, longitude=a.longitude,
            contact_site_nom=a.contact_site_nom, contact_site_telephone=a.contact_site_telephone,
            horaires_ouverture=a.horaires_ouverture, instructions_acces=a.instructions_acces,
            contraintes=a.contraintes, is_active=a.is_active,
            created_at=a.created_at, updated_at=a.updated_at,
        ) for a in addr_rows
    ]
    out = _client_from_row(row)
    return ClientDetail(**out.model_dump(), contacts=contacts, addresses=addresses)


@router.post("/clients", response_model=ClientOut, status_code=201)
@router.post("/customers", response_model=ClientOut, status_code=201, include_in_schema=False)
async def create_client(
    body: ClientCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = uuid.uuid4()
    # Auto-generate code if not provided
    code = body.code
    if not code:
        row = (await db.execute(
            text("SELECT COUNT(*) AS cnt FROM customers WHERE tenant_id = :tid"),
            {"tid": str(tenant.tenant_id)},
        )).first()
        code = f"CLI-{(row.cnt + 1):03d}"

    # RG-B-001: check code uniqueness
    existing = (await db.execute(
        text("SELECT id FROM customers WHERE tenant_id = :tid AND code = :code"),
        {"tid": str(tenant.tenant_id), "code": code},
    )).first()
    if existing:
        raise HTTPException(409, "Ce code client existe deja.")

    # LME validation: max 60 days net, max 45 days fin de mois
    if body.delai_paiement_jours and body.delai_paiement_jours > 60:
        raise HTTPException(422, "Delai de paiement LME: maximum 60 jours nets date de facture")
    if body.mode_paiement and "FIN_DE_MOIS" in (body.mode_paiement or "").upper():
        if body.delai_paiement_jours and body.delai_paiement_jours > 45:
            raise HTTPException(422, "Delai de paiement LME: maximum 45 jours fin de mois")

    siren = body.siret[:9] if body.siret and len(body.siret) >= 9 else None

    await db.execute(text("""
        INSERT INTO customers (
            id, tenant_id, name, siren, address, contact_name, contact_email, contact_phone, payment_terms_days,
            code, raison_sociale, nom_commercial, siret, tva_intracom, code_naf,
            adresse_facturation_ligne1, adresse_facturation_ligne2,
            adresse_facturation_cp, adresse_facturation_ville, adresse_facturation_pays,
            telephone, email, site_web,
            delai_paiement_jours, mode_paiement, condition_paiement_texte,
            escompte_pourcent, penalite_retard_pourcent, indemnite_recouvrement,
            plafond_encours, sla_delai_livraison_heures, sla_taux_service_pourcent, sla_penalite_texte,
            agency_ids, notes, statut, date_debut_relation,
            created_by, updated_by
        ) VALUES (
            :id, :tid, :name, :siren, :addr, :cn, :ce, :cp, :pt,
            :code, :raison_sociale, :nom_commercial, :siret, :tva_intracom, :code_naf,
            :afl1, :afl2, :afcp, :afville, :afpays,
            :tel, :email, :site_web,
            :dpj, :mp, :cpt,
            :escompte, :penalite, :indemnite,
            :plafond, :sla_delai, :sla_taux, :sla_pen,
            CAST(:agency_ids AS jsonb), :notes, :statut, :ddr,
            :uid, :uid2
        )
    """), {
        "id": str(cid), "tid": str(tenant.tenant_id),
        "name": body.raison_sociale, "siren": siren,
        "addr": body.adresse_facturation_ligne1, "cn": None, "ce": body.email, "cp": body.telephone,
        "pt": body.delai_paiement_jours,
        "code": code, "raison_sociale": body.raison_sociale, "nom_commercial": body.nom_commercial,
        "siret": body.siret, "tva_intracom": body.tva_intracom, "code_naf": body.code_naf,
        "afl1": body.adresse_facturation_ligne1, "afl2": body.adresse_facturation_ligne2,
        "afcp": body.adresse_facturation_cp, "afville": body.adresse_facturation_ville,
        "afpays": body.adresse_facturation_pays,
        "tel": body.telephone, "email": body.email, "site_web": body.site_web,
        "dpj": body.delai_paiement_jours, "mp": body.mode_paiement, "cpt": body.condition_paiement_texte,
        "escompte": str(body.escompte_pourcent) if body.escompte_pourcent else None,
        "penalite": str(body.penalite_retard_pourcent) if body.penalite_retard_pourcent else None,
        "indemnite": str(body.indemnite_recouvrement) if body.indemnite_recouvrement else None,
        "plafond": str(body.plafond_encours) if body.plafond_encours else None,
        "sla_delai": body.sla_delai_livraison_heures, "sla_taux": str(body.sla_taux_service_pourcent) if body.sla_taux_service_pourcent else None,
        "sla_pen": body.sla_penalite_texte,
        "agency_ids": json.dumps(body.agency_ids) if body.agency_ids else None,
        "notes": body.notes, "statut": body.statut, "ddr": body.date_debut_relation,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
        "uid2": user.get("user_id") if isinstance(user, dict) else None,
    })
    await db.commit()

    row = (await db.execute(
        text("SELECT * FROM customers WHERE id = :id"), {"id": str(cid)}
    )).first()
    return _client_from_row(row)


@router.put("/clients/{cid}", response_model=ClientOut)
@router.put("/customers/{cid}", response_model=ClientOut, include_in_schema=False)
async def update_client(
    cid: str,
    body: ClientUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        text("SELECT id FROM customers WHERE id = :id AND tenant_id = :tid"),
        {"id": cid, "tid": str(tenant.tenant_id)},
    )).first()
    if not existing:
        raise HTTPException(404, "Client not found")

    # LME validation: max 60 days net, max 45 days fin de mois
    if body.delai_paiement_jours and body.delai_paiement_jours > 60:
        raise HTTPException(422, "Delai de paiement LME: maximum 60 jours nets date de facture")
    if body.mode_paiement and "FIN_DE_MOIS" in (body.mode_paiement or "").upper():
        if body.delai_paiement_jours and body.delai_paiement_jours > 45:
            raise HTTPException(422, "Delai de paiement LME: maximum 45 jours fin de mois")

    siren = body.siret[:9] if body.siret and len(body.siret) >= 9 else None

    await db.execute(text("""
        UPDATE customers SET
            name = :name, siren = :siren,
            raison_sociale = :raison_sociale, nom_commercial = :nom_commercial,
            siret = :siret_val, tva_intracom = :tva_intracom, code_naf = :code_naf,
            adresse_facturation_ligne1 = :afl1, adresse_facturation_ligne2 = :afl2,
            adresse_facturation_cp = :afcp, adresse_facturation_ville = :afville,
            adresse_facturation_pays = :afpays,
            telephone = :tel, email = :email, site_web = :site_web,
            delai_paiement_jours = :dpj, mode_paiement = :mp, condition_paiement_texte = :cpt,
            escompte_pourcent = :escompte, penalite_retard_pourcent = :penalite,
            indemnite_recouvrement = :indemnite, plafond_encours = :plafond,
            sla_delai_livraison_heures = :sla_delai, sla_taux_service_pourcent = :sla_taux,
            sla_penalite_texte = :sla_pen,
            agency_ids = CAST(:agency_ids AS jsonb), notes = :notes,
            statut = :statut, date_debut_relation = :ddr,
            payment_terms_days = :pt, address = :addr,
            updated_at = now(), updated_by = :uid
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": cid, "tid": str(tenant.tenant_id),
        "name": body.raison_sociale, "siren": siren,
        "raison_sociale": body.raison_sociale, "nom_commercial": body.nom_commercial,
        "siret_val": body.siret, "tva_intracom": body.tva_intracom, "code_naf": body.code_naf,
        "afl1": body.adresse_facturation_ligne1, "afl2": body.adresse_facturation_ligne2,
        "afcp": body.adresse_facturation_cp, "afville": body.adresse_facturation_ville,
        "afpays": body.adresse_facturation_pays,
        "tel": body.telephone, "email": body.email, "site_web": body.site_web,
        "dpj": body.delai_paiement_jours, "mp": body.mode_paiement, "cpt": body.condition_paiement_texte,
        "escompte": str(body.escompte_pourcent) if body.escompte_pourcent else None,
        "penalite": str(body.penalite_retard_pourcent) if body.penalite_retard_pourcent else None,
        "indemnite": str(body.indemnite_recouvrement) if body.indemnite_recouvrement else None,
        "plafond": str(body.plafond_encours) if body.plafond_encours else None,
        "sla_delai": body.sla_delai_livraison_heures,
        "sla_taux": str(body.sla_taux_service_pourcent) if body.sla_taux_service_pourcent else None,
        "sla_pen": body.sla_penalite_texte,
        "agency_ids": json.dumps(body.agency_ids) if body.agency_ids else None,
        "notes": body.notes, "statut": body.statut, "ddr": body.date_debut_relation,
        "pt": body.delai_paiement_jours, "addr": body.adresse_facturation_ligne1,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
    })
    await db.commit()

    row = (await db.execute(
        text("SELECT * FROM customers WHERE id = :id"), {"id": cid}
    )).first()
    return _client_from_row(row)


@router.patch("/clients/{cid}/status", response_model=ClientOut)
async def change_client_status(
    cid: str,
    body: StatusChange,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.masterdata.schemas import CLIENT_STATUTS
    if body.statut not in CLIENT_STATUTS:
        raise HTTPException(422, f"Statut invalide: {body.statut}")

    is_active = body.statut == "ACTIF"
    result = await db.execute(text("""
        UPDATE customers SET statut = :statut, is_active = :active, updated_at = now(), updated_by = :uid
        WHERE id = :id AND tenant_id = :tid RETURNING id
    """), {
        "id": cid, "tid": str(tenant.tenant_id), "statut": body.statut, "active": is_active,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
    })
    if not result.first():
        raise HTTPException(404, "Client not found")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM customers WHERE id = :id"), {"id": cid})).first()
    return _client_from_row(row)


# ── Client contacts ───────────────────────────────────────────────

@router.post("/clients/{cid}/contacts", response_model=ClientContactOut, status_code=201)
async def add_client_contact(
    cid: str,
    body: ClientContactCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify client exists
    client = (await db.execute(
        text("SELECT id FROM customers WHERE id = :id AND tenant_id = :tid"),
        {"id": cid, "tid": str(tenant.tenant_id)},
    )).first()
    if not client:
        raise HTTPException(404, "Client not found")

    contact_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO client_contacts (
            id, tenant_id, client_id, civilite, nom, prenom, fonction,
            email, telephone_fixe, telephone_mobile,
            is_contact_principal, is_contact_facturation, is_contact_exploitation,
            notes, is_active
        ) VALUES (
            :id, :tid, :cid, :civ, :nom, :prenom, :fonction,
            :email, :tf, :tm,
            :icp, :icf, :ice,
            :notes, :active
        )
    """), {
        "id": str(contact_id), "tid": str(tenant.tenant_id), "cid": cid,
        "civ": body.civilite, "nom": body.nom, "prenom": body.prenom, "fonction": body.fonction,
        "email": body.email, "tf": body.telephone_fixe, "tm": body.telephone_mobile,
        "icp": body.is_contact_principal, "icf": body.is_contact_facturation,
        "ice": body.is_contact_exploitation, "notes": body.notes, "active": body.is_active,
    })
    await db.commit()
    return ClientContactOut(
        id=str(contact_id), client_id=cid, **body.model_dump(),
    )


@router.put("/clients/{cid}/contacts/{contact_id}", response_model=ClientContactOut)
async def update_client_contact(
    cid: str,
    contact_id: str,
    body: ClientContactCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE client_contacts SET
            civilite = :civ, nom = :nom, prenom = :prenom, fonction = :fonction,
            email = :email, telephone_fixe = :tf, telephone_mobile = :tm,
            is_contact_principal = :icp, is_contact_facturation = :icf,
            is_contact_exploitation = :ice, notes = :notes, is_active = :active,
            updated_at = now()
        WHERE id = :id AND client_id = :cid AND tenant_id = :tid RETURNING id
    """), {
        "id": contact_id, "cid": cid, "tid": str(tenant.tenant_id),
        "civ": body.civilite, "nom": body.nom, "prenom": body.prenom, "fonction": body.fonction,
        "email": body.email, "tf": body.telephone_fixe, "tm": body.telephone_mobile,
        "icp": body.is_contact_principal, "icf": body.is_contact_facturation,
        "ice": body.is_contact_exploitation, "notes": body.notes, "active": body.is_active,
    })
    if not result.first():
        raise HTTPException(404, "Contact not found")
    await db.commit()
    return ClientContactOut(id=contact_id, client_id=cid, **body.model_dump())


# ── Client addresses ──────────────────────────────────────────────

@router.post("/clients/{cid}/addresses", response_model=ClientAddressOut, status_code=201)
async def add_client_address(
    cid: str,
    body: ClientAddressCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client = (await db.execute(
        text("SELECT id FROM customers WHERE id = :id AND tenant_id = :tid"),
        {"id": cid, "tid": str(tenant.tenant_id)},
    )).first()
    if not client:
        raise HTTPException(404, "Client not found")

    aid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO client_addresses (
            id, tenant_id, client_id, libelle, type, adresse_ligne1, adresse_ligne2,
            code_postal, ville, pays, latitude, longitude,
            contact_site_nom, contact_site_telephone, horaires_ouverture,
            instructions_acces, contraintes, is_active
        ) VALUES (
            :id, :tid, :cid, :lib, :type, :al1, :al2,
            :cp, :ville, :pays, :lat, :lon,
            :csn, :cst, :ho,
            :ia, CAST(:contraintes AS jsonb), :active
        )
    """), {
        "id": str(aid), "tid": str(tenant.tenant_id), "cid": cid,
        "lib": body.libelle, "type": body.type,
        "al1": body.adresse_ligne1, "al2": body.adresse_ligne2,
        "cp": body.code_postal, "ville": body.ville, "pays": body.pays,
        "lat": str(body.latitude) if body.latitude else None,
        "lon": str(body.longitude) if body.longitude else None,
        "csn": body.contact_site_nom, "cst": body.contact_site_telephone,
        "ho": body.horaires_ouverture, "ia": body.instructions_acces,
        "contraintes": json.dumps(body.contraintes) if body.contraintes else None,
        "active": body.is_active,
    })
    await db.commit()
    return ClientAddressOut(id=str(aid), client_id=cid, **body.model_dump())


@router.put("/clients/{cid}/addresses/{aid}", response_model=ClientAddressOut)
async def update_client_address(
    cid: str,
    aid: str,
    body: ClientAddressCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE client_addresses SET
            libelle = :lib, type = :type, adresse_ligne1 = :al1, adresse_ligne2 = :al2,
            code_postal = :cp, ville = :ville, pays = :pays,
            latitude = :lat, longitude = :lon,
            contact_site_nom = :csn, contact_site_telephone = :cst,
            horaires_ouverture = :ho, instructions_acces = :ia,
            contraintes = CAST(:contraintes AS jsonb), is_active = :active,
            updated_at = now()
        WHERE id = :id AND client_id = :cid AND tenant_id = :tid RETURNING id
    """), {
        "id": aid, "cid": cid, "tid": str(tenant.tenant_id),
        "lib": body.libelle, "type": body.type,
        "al1": body.adresse_ligne1, "al2": body.adresse_ligne2,
        "cp": body.code_postal, "ville": body.ville, "pays": body.pays,
        "lat": str(body.latitude) if body.latitude else None,
        "lon": str(body.longitude) if body.longitude else None,
        "csn": body.contact_site_nom, "cst": body.contact_site_telephone,
        "ho": body.horaires_ouverture, "ia": body.instructions_acces,
        "contraintes": json.dumps(body.contraintes) if body.contraintes else None,
        "active": body.is_active,
    })
    if not result.first():
        raise HTTPException(404, "Address not found")
    await db.commit()
    return ClientAddressOut(id=aid, client_id=cid, **body.model_dump())


# ══════════════════════════════════════════════════════════════════
# SUBCONTRACTORS
# ══════════════════════════════════════════════════════════════════

def _sub_from_row(r) -> SubcontractorOut:
    return SubcontractorOut(
        id=str(r.id), code=r.code, raison_sociale=r.raison_sociale,
        siret=r.siret, siren=r.siren, tva_intracom=r.tva_intracom,
        licence_transport=r.licence_transport,
        adresse_ligne1=r.adresse_ligne1, code_postal=r.code_postal,
        ville=r.ville, pays=r.pays, telephone=r.telephone, email=r.email,
        contact_principal_nom=r.contact_principal_nom,
        zones_geographiques=r.zones_geographiques,
        types_vehicules_disponibles=r.types_vehicules_disponibles,
        specialites=r.specialites,
        delai_paiement_jours=r.delai_paiement_jours, mode_paiement=r.mode_paiement,
        statut=r.statut, conformite_statut=r.conformite_statut,
        note_qualite=r.note_qualite, agency_ids=r.agency_ids,
        notes=r.notes,
        created_at=r.created_at, updated_at=r.updated_at,
    )


@router.get("/subcontractors", response_model=list[SubcontractorOut])
async def list_subcontractors(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    search: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    q = "SELECT * FROM subcontractors WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    if search:
        q += " AND (raison_sociale ILIKE :search OR code ILIKE :search OR siret ILIKE :search)"
        params["search"] = f"%{search}%"
    q += " ORDER BY raison_sociale LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_sub_from_row(r) for r in rows.fetchall()]


@router.get("/subcontractors/{sid}", response_model=SubcontractorDetail)
async def get_subcontractor(
    sid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT * FROM subcontractors WHERE id = :id AND tenant_id = :tid"),
        {"id": sid, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "Subcontractor not found")
    # Get contracts
    contract_rows = (await db.execute(
        text("SELECT * FROM subcontractor_contracts WHERE subcontractor_id = :sid AND tenant_id = :tid ORDER BY date_debut DESC"),
        {"sid": sid, "tid": str(tenant.tenant_id)},
    )).fetchall()
    contracts = [
        SubcontractorContractOut(
            id=str(c.id), subcontractor_id=str(c.subcontractor_id),
            reference=c.reference, type_prestation=c.type_prestation,
            date_debut=c.date_debut, date_fin=c.date_fin,
            tacite_reconduction=c.tacite_reconduction,
            preavis_resiliation_jours=c.preavis_resiliation_jours,
            document_s3_key=c.document_s3_key, tarification=c.tarification,
            statut=c.statut, notes=c.notes,
            created_at=c.created_at, updated_at=c.updated_at,
        ) for c in contract_rows
    ]
    out = _sub_from_row(row)
    return SubcontractorDetail(
        **out.model_dump(),
        adresse_ligne2=row.adresse_ligne2,
        contact_principal_telephone=row.contact_principal_telephone,
        contact_principal_email=row.contact_principal_email,
        rib_iban=row.rib_iban, rib_bic=row.rib_bic,
        contracts=contracts,
    )


@router.post("/subcontractors", response_model=SubcontractorOut, status_code=201)
async def create_subcontractor(
    body: SubcontractorCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sid = uuid.uuid4()
    siren = body.siret[:9] if body.siret and len(body.siret) >= 9 else body.siren

    # Check code uniqueness
    existing = (await db.execute(
        text("SELECT id FROM subcontractors WHERE tenant_id = :tid AND code = :code"),
        {"tid": str(tenant.tenant_id), "code": body.code},
    )).first()
    if existing:
        raise HTTPException(409, "Ce code sous-traitant existe deja.")

    await db.execute(text("""
        INSERT INTO subcontractors (
            id, tenant_id, code, raison_sociale, siret, siren, tva_intracom, licence_transport,
            adresse_ligne1, adresse_ligne2, code_postal, ville, pays,
            telephone, email,
            contact_principal_nom, contact_principal_telephone, contact_principal_email,
            zones_geographiques, types_vehicules_disponibles, specialites,
            delai_paiement_jours, mode_paiement, rib_iban, rib_bic,
            statut, conformite_statut, note_qualite, agency_ids, notes,
            created_by, updated_by
        ) VALUES (
            :id, :tid, :code, :rs, :siret, :siren, :tva, :licence,
            :al1, :al2, :cp, :ville, :pays,
            :tel, :email,
            :cpn, :cpt, :cpe,
            CAST(:zones AS jsonb), CAST(:types_veh AS jsonb), CAST(:spec AS jsonb),
            :dpj, :mp, :iban, :bic,
            :statut, :conf, :note_q, CAST(:agency_ids AS jsonb), :notes,
            :uid, :uid2
        )
    """), {
        "id": str(sid), "tid": str(tenant.tenant_id),
        "code": body.code, "rs": body.raison_sociale,
        "siret": body.siret, "siren": siren, "tva": body.tva_intracom,
        "licence": body.licence_transport,
        "al1": body.adresse_ligne1, "al2": body.adresse_ligne2,
        "cp": body.code_postal, "ville": body.ville, "pays": body.pays,
        "tel": body.telephone, "email": body.email,
        "cpn": body.contact_principal_nom, "cpt": body.contact_principal_telephone,
        "cpe": body.contact_principal_email,
        "zones": json.dumps(body.zones_geographiques) if body.zones_geographiques else None,
        "types_veh": json.dumps(body.types_vehicules_disponibles) if body.types_vehicules_disponibles else None,
        "spec": json.dumps(body.specialites) if body.specialites else None,
        "dpj": body.delai_paiement_jours, "mp": body.mode_paiement,
        "iban": body.rib_iban, "bic": body.rib_bic,
        "statut": body.statut, "conf": body.conformite_statut,
        "note_q": str(body.note_qualite) if body.note_qualite else None,
        "agency_ids": json.dumps(body.agency_ids) if body.agency_ids else None,
        "notes": body.notes,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
        "uid2": user.get("user_id") if isinstance(user, dict) else None,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM subcontractors WHERE id = :id"), {"id": str(sid)})).first()
    return _sub_from_row(row)


@router.put("/subcontractors/{sid}", response_model=SubcontractorOut)
async def update_subcontractor(
    sid: str,
    body: SubcontractorUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        text("SELECT id FROM subcontractors WHERE id = :id AND tenant_id = :tid"),
        {"id": sid, "tid": str(tenant.tenant_id)},
    )).first()
    if not existing:
        raise HTTPException(404, "Subcontractor not found")

    siren = body.siret[:9] if body.siret and len(body.siret) >= 9 else body.siren

    await db.execute(text("""
        UPDATE subcontractors SET
            raison_sociale = :rs, siret = :siret, siren = :siren, tva_intracom = :tva,
            licence_transport = :licence,
            adresse_ligne1 = :al1, adresse_ligne2 = :al2, code_postal = :cp, ville = :ville, pays = :pays,
            telephone = :tel, email = :email,
            contact_principal_nom = :cpn, contact_principal_telephone = :cpt, contact_principal_email = :cpe,
            zones_geographiques = CAST(:zones AS jsonb),
            types_vehicules_disponibles = CAST(:types_veh AS jsonb),
            specialites = CAST(:spec AS jsonb),
            delai_paiement_jours = :dpj, mode_paiement = :mp, rib_iban = :iban, rib_bic = :bic,
            statut = :statut, conformite_statut = :conf, note_qualite = :note_q,
            agency_ids = CAST(:agency_ids AS jsonb), notes = :notes,
            updated_at = now(), updated_by = :uid
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": sid, "tid": str(tenant.tenant_id),
        "rs": body.raison_sociale, "siret": body.siret, "siren": siren, "tva": body.tva_intracom,
        "licence": body.licence_transport,
        "al1": body.adresse_ligne1, "al2": body.adresse_ligne2,
        "cp": body.code_postal, "ville": body.ville, "pays": body.pays,
        "tel": body.telephone, "email": body.email,
        "cpn": body.contact_principal_nom, "cpt": body.contact_principal_telephone,
        "cpe": body.contact_principal_email,
        "zones": json.dumps(body.zones_geographiques) if body.zones_geographiques else None,
        "types_veh": json.dumps(body.types_vehicules_disponibles) if body.types_vehicules_disponibles else None,
        "spec": json.dumps(body.specialites) if body.specialites else None,
        "dpj": body.delai_paiement_jours, "mp": body.mode_paiement,
        "iban": body.rib_iban, "bic": body.rib_bic,
        "statut": body.statut, "conf": body.conformite_statut,
        "note_q": str(body.note_qualite) if body.note_qualite else None,
        "agency_ids": json.dumps(body.agency_ids) if body.agency_ids else None,
        "notes": body.notes,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM subcontractors WHERE id = :id"), {"id": sid})).first()
    return _sub_from_row(row)


@router.patch("/subcontractors/{sid}/status", response_model=SubcontractorOut)
async def change_subcontractor_status(
    sid: str,
    body: StatusChange,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.masterdata.schemas import SUB_STATUTS
    if body.statut not in SUB_STATUTS:
        raise HTTPException(422, f"Statut invalide: {body.statut}")

    result = await db.execute(text("""
        UPDATE subcontractors SET statut = :statut, updated_at = now(), updated_by = :uid
        WHERE id = :id AND tenant_id = :tid RETURNING id
    """), {
        "id": sid, "tid": str(tenant.tenant_id), "statut": body.statut,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
    })
    if not result.first():
        raise HTTPException(404, "Subcontractor not found")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM subcontractors WHERE id = :id"), {"id": sid})).first()
    return _sub_from_row(row)


# ── Subcontractor contracts ───────────────────────────────────────

@router.post("/subcontractors/{sid}/contracts", response_model=SubcontractorContractOut, status_code=201)
async def add_subcontractor_contract(
    sid: str,
    body: SubcontractorContractCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = (await db.execute(
        text("SELECT id FROM subcontractors WHERE id = :id AND tenant_id = :tid"),
        {"id": sid, "tid": str(tenant.tenant_id)},
    )).first()
    if not sub:
        raise HTTPException(404, "Subcontractor not found")

    cid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO subcontractor_contracts (
            id, tenant_id, subcontractor_id, reference, type_prestation,
            date_debut, date_fin, tacite_reconduction, preavis_resiliation_jours,
            document_s3_key, tarification, statut, notes
        ) VALUES (
            :id, :tid, :sid, :ref, :tp,
            :dd, :df, :tr, :prj,
            :doc, CAST(:tarif AS jsonb), :statut, :notes
        )
    """), {
        "id": str(cid), "tid": str(tenant.tenant_id), "sid": sid,
        "ref": body.reference, "tp": body.type_prestation,
        "dd": body.date_debut, "df": body.date_fin,
        "tr": body.tacite_reconduction, "prj": body.preavis_resiliation_jours,
        "doc": body.document_s3_key,
        "tarif": json.dumps(body.tarification) if body.tarification else None,
        "statut": body.statut, "notes": body.notes,
    })
    await db.commit()
    return SubcontractorContractOut(id=str(cid), subcontractor_id=sid, **body.model_dump())


@router.put("/subcontractors/{sid}/contracts/{cid}", response_model=SubcontractorContractOut)
async def update_subcontractor_contract(
    sid: str,
    cid: str,
    body: SubcontractorContractCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        UPDATE subcontractor_contracts SET
            reference = :ref, type_prestation = :tp,
            date_debut = :dd, date_fin = :df,
            tacite_reconduction = :tr, preavis_resiliation_jours = :prj,
            document_s3_key = :doc, tarification = CAST(:tarif AS jsonb),
            statut = :statut, notes = :notes, updated_at = now()
        WHERE id = :id AND subcontractor_id = :sid AND tenant_id = :tid RETURNING id
    """), {
        "id": cid, "sid": sid, "tid": str(tenant.tenant_id),
        "ref": body.reference, "tp": body.type_prestation,
        "dd": body.date_debut, "df": body.date_fin,
        "tr": body.tacite_reconduction, "prj": body.preavis_resiliation_jours,
        "doc": body.document_s3_key,
        "tarif": json.dumps(body.tarification) if body.tarification else None,
        "statut": body.statut, "notes": body.notes,
    })
    if not result.first():
        raise HTTPException(404, "Contract not found")
    await db.commit()
    return SubcontractorContractOut(id=cid, subcontractor_id=sid, **body.model_dump())


# ══════════════════════════════════════════════════════════════════
# DRIVERS
# ══════════════════════════════════════════════════════════════════

def _driver_from_row(r) -> DriverOut:
    return DriverOut(
        id=str(r.id),
        matricule=r.matricule,
        civilite=getattr(r, "civilite", None),
        nom=getattr(r, "nom", None) or r.last_name,
        prenom=getattr(r, "prenom", None) or r.first_name,
        date_naissance=getattr(r, "date_naissance", None),
        telephone_mobile=getattr(r, "telephone_mobile", None) or r.phone,
        email=r.email,
        statut_emploi=getattr(r, "statut_emploi", None),
        type_contrat=getattr(r, "type_contrat", None),
        date_entree=getattr(r, "date_entree", None) or r.hire_date,
        date_sortie=getattr(r, "date_sortie", None),
        poste=getattr(r, "poste", None),
        categorie_permis=getattr(r, "categorie_permis", None),
        qualification_fimo=getattr(r, "qualification_fimo", None),
        qualification_fco=getattr(r, "qualification_fco", None),
        qualification_adr=getattr(r, "qualification_adr", None),
        conformite_statut=getattr(r, "conformite_statut", None),
        statut=getattr(r, "statut", None) or ("ACTIF" if r.is_active else "INACTIF"),
        agency_id=str(r.agency_id) if r.agency_id else None,
        notes=getattr(r, "notes", None),
        created_at=getattr(r, "created_at", None),
        updated_at=getattr(r, "updated_at", None),
        # Legacy
        first_name=r.first_name,
        last_name=r.last_name,
        phone=r.phone,
        is_active=r.is_active,
    )


@router.get("/drivers", response_model=list[DriverOut])
async def list_drivers(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    search: str | None = Query(None),
    agency_id: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    q = "SELECT * FROM drivers WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    if search:
        q += " AND (nom ILIKE :search OR prenom ILIKE :search OR last_name ILIKE :search OR first_name ILIKE :search OR matricule ILIKE :search)"
        params["search"] = f"%{search}%"
    if agency_id:
        q += " AND agency_id = :agency_id"
        params["agency_id"] = agency_id
    q += " ORDER BY COALESCE(nom, last_name), COALESCE(prenom, first_name) LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_driver_from_row(r) for r in rows.fetchall()]


@router.get("/drivers/{did}", response_model=DriverDetail)
async def get_driver(
    did: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT * FROM drivers WHERE id = :id AND tenant_id = :tid"),
        {"id": did, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "Driver not found")
    out = _driver_from_row(row)
    return DriverDetail(
        **out.model_dump(),
        lieu_naissance=getattr(row, "lieu_naissance", None),
        nationalite=getattr(row, "nationalite", None),
        nir=getattr(row, "nir", None),
        adresse_ligne1=getattr(row, "adresse_ligne1", None),
        adresse_ligne2=getattr(row, "adresse_ligne2", None),
        code_postal=getattr(row, "code_postal", None),
        ville=getattr(row, "ville", None),
        pays=getattr(row, "pays", None),
        agence_interim_nom=getattr(row, "agence_interim_nom", None),
        agence_interim_contact=getattr(row, "agence_interim_contact", None),
        motif_sortie=getattr(row, "motif_sortie", None),
        coefficient=getattr(row, "coefficient", None),
        groupe=getattr(row, "groupe", None),
        salaire_base_mensuel=getattr(row, "salaire_base_mensuel", None),
        taux_horaire=getattr(row, "taux_horaire", None),
        qualification_adr_classes=getattr(row, "qualification_adr_classes", None),
        carte_conducteur_numero=getattr(row, "carte_conducteur_numero", None),
        photo_s3_key=getattr(row, "photo_s3_key", None),
    )


@router.post("/drivers", response_model=DriverOut, status_code=201)
async def create_driver(
    body: DriverCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    did = uuid.uuid4()
    agency_id = body.agency_id or (str(tenant.agency_id) if tenant.agency_id else None)

    # Check matricule uniqueness
    existing = (await db.execute(
        text("SELECT id FROM drivers WHERE tenant_id = :tid AND matricule = :mat"),
        {"tid": str(tenant.tenant_id), "mat": body.matricule},
    )).first()
    if existing:
        raise HTTPException(409, "Ce matricule existe deja.")

    # Check NIR uniqueness (RG-B: two drivers can't share same NIR)
    if body.nir:
        if not validate_nir(body.nir):
            raise HTTPException(422, "NIR (numero de securite sociale) invalide")
        existing_nir = (await db.execute(
            text("SELECT id FROM drivers WHERE tenant_id = :tid AND nir = :nir"),
            {"tid": str(tenant.tenant_id), "nir": body.nir},
        )).first()
        if existing_nir:
            raise HTTPException(409, "Ce NIR est deja utilise par un autre conducteur.")

    await db.execute(text("""
        INSERT INTO drivers (
            id, tenant_id, agency_id, matricule, first_name, last_name,
            license_number, license_categories, phone, email, hire_date,
            civilite, nom, prenom, date_naissance, lieu_naissance, nationalite, nir,
            adresse_ligne1, adresse_ligne2, code_postal, ville, pays, telephone_mobile,
            statut_emploi, agence_interim_nom, agence_interim_contact,
            type_contrat, date_entree, date_sortie, motif_sortie, poste,
            categorie_permis, coefficient, groupe, salaire_base_mensuel, taux_horaire,
            qualification_fimo, qualification_fco, qualification_adr, qualification_adr_classes,
            carte_conducteur_numero, statut, notes, created_by, updated_by
        ) VALUES (
            :id, :tid, :aid, :mat, :fn, :ln,
            :lic, :cats, :ph, :em, :hd,
            :civ, :nom, :prenom, :dob, :lieuN, :nat, :nir,
            :al1, :al2, :cp, :ville, :pays, :tm,
            :se, :ain, :aic,
            :tc, :de, :ds, :ms, :poste,
            CAST(:cpermis AS jsonb), :coeff, :groupe, :sbm, :th,
            :fimo, :fco, :adr, CAST(:adr_classes AS jsonb),
            :ccn, :statut, :notes, :uid, :uid2
        )
    """), {
        "id": str(did), "tid": str(tenant.tenant_id), "aid": agency_id,
        "mat": body.matricule,
        "fn": body.first_name or body.prenom, "ln": body.last_name or body.nom,
        "lic": body.license_number, "cats": body.license_categories,
        "ph": body.phone or body.telephone_mobile, "em": body.email,
        "hd": body.hire_date or body.date_entree,
        "civ": body.civilite, "nom": body.nom, "prenom": body.prenom,
        "dob": body.date_naissance, "lieuN": body.lieu_naissance, "nat": body.nationalite,
        "nir": body.nir,
        "al1": body.adresse_ligne1, "al2": body.adresse_ligne2,
        "cp": body.code_postal, "ville": body.ville, "pays": body.pays,
        "tm": body.telephone_mobile,
        "se": body.statut_emploi, "ain": body.agence_interim_nom, "aic": body.agence_interim_contact,
        "tc": body.type_contrat, "de": body.date_entree, "ds": body.date_sortie,
        "ms": body.motif_sortie, "poste": body.poste,
        "cpermis": json.dumps(body.categorie_permis) if body.categorie_permis else None,
        "coeff": body.coefficient, "groupe": body.groupe,
        "sbm": str(body.salaire_base_mensuel) if body.salaire_base_mensuel else None,
        "th": str(body.taux_horaire) if body.taux_horaire else None,
        "fimo": body.qualification_fimo, "fco": body.qualification_fco,
        "adr": body.qualification_adr,
        "adr_classes": json.dumps(body.qualification_adr_classes) if body.qualification_adr_classes else None,
        "ccn": body.carte_conducteur_numero,
        "statut": "ACTIF", "notes": body.notes,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
        "uid2": user.get("user_id") if isinstance(user, dict) else None,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM drivers WHERE id = :id"), {"id": str(did)})).first()
    return _driver_from_row(row)


@router.put("/drivers/{did}", response_model=DriverOut)
async def update_driver(
    did: str,
    body: DriverUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        text("SELECT id FROM drivers WHERE id = :id AND tenant_id = :tid"),
        {"id": did, "tid": str(tenant.tenant_id)},
    )).first()
    if not existing:
        raise HTTPException(404, "Driver not found")

    # Validate NIR if provided
    if body.nir and not validate_nir(body.nir):
        raise HTTPException(422, "NIR (numero de securite sociale) invalide")

    await db.execute(text("""
        UPDATE drivers SET
            first_name = :fn, last_name = :ln, phone = :ph, email = :em,
            license_number = :lic, license_categories = :cats, hire_date = :hd,
            civilite = :civ, nom = :nom, prenom = :prenom,
            date_naissance = :dob, lieu_naissance = :lieuN, nationalite = :nat, nir = :nir,
            adresse_ligne1 = :al1, adresse_ligne2 = :al2, code_postal = :cp, ville = :ville, pays = :pays,
            telephone_mobile = :tm,
            statut_emploi = :se, agence_interim_nom = :ain, agence_interim_contact = :aic,
            type_contrat = :tc, date_entree = :de, date_sortie = :ds, motif_sortie = :ms, poste = :poste,
            categorie_permis = CAST(:cpermis AS jsonb), coefficient = :coeff, groupe = :groupe,
            salaire_base_mensuel = :sbm, taux_horaire = :th,
            qualification_fimo = :fimo, qualification_fco = :fco, qualification_adr = :adr,
            qualification_adr_classes = CAST(:adr_classes AS jsonb),
            carte_conducteur_numero = :ccn, notes = :notes,
            updated_at = now(), updated_by = :uid
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": did, "tid": str(tenant.tenant_id),
        "fn": body.first_name or body.prenom, "ln": body.last_name or body.nom,
        "ph": body.phone or body.telephone_mobile, "em": body.email,
        "lic": body.license_number, "cats": body.license_categories,
        "hd": body.hire_date or body.date_entree,
        "civ": body.civilite, "nom": body.nom, "prenom": body.prenom,
        "dob": body.date_naissance, "lieuN": body.lieu_naissance, "nat": body.nationalite,
        "nir": body.nir,
        "al1": body.adresse_ligne1, "al2": body.adresse_ligne2,
        "cp": body.code_postal, "ville": body.ville, "pays": body.pays,
        "tm": body.telephone_mobile,
        "se": body.statut_emploi, "ain": body.agence_interim_nom, "aic": body.agence_interim_contact,
        "tc": body.type_contrat, "de": body.date_entree, "ds": body.date_sortie,
        "ms": body.motif_sortie, "poste": body.poste,
        "cpermis": json.dumps(body.categorie_permis) if body.categorie_permis else None,
        "coeff": body.coefficient, "groupe": body.groupe,
        "sbm": str(body.salaire_base_mensuel) if body.salaire_base_mensuel else None,
        "th": str(body.taux_horaire) if body.taux_horaire else None,
        "fimo": body.qualification_fimo, "fco": body.qualification_fco,
        "adr": body.qualification_adr,
        "adr_classes": json.dumps(body.qualification_adr_classes) if body.qualification_adr_classes else None,
        "ccn": body.carte_conducteur_numero, "notes": body.notes,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM drivers WHERE id = :id"), {"id": did})).first()
    return _driver_from_row(row)


@router.patch("/drivers/{did}/status", response_model=DriverOut)
async def change_driver_status(
    did: str,
    body: StatusChange,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.masterdata.schemas import DRIVER_STATUTS
    if body.statut not in DRIVER_STATUTS:
        raise HTTPException(422, f"Statut invalide: {body.statut}")

    is_active = body.statut == "ACTIF"
    result = await db.execute(text("""
        UPDATE drivers SET statut = :statut, is_active = :active, updated_at = now(), updated_by = :uid
        WHERE id = :id AND tenant_id = :tid RETURNING id
    """), {
        "id": did, "tid": str(tenant.tenant_id), "statut": body.statut, "active": is_active,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
    })
    if not result.first():
        raise HTTPException(404, "Driver not found")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM drivers WHERE id = :id"), {"id": did})).first()
    return _driver_from_row(row)


# ══════════════════════════════════════════════════════════════════
# VEHICLES
# ══════════════════════════════════════════════════════════════════

def _vehicle_from_row(r) -> VehicleOut:
    return VehicleOut(
        id=str(r.id),
        immatriculation=getattr(r, "immatriculation", None) or r.plate_number,
        type_entity=getattr(r, "type_entity", None),
        categorie=getattr(r, "categorie", None),
        marque=getattr(r, "marque", None) or r.brand,
        modele=getattr(r, "modele", None) or r.model,
        annee_mise_en_circulation=getattr(r, "annee_mise_en_circulation", None),
        carrosserie=getattr(r, "carrosserie", None),
        ptac_kg=getattr(r, "ptac_kg", None),
        charge_utile_kg=getattr(r, "charge_utile_kg", None),
        motorisation=getattr(r, "motorisation", None),
        norme_euro=getattr(r, "norme_euro", None),
        proprietaire=getattr(r, "proprietaire", None),
        km_compteur_actuel=getattr(r, "km_compteur_actuel", None),
        conformite_statut=getattr(r, "conformite_statut", None),
        statut=getattr(r, "statut", None) or ("ACTIF" if r.is_active else "INACTIF"),
        agency_id=str(r.agency_id) if r.agency_id else None,
        notes=getattr(r, "notes", None),
        created_at=getattr(r, "created_at", None),
        updated_at=getattr(r, "updated_at", None),
        # Legacy
        plate_number=r.plate_number,
        brand=r.brand,
        model=r.model,
        vehicle_type=r.vehicle_type,
        payload_kg=float(r.payload_kg) if r.payload_kg else None,
        is_active=r.is_active,
    )


@router.get("/vehicles", response_model=list[VehicleOut])
async def list_vehicles(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    statut: str | None = Query(None),
    categorie: str | None = Query(None),
    search: str | None = Query(None),
    agency_id: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    q = "SELECT * FROM vehicles WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    if categorie:
        q += " AND categorie = :categorie"
        params["categorie"] = categorie
    if search:
        q += " AND (immatriculation ILIKE :search OR plate_number ILIKE :search OR marque ILIKE :search OR brand ILIKE :search)"
        params["search"] = f"%{search}%"
    if agency_id:
        q += " AND agency_id = :agency_id"
        params["agency_id"] = agency_id
    q += " ORDER BY COALESCE(immatriculation, plate_number) LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = await db.execute(text(q), params)
    return [_vehicle_from_row(r) for r in rows.fetchall()]


@router.get("/vehicles/{vid}", response_model=VehicleDetail)
async def get_vehicle(
    vid: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(
        text("SELECT * FROM vehicles WHERE id = :id AND tenant_id = :tid"),
        {"id": vid, "tid": str(tenant.tenant_id)},
    )).first()
    if not row:
        raise HTTPException(404, "Vehicle not found")
    out = _vehicle_from_row(row)
    return VehicleDetail(
        **out.model_dump(),
        date_premiere_immatriculation=getattr(row, "date_premiere_immatriculation", None) or row.first_registration,
        vin=row.vin,
        ptra_kg=getattr(row, "ptra_kg", None),
        volume_m3=getattr(row, "volume_m3", None),
        longueur_utile_m=getattr(row, "longueur_utile_m", None),
        largeur_utile_m=getattr(row, "largeur_utile_m", None),
        hauteur_utile_m=getattr(row, "hauteur_utile_m", None),
        nb_palettes_europe=getattr(row, "nb_palettes_europe", None),
        nb_essieux=getattr(row, "nb_essieux", None),
        equipements=getattr(row, "equipements", None),
        temperature_min=getattr(row, "temperature_min", None),
        temperature_max=getattr(row, "temperature_max", None),
        loueur_nom=getattr(row, "loueur_nom", None),
        contrat_location_ref=getattr(row, "contrat_location_ref", None),
        date_fin_contrat_location=getattr(row, "date_fin_contrat_location", None),
        date_dernier_releve_km=getattr(row, "date_dernier_releve_km", None),
    )


@router.post("/vehicles", response_model=VehicleOut, status_code=201)
async def create_vehicle(
    body: VehicleCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vid = uuid.uuid4()
    agency_id = body.agency_id or (str(tenant.agency_id) if tenant.agency_id else None)
    plate = body.immatriculation or body.plate_number

    # RG-B-030: check immatriculation uniqueness
    existing = (await db.execute(
        text("SELECT id FROM vehicles WHERE tenant_id = :tid AND (immatriculation = :plate OR plate_number = :plate)"),
        {"tid": str(tenant.tenant_id), "plate": plate},
    )).first()
    if existing:
        raise HTTPException(409, "Cette immatriculation existe deja.")

    # Validate VIN if provided
    if body.vin and not validate_vin(body.vin):
        raise HTTPException(422, "VIN (numero d'identification du vehicule) invalide")

    await db.execute(text("""
        INSERT INTO vehicles (
            id, tenant_id, agency_id, plate_number, vin, brand, model, vehicle_type,
            payload_kg, first_registration,
            immatriculation, type_entity, categorie, marque, modele,
            annee_mise_en_circulation, date_premiere_immatriculation, carrosserie,
            ptac_kg, ptra_kg, charge_utile_kg, volume_m3,
            longueur_utile_m, largeur_utile_m, hauteur_utile_m,
            nb_palettes_europe, nb_essieux, motorisation, norme_euro,
            equipements, temperature_min, temperature_max,
            proprietaire, loueur_nom, contrat_location_ref, date_fin_contrat_location,
            km_compteur_actuel, date_dernier_releve_km,
            statut, notes, created_by, updated_by
        ) VALUES (
            :id, :tid, :aid, :plate, :vin, :brand, :model_legacy, :vtype,
            :payload, :reg,
            :immat, :te, :cat, :marque, :modele,
            :amc, :dpi, :carros,
            :ptac, :ptra, :cu, :vol,
            :longueur, :largeur, :hauteur,
            :npe, :nbe, :motor, :euro,
            CAST(:equip AS jsonb), :tmin, :tmax,
            :proprio, :loueur, :clref, :dfcl,
            :km, :ddrk,
            :statut, :notes, :uid, :uid2
        )
    """), {
        "id": str(vid), "tid": str(tenant.tenant_id), "aid": agency_id,
        "plate": plate, "vin": body.vin,
        "brand": body.brand or body.marque, "model_legacy": body.model or body.modele,
        "vtype": body.vehicle_type or body.categorie,
        "payload": body.payload_kg or body.charge_utile_kg,
        "reg": body.first_registration or (str(body.date_premiere_immatriculation) if body.date_premiere_immatriculation else None),
        "immat": plate, "te": body.type_entity,
        "cat": body.categorie, "marque": body.marque or body.brand,
        "modele": body.modele or body.model,
        "amc": body.annee_mise_en_circulation,
        "dpi": body.date_premiere_immatriculation,
        "carros": body.carrosserie,
        "ptac": body.ptac_kg, "ptra": body.ptra_kg,
        "cu": body.charge_utile_kg, "vol": str(body.volume_m3) if body.volume_m3 else None,
        "longueur": str(body.longueur_utile_m) if body.longueur_utile_m else None,
        "largeur": str(body.largeur_utile_m) if body.largeur_utile_m else None,
        "hauteur": str(body.hauteur_utile_m) if body.hauteur_utile_m else None,
        "npe": body.nb_palettes_europe, "nbe": body.nb_essieux,
        "motor": body.motorisation, "euro": body.norme_euro,
        "equip": json.dumps(body.equipements) if body.equipements else None,
        "tmin": str(body.temperature_min) if body.temperature_min else None,
        "tmax": str(body.temperature_max) if body.temperature_max else None,
        "proprio": body.proprietaire, "loueur": body.loueur_nom,
        "clref": body.contrat_location_ref,
        "dfcl": body.date_fin_contrat_location,
        "km": body.km_compteur_actuel, "ddrk": body.date_dernier_releve_km,
        "statut": "ACTIF", "notes": body.notes,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
        "uid2": user.get("user_id") if isinstance(user, dict) else None,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vehicles WHERE id = :id"), {"id": str(vid)})).first()
    return _vehicle_from_row(row)


@router.put("/vehicles/{vid}", response_model=VehicleOut)
async def update_vehicle(
    vid: str,
    body: VehicleUpdate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        text("SELECT id FROM vehicles WHERE id = :id AND tenant_id = :tid"),
        {"id": vid, "tid": str(tenant.tenant_id)},
    )).first()
    if not existing:
        raise HTTPException(404, "Vehicle not found")

    # Validate VIN if provided
    if body.vin and not validate_vin(body.vin):
        raise HTTPException(422, "VIN (numero d'identification du vehicule) invalide")

    plate = body.immatriculation or body.plate_number

    await db.execute(text("""
        UPDATE vehicles SET
            plate_number = :plate, vin = :vin, brand = :brand_legacy, model = :model_legacy,
            vehicle_type = :vtype, payload_kg = :payload, first_registration = :reg,
            immatriculation = :immat, type_entity = :te, categorie = :cat,
            marque = :marque, modele = :modele,
            annee_mise_en_circulation = :amc, date_premiere_immatriculation = :dpi,
            carrosserie = :carros,
            ptac_kg = :ptac, ptra_kg = :ptra, charge_utile_kg = :cu, volume_m3 = :vol,
            longueur_utile_m = :longueur, largeur_utile_m = :largeur, hauteur_utile_m = :hauteur,
            nb_palettes_europe = :npe, nb_essieux = :nbe,
            motorisation = :motor, norme_euro = :euro,
            equipements = CAST(:equip AS jsonb),
            temperature_min = :tmin, temperature_max = :tmax,
            proprietaire = :proprio, loueur_nom = :loueur,
            contrat_location_ref = :clref, date_fin_contrat_location = :dfcl,
            km_compteur_actuel = :km, date_dernier_releve_km = :ddrk,
            notes = :notes, updated_at = now(), updated_by = :uid
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": vid, "tid": str(tenant.tenant_id),
        "plate": plate, "vin": body.vin,
        "brand_legacy": body.brand or body.marque, "model_legacy": body.model or body.modele,
        "vtype": body.vehicle_type or body.categorie,
        "payload": body.payload_kg or body.charge_utile_kg,
        "reg": body.first_registration or (str(body.date_premiere_immatriculation) if body.date_premiere_immatriculation else None),
        "immat": plate, "te": body.type_entity,
        "cat": body.categorie, "marque": body.marque or body.brand,
        "modele": body.modele or body.model,
        "amc": body.annee_mise_en_circulation,
        "dpi": body.date_premiere_immatriculation,
        "carros": body.carrosserie,
        "ptac": body.ptac_kg, "ptra": body.ptra_kg,
        "cu": body.charge_utile_kg, "vol": str(body.volume_m3) if body.volume_m3 else None,
        "longueur": str(body.longueur_utile_m) if body.longueur_utile_m else None,
        "largeur": str(body.largeur_utile_m) if body.largeur_utile_m else None,
        "hauteur": str(body.hauteur_utile_m) if body.hauteur_utile_m else None,
        "npe": body.nb_palettes_europe, "nbe": body.nb_essieux,
        "motor": body.motorisation, "euro": body.norme_euro,
        "equip": json.dumps(body.equipements) if body.equipements else None,
        "tmin": str(body.temperature_min) if body.temperature_min else None,
        "tmax": str(body.temperature_max) if body.temperature_max else None,
        "proprio": body.proprietaire, "loueur": body.loueur_nom,
        "clref": body.contrat_location_ref,
        "dfcl": body.date_fin_contrat_location,
        "km": body.km_compteur_actuel, "ddrk": body.date_dernier_releve_km,
        "notes": body.notes,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
    })
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vehicles WHERE id = :id"), {"id": vid})).first()
    return _vehicle_from_row(row)


@router.patch("/vehicles/{vid}/status", response_model=VehicleOut)
async def change_vehicle_status(
    vid: str,
    body: StatusChange,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.masterdata.schemas import VEHICLE_STATUTS
    if body.statut not in VEHICLE_STATUTS:
        raise HTTPException(422, f"Statut invalide: {body.statut}")

    is_active = body.statut == "ACTIF"
    result = await db.execute(text("""
        UPDATE vehicles SET statut = :statut, is_active = :active, updated_at = now(), updated_by = :uid
        WHERE id = :id AND tenant_id = :tid RETURNING id
    """), {
        "id": vid, "tid": str(tenant.tenant_id), "statut": body.statut, "active": is_active,
        "uid": user.get("user_id") if isinstance(user, dict) else None,
    })
    if not result.first():
        raise HTTPException(404, "Vehicle not found")
    await db.commit()
    row = (await db.execute(text("SELECT * FROM vehicles WHERE id = :id"), {"id": vid})).first()
    return _vehicle_from_row(row)


# ══════════════════════════════════════════════════════════════════
# LEGACY ENDPOINTS (backward compat — kept as aliases)
# ══════════════════════════════════════════════════════════════════
# The /customers endpoints are aliased above via include_in_schema=False decorators.
# /suppliers is kept as-is for the supplier_invoices module.

from pydantic import BaseModel as _BM  # noqa: E402


class SupplierIn(_BM):
    name: str
    siren: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class SupplierOut(_BM):
    id: str
    name: str
    siren: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    is_active: bool = True


@router.get("/suppliers", response_model=list[SupplierOut])
async def list_suppliers(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        text("SELECT * FROM suppliers WHERE tenant_id = :tid AND is_active = true ORDER BY name"),
        {"tid": str(tenant.tenant_id)},
    )
    return [SupplierOut(id=str(r.id), name=r.name, siren=r.siren, address=r.address,
                        contact_email=r.contact_email, contact_phone=r.contact_phone,
                        is_active=r.is_active) for r in rows.fetchall()]


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
async def create_supplier(
    body: SupplierIn,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sid = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO suppliers (id, tenant_id, name, siren, address, contact_email, contact_phone)
        VALUES (:id, :tid, :name, :siren, :addr, :ce, :cp)
    """), {"id": str(sid), "tid": str(tenant.tenant_id), "name": body.name, "siren": body.siren,
           "addr": body.address, "ce": body.contact_email, "cp": body.contact_phone})
    await db.commit()
    return SupplierOut(id=str(sid), name=body.name, siren=body.siren, address=body.address,
                       contact_email=body.contact_email, contact_phone=body.contact_phone)
