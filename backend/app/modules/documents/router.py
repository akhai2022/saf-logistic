"""Module D — Gestion documentaire & Conformité: full CRUD + compliance engine."""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.modules.documents.schemas import (
    ComplianceAlertAcknowledge,
    ComplianceAlertOut,
    ComplianceChecklistItem,
    ComplianceChecklistOut,
    ComplianceDashboardEntity,
    ComplianceDashboardOut,
    ComplianceTemplateCreate,
    ComplianceTemplateOut,
    DocumentCreate,
    DocumentOut,
    DocumentValidation,
)

router = APIRouter(tags=["documents"])


# ── Helpers ──────────────────────────────────────────────────────

def _ts(val) -> str | None:
    return str(val) if val else None


def _doc_from_row(r) -> DocumentOut:
    doc_type = getattr(r, "type_document", None) or getattr(r, "doc_type", None) or ""
    statut = getattr(r, "statut", None) or "VALIDE"
    tags = getattr(r, "tags", None)
    return DocumentOut(
        id=str(r.id),
        entity_type=r.entity_type,
        entity_id=str(r.entity_id),
        type_document=doc_type,
        sous_type=getattr(r, "sous_type", None),
        fichier_s3_key=getattr(r, "fichier_s3_key", None) or getattr(r, "s3_key", None),
        fichier_nom_original=getattr(r, "fichier_nom_original", None) or getattr(r, "file_name", None),
        fichier_taille_octets=getattr(r, "fichier_taille_octets", None),
        fichier_mime_type=getattr(r, "fichier_mime_type", None),
        numero_document=getattr(r, "numero_document", None),
        date_emission=_ts(getattr(r, "date_emission", None) or getattr(r, "issue_date", None)),
        date_expiration=_ts(getattr(r, "date_expiration", None) or getattr(r, "expiry_date", None)),
        date_prochaine_echeance=_ts(getattr(r, "date_prochaine_echeance", None)),
        organisme_emetteur=getattr(r, "organisme_emetteur", None),
        tags=list(tags) if tags else None,
        notes=getattr(r, "notes", None),
        version=getattr(r, "version", None),
        remplace_document_id=_ts(getattr(r, "remplace_document_id", None)),
        statut=statut,
        validation_par=_ts(getattr(r, "validation_par", None)),
        validation_date=_ts(getattr(r, "validation_date", None)),
        motif_rejet=getattr(r, "motif_rejet", None),
        is_critical=getattr(r, "is_critical", None),
        uploaded_by=_ts(getattr(r, "uploaded_by", None)),
        uploaded_by_role=getattr(r, "uploaded_by_role", None),
        created_at=_ts(getattr(r, "created_at", None)),
        updated_at=_ts(getattr(r, "updated_at", None)),
        # Legacy compat
        compliance_status=getattr(r, "compliance_status", None) or statut,
        doc_type=doc_type,
        s3_key=getattr(r, "fichier_s3_key", None) or getattr(r, "s3_key", None),
        file_name=getattr(r, "fichier_nom_original", None) or getattr(r, "file_name", None),
        issue_date=_ts(getattr(r, "date_emission", None) or getattr(r, "issue_date", None)),
        expiry_date=_ts(getattr(r, "date_expiration", None) or getattr(r, "expiry_date", None)),
    )


def _template_from_row(r) -> ComplianceTemplateOut:
    cond = getattr(r, "condition_applicabilite", None)
    if isinstance(cond, str):
        try:
            cond = json.loads(cond)
        except (json.JSONDecodeError, TypeError):
            cond = None
    alertes = getattr(r, "alertes_jours", None)
    return ComplianceTemplateOut(
        id=str(r.id),
        entity_type=r.entity_type,
        type_document=r.type_document,
        libelle=r.libelle,
        obligatoire=r.obligatoire,
        bloquant=r.bloquant,
        condition_applicabilite=cond,
        duree_validite_defaut_jours=getattr(r, "duree_validite_defaut_jours", None),
        alertes_jours=list(alertes) if alertes else None,
        ordre_affichage=getattr(r, "ordre_affichage", 0),
        is_active=r.is_active,
        created_at=_ts(getattr(r, "created_at", None)),
        updated_at=_ts(getattr(r, "updated_at", None)),
    )


async def recalculate_compliance(
    db: AsyncSession, tenant_id: str, entity_type: str, entity_id: str
) -> ComplianceChecklistOut:
    """Compute compliance checklist from templates + documents for one entity."""
    today = date.today()

    # Get active templates for this entity type
    templates = (await db.execute(text("""
        SELECT * FROM compliance_templates
        WHERE tenant_id = :tid AND entity_type = :etype AND is_active = true
        ORDER BY ordre_affichage
    """), {"tid": tenant_id, "etype": entity_type})).fetchall()

    items: list[ComplianceChecklistItem] = []
    nb_requis = 0
    nb_valides = 0
    nb_manquants = 0
    nb_expires = 0
    nb_expirant = 0
    has_bloquant = False

    for tpl in templates:
        nb_requis += 1
        # Find latest valid document for this type
        doc = (await db.execute(text("""
            SELECT id, date_expiration, statut
            FROM documents
            WHERE tenant_id = :tid AND entity_type = :etype AND entity_id = :eid
              AND doc_type = :dtype
              AND statut NOT IN ('ARCHIVE', 'REJETE', 'BROUILLON')
            ORDER BY version DESC, created_at DESC LIMIT 1
        """), {
            "tid": tenant_id, "etype": entity_type,
            "eid": entity_id, "dtype": tpl.type_document,
        })).first()

        if not doc:
            nb_manquants += 1
            item_statut = "MANQUANT"
            if tpl.bloquant:
                has_bloquant = True
            items.append(ComplianceChecklistItem(
                type_document=tpl.type_document, libelle=tpl.libelle,
                obligatoire=tpl.obligatoire, bloquant=tpl.bloquant,
                statut=item_statut,
            ))
            continue

        exp = doc.date_expiration
        doc_statut = doc.statut or "VALIDE"
        jours = None

        if doc_statut == "EXPIRE" or (exp and exp < today):
            nb_expires += 1
            item_statut = "EXPIRE"
            if tpl.bloquant:
                has_bloquant = True
            jours = (today - exp).days if exp else None
        elif doc_statut == "EN_ATTENTE_VALIDATION":
            item_statut = "EN_ATTENTE"
            nb_manquants += 1  # Doesn't count as valid yet
        elif exp and (exp - today).days <= 60:
            nb_expirant += 1
            nb_valides += 1
            item_statut = "EXPIRANT"
            jours = (exp - today).days
        else:
            nb_valides += 1
            item_statut = "OK"
            jours = (exp - today).days if exp else None

        items.append(ComplianceChecklistItem(
            type_document=tpl.type_document, libelle=tpl.libelle,
            obligatoire=tpl.obligatoire, bloquant=tpl.bloquant,
            statut=item_statut,
            document_id=str(doc.id),
            date_expiration=str(exp) if exp else None,
            jours_avant_expiration=jours,
        ))

    # Determine global status
    if has_bloquant:
        statut_global = "BLOQUANT"
    elif nb_manquants > 0 or nb_expires > 0 or nb_expirant > 0:
        statut_global = "A_REGULARISER"
    else:
        statut_global = "OK"

    taux = round((nb_valides / nb_requis * 100), 2) if nb_requis > 0 else 100.0

    # Upsert compliance_checklists
    details_json = json.dumps(
        [item.model_dump() for item in items], default=str
    )
    await db.execute(text("""
        INSERT INTO compliance_checklists (
            id, tenant_id, entity_type, entity_id, statut_global,
            nb_documents_requis, nb_documents_valides, nb_documents_manquants,
            nb_documents_expires, nb_documents_expirant_bientot,
            taux_conformite_pourcent, details, derniere_mise_a_jour
        ) VALUES (
            gen_random_uuid(), :tid, :etype, :eid, :sg,
            :req, :val, :man, :exp, :expb,
            :taux, :det, NOW()
        )
        ON CONFLICT (tenant_id, entity_type, entity_id)
        DO UPDATE SET
            statut_global = :sg,
            nb_documents_requis = :req,
            nb_documents_valides = :val,
            nb_documents_manquants = :man,
            nb_documents_expires = :exp,
            nb_documents_expirant_bientot = :expb,
            taux_conformite_pourcent = :taux,
            details = :det,
            derniere_mise_a_jour = NOW(),
            updated_at = NOW()
    """), {
        "tid": tenant_id, "etype": entity_type, "eid": entity_id,
        "sg": statut_global, "req": nb_requis, "val": nb_valides,
        "man": nb_manquants, "exp": nb_expires, "expb": nb_expirant,
        "taux": taux, "det": details_json,
    })

    # Update entity conformite_statut
    entity_table = {
        "DRIVER": "drivers", "VEHICLE": "vehicles",
        "SUBCONTRACTOR": "subcontractors",
    }.get(entity_type)
    if entity_table:
        await db.execute(text(f"""
            UPDATE {entity_table} SET conformite_statut = :sg
            WHERE id = :eid AND tenant_id = :tid
        """), {"sg": statut_global, "eid": entity_id, "tid": tenant_id})

    return ComplianceChecklistOut(
        entity_type=entity_type, entity_id=entity_id,
        statut_global=statut_global,
        nb_documents_requis=nb_requis, nb_documents_valides=nb_valides,
        nb_documents_manquants=nb_manquants, nb_documents_expires=nb_expires,
        nb_documents_expirant_bientot=nb_expirant,
        taux_conformite_pourcent=taux, items=items,
    )


# ── Document CRUD ────────────────────────────────────────────────

@router.get("/v1/documents", response_model=list[DocumentOut])
async def list_documents(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    type_document: str | None = Query(None),
    statut: str | None = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    q = "SELECT * FROM documents WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if entity_type:
        q += " AND entity_type = :etype"
        params["etype"] = entity_type.upper()
    if entity_id:
        q += " AND entity_id = :eid"
        params["eid"] = entity_id
    if type_document:
        q += " AND doc_type = :dtype"
        params["dtype"] = type_document
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    q += " ORDER BY created_at DESC LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = (await db.execute(text(q), params)).fetchall()
    return [_doc_from_row(r) for r in rows]


@router.post("/v1/documents", response_model=DocumentOut, status_code=201)
async def create_document(
    body: DocumentCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    uid = str(user["id"]) if isinstance(user, dict) and "id" in user else None
    doc_id = uuid.uuid4()

    # RG-D-006: auto-archive previous version
    prev = (await db.execute(text("""
        SELECT id, version FROM documents
        WHERE tenant_id = :tid AND entity_type = :etype AND entity_id = :eid
          AND doc_type = :dtype
          AND statut = 'VALIDE'
        ORDER BY version DESC LIMIT 1
    """), {
        "tid": tid, "etype": body.entity_type,
        "eid": body.entity_id, "dtype": body.type_document,
    })).first()

    new_version = 1
    remplace_id = None
    if prev:
        new_version = (prev.version or 1) + 1
        remplace_id = str(prev.id)
        await db.execute(text("""
            UPDATE documents SET statut = 'ARCHIVE'
            WHERE id = :id
        """), {"id": str(prev.id)})

    tags_val = "{" + ",".join(body.tags) + "}" if body.tags else None

    # Convert date strings to date objects for asyncpg compatibility
    demission_val = (
        date.fromisoformat(body.date_emission) if isinstance(body.date_emission, str) and body.date_emission
        else body.date_emission
    )
    dexpiration_val = (
        date.fromisoformat(body.date_expiration) if isinstance(body.date_expiration, str) and body.date_expiration
        else body.date_expiration
    )

    await db.execute(text("""
        INSERT INTO documents (
            id, tenant_id, entity_type, entity_id,
            doc_type, sous_type,
            s3_key, file_name,
            fichier_taille_octets, fichier_mime_type,
            numero_document, date_emission, date_expiration,
            issue_date, expiry_date,
            organisme_emetteur, tags, notes,
            version, remplace_document_id,
            statut, compliance_status,
            is_critical, uploaded_by, uploaded_by_role
        ) VALUES (
            :id, :tid, :etype, :eid,
            :dtype, :stype,
            :s3k, :fname,
            :fsize, :fmime,
            :numdoc, :demission, :dexpiration,
            :demission, :dexpiration,
            :org, :tags, :notes,
            :ver, :repl,
            'VALIDE', 'valid',
            :crit, :uid, :urole
        )
    """), {
        "id": str(doc_id), "tid": tid,
        "etype": body.entity_type, "eid": body.entity_id,
        "dtype": body.type_document, "stype": body.sous_type,
        "s3k": body.fichier_s3_key, "fname": body.fichier_nom_original,
        "fsize": body.fichier_taille_octets, "fmime": body.fichier_mime_type,
        "numdoc": body.numero_document,
        "demission": demission_val, "dexpiration": dexpiration_val,
        "org": body.organisme_emetteur, "tags": tags_val, "notes": body.notes,
        "ver": new_version, "repl": remplace_id,
        "crit": body.is_critical, "uid": uid, "urole": "EXPLOITATION",
    })

    # Recalculate compliance
    await recalculate_compliance(db, tid, body.entity_type, body.entity_id)
    await db.commit()

    row = (await db.execute(
        text("SELECT * FROM documents WHERE id = :id"), {"id": str(doc_id)}
    )).first()
    return _doc_from_row(row)


@router.get("/v1/documents/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text(
        "SELECT * FROM documents WHERE id = :id AND tenant_id = :tid"
    ), {"id": doc_id, "tid": str(tenant.tenant_id)})).first()
    if not row:
        raise HTTPException(404, "Document not found")
    return _doc_from_row(row)


@router.get("/v1/documents/{doc_id}/download")
async def download_document(
    doc_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text(
        "SELECT s3_key FROM documents WHERE id = :id AND tenant_id = :tid"
    ), {"id": doc_id, "tid": str(tenant.tenant_id)})).first()
    if not row:
        raise HTTPException(404, "Document not found")
    s3_key = row.s3_key
    if not s3_key:
        raise HTTPException(404, "No file associated")
    return {"s3_key": s3_key, "download_url": f"/v1/files/presign-download?s3_key={s3_key}"}


@router.patch("/v1/documents/{doc_id}/validate", response_model=DocumentOut)
async def validate_document(
    doc_id: str,
    body: DocumentValidation,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """RG-D-007: validate or reject a document."""
    tid = str(tenant.tenant_id)
    uid = str(user["id"]) if isinstance(user, dict) and "id" in user else None

    row = (await db.execute(text(
        "SELECT * FROM documents WHERE id = :id AND tenant_id = :tid"
    ), {"id": doc_id, "tid": tid})).first()
    if not row:
        raise HTTPException(404, "Document not found")

    await db.execute(text("""
        UPDATE documents SET
            statut = :statut,
            validation_par = :uid,
            validation_date = NOW(),
            motif_rejet = :motif,
            compliance_status = CASE WHEN :statut = 'VALIDE' THEN 'valid' ELSE 'rejected' END
        WHERE id = :id
    """), {
        "id": doc_id, "statut": body.statut,
        "uid": uid, "motif": body.motif_rejet,
    })

    # Recalculate compliance for the entity
    await recalculate_compliance(db, tid, row.entity_type, str(row.entity_id))
    await db.commit()

    updated = (await db.execute(text(
        "SELECT * FROM documents WHERE id = :id"
    ), {"id": doc_id})).first()
    return _doc_from_row(updated)


@router.patch("/v1/documents/{doc_id}/reject", response_model=DocumentOut)
async def reject_document(
    doc_id: str,
    body: DocumentValidation,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    body.statut = "REJETE"
    return await validate_document(doc_id, body, tenant, user, db)


# ── Compliance endpoints ─────────────────────────────────────────

@router.get("/v1/compliance/{entity_type}/{entity_id}",
            response_model=ComplianceChecklistOut)
async def get_compliance_checklist(
    entity_type: str,
    entity_id: str,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    etype = entity_type.upper()
    result = await recalculate_compliance(
        db, str(tenant.tenant_id), etype, entity_id
    )
    await db.commit()
    return result


@router.get("/v1/compliance/dashboard", response_model=ComplianceDashboardOut)
async def compliance_dashboard(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = Query(None),
):
    tid = str(tenant.tenant_id)
    entities: list[ComplianceDashboardEntity] = []

    etypes = [entity_type.upper()] if entity_type else ["DRIVER", "VEHICLE", "SUBCONTRACTOR"]

    for etype in etypes:
        if etype == "DRIVER":
            eq = """SELECT id, COALESCE(nom, last_name, '') || ' ' ||
                    COALESCE(prenom, first_name, '') AS name
                    FROM drivers WHERE tenant_id = :tid
                    AND COALESCE(statut, 'ACTIF') = 'ACTIF'"""
        elif etype == "VEHICLE":
            eq = """SELECT id, COALESCE(immatriculation, plate_number, '') AS name
                    FROM vehicles WHERE tenant_id = :tid
                    AND COALESCE(statut, 'ACTIF') = 'ACTIF'"""
        elif etype == "SUBCONTRACTOR":
            eq = """SELECT id, raison_sociale AS name
                    FROM subcontractors WHERE tenant_id = :tid
                    AND COALESCE(statut, 'ACTIF') = 'ACTIF'"""
        else:
            continue

        rows = (await db.execute(text(eq), {"tid": tid})).fetchall()
        for row in rows:
            eid = str(row.id)
            # Get checklist from cache or compute
            cl = (await db.execute(text("""
                SELECT * FROM compliance_checklists
                WHERE tenant_id = :tid AND entity_type = :etype AND entity_id = :eid
            """), {"tid": tid, "etype": etype, "eid": eid})).first()

            if cl:
                entities.append(ComplianceDashboardEntity(
                    entity_type=etype, entity_id=eid, entity_name=row.name,
                    statut_global=cl.statut_global,
                    taux_conformite_pourcent=float(cl.taux_conformite_pourcent or 0),
                    nb_documents_requis=cl.nb_documents_requis or 0,
                    nb_documents_valides=cl.nb_documents_valides or 0,
                    nb_documents_manquants=cl.nb_documents_manquants or 0,
                    nb_documents_expires=cl.nb_documents_expires or 0,
                ))
            else:
                # Compute on-the-fly
                result = await recalculate_compliance(db, tid, etype, eid)
                entities.append(ComplianceDashboardEntity(
                    entity_type=etype, entity_id=eid, entity_name=row.name,
                    statut_global=result.statut_global,
                    taux_conformite_pourcent=result.taux_conformite_pourcent,
                    nb_documents_requis=result.nb_documents_requis,
                    nb_documents_valides=result.nb_documents_valides,
                    nb_documents_manquants=result.nb_documents_manquants,
                    nb_documents_expires=result.nb_documents_expires,
                ))

    await db.commit()

    total = len(entities)
    nb_ok = sum(1 for e in entities if e.statut_global == "OK")
    nb_ar = sum(1 for e in entities if e.statut_global == "A_REGULARISER")
    nb_bl = sum(1 for e in entities if e.statut_global == "BLOQUANT")
    taux = round((nb_ok / total * 100), 2) if total > 0 else 100.0

    return ComplianceDashboardOut(
        total_entities=total,
        nb_conformes=nb_ok, nb_a_regulariser=nb_ar, nb_bloquants=nb_bl,
        taux_conformite_global=taux, entities=entities,
    )


@router.get("/v1/compliance/alerts", response_model=list[ComplianceAlertOut])
async def list_compliance_alerts(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = Query(None),
    statut: str | None = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    q = "SELECT * FROM compliance_alerts WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if entity_type:
        q += " AND entity_type = :etype"
        params["etype"] = entity_type.upper()
    if statut:
        q += " AND statut = :statut"
        params["statut"] = statut
    q += " ORDER BY created_at DESC LIMIT :lim OFFSET :off"
    params["lim"] = limit
    params["off"] = offset
    rows = (await db.execute(text(q), params)).fetchall()
    return [ComplianceAlertOut(
        id=str(r.id), document_id=str(r.document_id),
        entity_type=r.entity_type, entity_id=str(r.entity_id),
        type_alerte=r.type_alerte,
        date_declenchement=_ts(r.date_declenchement),
        date_expiration_document=_ts(r.date_expiration_document),
        statut=r.statut,
        date_acquittement=_ts(getattr(r, "date_acquittement", None)),
        acquittee_par=_ts(getattr(r, "acquittee_par", None)),
        notes=getattr(r, "notes", None),
        escalade_niveau=getattr(r, "escalade_niveau", 0),
        created_at=_ts(r.created_at),
    ) for r in rows]


@router.patch("/v1/compliance/alerts/{alert_id}/acknowledge",
              response_model=ComplianceAlertOut)
async def acknowledge_alert(
    alert_id: str,
    body: ComplianceAlertAcknowledge,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    uid = str(user["id"]) if isinstance(user, dict) and "id" in user else None

    row = (await db.execute(text(
        "SELECT * FROM compliance_alerts WHERE id = :id AND tenant_id = :tid"
    ), {"id": alert_id, "tid": tid})).first()
    if not row:
        raise HTTPException(404, "Alert not found")

    await db.execute(text("""
        UPDATE compliance_alerts SET
            statut = 'ACQUITTEE',
            date_acquittement = NOW(),
            acquittee_par = :uid,
            notes = COALESCE(:notes, notes),
            updated_at = NOW()
        WHERE id = :id
    """), {"id": alert_id, "uid": uid, "notes": body.notes})
    await db.commit()

    updated = (await db.execute(text(
        "SELECT * FROM compliance_alerts WHERE id = :id"
    ), {"id": alert_id})).first()
    return ComplianceAlertOut(
        id=str(updated.id), document_id=str(updated.document_id),
        entity_type=updated.entity_type, entity_id=str(updated.entity_id),
        type_alerte=updated.type_alerte,
        date_declenchement=_ts(updated.date_declenchement),
        date_expiration_document=_ts(updated.date_expiration_document),
        statut=updated.statut,
        date_acquittement=_ts(updated.date_acquittement),
        acquittee_par=_ts(updated.acquittee_par),
        notes=updated.notes,
        escalade_niveau=updated.escalade_niveau,
        created_at=_ts(updated.created_at),
    )


# ── Compliance Templates CRUD ────────────────────────────────────

@router.get("/v1/compliance/templates", response_model=list[ComplianceTemplateOut])
async def list_templates(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = Query(None),
):
    q = "SELECT * FROM compliance_templates WHERE tenant_id = :tid"
    params: dict = {"tid": str(tenant.tenant_id)}
    if entity_type:
        q += " AND entity_type = :etype"
        params["etype"] = entity_type.upper()
    q += " ORDER BY entity_type, ordre_affichage"
    rows = (await db.execute(text(q), params)).fetchall()
    return [_template_from_row(r) for r in rows]


@router.post("/v1/compliance/templates", response_model=ComplianceTemplateOut,
             status_code=201)
async def create_template(
    body: ComplianceTemplateCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    tpl_id = uuid.uuid4()
    cond_json = json.dumps(body.condition_applicabilite) if body.condition_applicabilite else None
    alertes_val = "{" + ",".join(str(a) for a in body.alertes_jours) + "}" if body.alertes_jours else None

    await db.execute(text("""
        INSERT INTO compliance_templates (
            id, tenant_id, entity_type, type_document, libelle,
            obligatoire, bloquant, condition_applicabilite,
            duree_validite_defaut_jours, alertes_jours,
            ordre_affichage, is_active
        ) VALUES (
            :id, :tid, :etype, :dtype, :lib,
            :oblig, :bloq, :cond,
            :duree, :alertes,
            :ordre, :active
        )
    """), {
        "id": str(tpl_id), "tid": tid,
        "etype": body.entity_type.upper(), "dtype": body.type_document,
        "lib": body.libelle, "oblig": body.obligatoire, "bloq": body.bloquant,
        "cond": cond_json, "duree": body.duree_validite_defaut_jours,
        "alertes": alertes_val, "ordre": body.ordre_affichage,
        "active": body.is_active,
    })
    await db.commit()

    row = (await db.execute(text(
        "SELECT * FROM compliance_templates WHERE id = :id"
    ), {"id": str(tpl_id)})).first()
    return _template_from_row(row)


@router.put("/v1/compliance/templates/{tpl_id}", response_model=ComplianceTemplateOut)
async def update_template(
    tpl_id: str,
    body: ComplianceTemplateCreate,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tid = str(tenant.tenant_id)
    existing = (await db.execute(text(
        "SELECT id FROM compliance_templates WHERE id = :id AND tenant_id = :tid"
    ), {"id": tpl_id, "tid": tid})).first()
    if not existing:
        raise HTTPException(404, "Template not found")

    cond_json = json.dumps(body.condition_applicabilite) if body.condition_applicabilite else None
    alertes_val = "{" + ",".join(str(a) for a in body.alertes_jours) + "}" if body.alertes_jours else None

    await db.execute(text("""
        UPDATE compliance_templates SET
            entity_type = :etype, type_document = :dtype, libelle = :lib,
            obligatoire = :oblig, bloquant = :bloq,
            condition_applicabilite = :cond,
            duree_validite_defaut_jours = :duree, alertes_jours = :alertes,
            ordre_affichage = :ordre, is_active = :active,
            updated_at = NOW()
        WHERE id = :id
    """), {
        "id": tpl_id, "etype": body.entity_type.upper(), "dtype": body.type_document,
        "lib": body.libelle, "oblig": body.obligatoire, "bloq": body.bloquant,
        "cond": cond_json, "duree": body.duree_validite_defaut_jours,
        "alertes": alertes_val, "ordre": body.ordre_affichage,
        "active": body.is_active,
    })
    await db.commit()

    row = (await db.execute(text(
        "SELECT * FROM compliance_templates WHERE id = :id"
    ), {"id": tpl_id})).first()
    return _template_from_row(row)


# ── Legacy compat: /v1/documents/compliance ──────────────────────

@router.get("/v1/documents/compliance")
async def legacy_compliance_dashboard(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = Query(None),
):
    """Legacy endpoint — returns flat ComplianceItem list for backward compat."""
    from app.modules.documents.schemas import ComplianceChecklistItem

    items = []
    tid = str(tenant.tenant_id)

    for etype in ([entity_type] if entity_type else ["driver", "vehicle"]):
        etype_upper = etype.upper()
        if etype_upper == "DRIVER":
            entity_q = """SELECT id, COALESCE(nom, last_name, '') || ' ' ||
                          COALESCE(prenom, first_name, '') AS name
                          FROM drivers WHERE tenant_id = :tid
                          AND (is_active = true OR statut = 'ACTIF')"""
        elif etype_upper == "VEHICLE":
            entity_q = """SELECT id, COALESCE(immatriculation, plate_number, '') AS name
                          FROM vehicles WHERE tenant_id = :tid
                          AND (is_active = true OR statut = 'ACTIF')"""
        else:
            continue

        entities = (await db.execute(text(entity_q), {"tid": tid})).fetchall()

        # Try compliance_templates first, fall back to document_types
        templates = (await db.execute(text("""
            SELECT type_document AS code, libelle AS label, obligatoire AS is_mandatory
            FROM compliance_templates
            WHERE tenant_id = :tid AND entity_type = :etype AND is_active = true
            ORDER BY ordre_affichage
        """), {"tid": tid, "etype": etype_upper})).fetchall()

        if not templates:
            templates = (await db.execute(text("""
                SELECT code, label, is_mandatory
                FROM document_types
                WHERE tenant_id = :tid AND entity_type = :etype
            """), {"tid": tid, "etype": etype})).fetchall()

        for entity in entities:
            for dt in templates:
                doc = (await db.execute(text("""
                    SELECT id, expiry_date, date_expiration, compliance_status, statut
                    FROM documents
                    WHERE tenant_id = :tid AND entity_type IN (:etype, :etype_low)
                      AND entity_id = :eid
                      AND doc_type = :dtype
                      AND COALESCE(statut, 'VALIDE') NOT IN ('ARCHIVE', 'REJETE')
                    ORDER BY created_at DESC LIMIT 1
                """), {
                    "tid": tid, "etype": etype_upper, "etype_low": etype.lower(),
                    "eid": str(entity.id), "dtype": dt.code,
                })).first()

                if doc:
                    status = doc.compliance_status or doc.statut or "valid"
                    exp = doc.date_expiration or doc.expiry_date
                    items.append({
                        "entity_type": etype, "entity_id": str(entity.id),
                        "entity_name": entity.name,
                        "doc_type_code": dt.code, "doc_type_label": dt.label,
                        "is_mandatory": dt.is_mandatory, "status": status,
                        "expiry_date": str(exp) if exp else None,
                        "document_id": str(doc.id),
                    })
                else:
                    items.append({
                        "entity_type": etype, "entity_id": str(entity.id),
                        "entity_name": entity.name,
                        "doc_type_code": dt.code, "doc_type_label": dt.label,
                        "is_mandatory": dt.is_mandatory, "status": "missing",
                    })

    return items


# ── New compliance endpoints for UI banners/widgets ──────────────

@router.get("/v1/compliance/upcoming-expirations")
async def upcoming_expirations(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(90, ge=1, le=365),
):
    """Documents expiring within N days — for dashboard widgets and alert banners."""
    tid = str(tenant.tenant_id)
    rows = (await db.execute(text("""
        SELECT d.id, d.entity_type, d.entity_id, d.doc_type, d.date_expiration,
               d.statut, d.is_critical,
               CASE
                   WHEN d.date_expiration < CURRENT_DATE THEN 'EXPIRED'
                   WHEN d.date_expiration <= CURRENT_DATE + :days * INTERVAL '1 day' THEN 'EXPIRING'
                   ELSE 'OK'
               END AS urgency,
               (d.date_expiration - CURRENT_DATE) AS days_remaining,
               CASE d.entity_type
                   WHEN 'driver' THEN (SELECT COALESCE(nom, last_name, '') || ' ' || COALESCE(prenom, first_name, '') FROM drivers WHERE id = d.entity_id)
                   WHEN 'vehicle' THEN (SELECT COALESCE(immatriculation, plate_number, '') FROM vehicles WHERE id = d.entity_id)
                   ELSE ''
               END AS entity_name
        FROM documents d
        WHERE d.tenant_id = :tid
          AND d.date_expiration IS NOT NULL
          AND d.date_expiration <= CURRENT_DATE + :days * INTERVAL '1 day'
          AND COALESCE(d.statut, 'VALIDE') NOT IN ('ARCHIVE', 'REJETE', 'BROUILLON')
        ORDER BY d.date_expiration ASC
    """), {"tid": tid, "days": days})).fetchall()

    return [
        {
            "id": str(r.id),
            "entity_type": r.entity_type,
            "entity_id": str(r.entity_id),
            "entity_name": r.entity_name,
            "doc_type": r.doc_type,
            "date_expiration": r.date_expiration.isoformat() if r.date_expiration else None,
            "urgency": r.urgency,
            "days_remaining": r.days_remaining,
            "is_critical": r.is_critical,
            "statut": r.statut,
        }
        for r in rows
    ]


@router.get("/v1/compliance/entity-statuses")
async def entity_compliance_statuses(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = Query(None),
):
    """Compliance status per entity — for list page row highlighting.
    Returns a map of entity_id → {statut_global, nb_expired, nb_expiring, next_expiry}.
    """
    tid = str(tenant.tenant_id)
    etype_filter = ""
    params: dict = {"tid": tid}
    if entity_type:
        etype_filter = "AND entity_type = :etype"
        params["etype"] = entity_type.lower()

    rows = (await db.execute(text(f"""
        SELECT entity_type, entity_id, statut_global,
               nb_documents_expires, nb_documents_expirant_bientot,
               nb_documents_manquants, taux_conformite_pourcent
        FROM compliance_checklists
        WHERE tenant_id = :tid {etype_filter}
    """), params)).fetchall()

    return {
        str(r.entity_id): {
            "statut_global": r.statut_global,
            "nb_expired": r.nb_documents_expires,
            "nb_expiring": r.nb_documents_expirant_bientot,
            "nb_missing": r.nb_documents_manquants,
            "taux_conformite": float(r.taux_conformite_pourcent) if r.taux_conformite_pourcent else 100,
        }
        for r in rows
    }
