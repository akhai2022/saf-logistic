"""
Backfill compliance documents from SAF integration data.

Creates documents table records from the driver/vehicle expiry dates
extracted from the integration spreadsheets. Idempotent — safe to re-run.

Usage:
  python -m app.core.backfill_compliance
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory

# ── Driver document expiry dates from integration spreadsheets ─────
# Source: "Document Chauffeur" sheet in Tableau Document global.xlsb.xlsx
DRIVER_DOCUMENTS = [
    {"name": "ABDALLAH Fouad", "carte_identite": "2033-07-18", "permis_conduire": "2028-11-02", "adr": "2026-11-05", "carte_conducteur": "2028-12-18", "fco": "2027-11-25", "visite_medicale": "2027-07-21"},
    {"name": "ABDALLAH Khaled", "carte_identite": "2034-04-25", "permis_conduire": "2039-10-15", "visite_medicale": "2024-10-03"},
    {"name": "ABDALLAH Sofiane", "carte_identite": "2031-06-06", "permis_conduire": "2028-06-08", "carte_conducteur": "2028-04-12", "fco": "2027-06-24", "visite_medicale": "2028-05-19"},
    {"name": "AKLAL Lahcen", "carte_identite": "2033-09-13", "permis_conduire": "2028-10-17", "adr": "2028-07-25", "carte_conducteur": "2028-09-13", "fco": "2028-08-04", "visite_medicale": "2028-03-02"},
    {"name": "BENACHOUR Kamel", "carte_identite": "2035-05-26", "permis_conduire": "2030-12-05", "adr": "2028-10-17", "carte_conducteur": "2026-02-21", "fco": "2031-02-06", "visite_medicale": "2028-11-05"},
    {"name": "BENALI Mokhtar", "carte_identite": "2026-01-21", "permis_conduire": "2028-04-14", "carte_conducteur": "2028-05-30", "visite_medicale": "2028-03-02"},
    {"name": "BENALLOU Mohammed", "carte_identite": "2028-10-30", "permis_conduire": "2034-01-28", "adr": "2019-11-05", "carte_conducteur": "2028-06-04", "visite_medicale": "2026-07-09"},
    {"name": "BETTIOUI Badr", "carte_identite": "2024-08-30", "permis_conduire": "2027-03-29", "adr": "2028-11-28", "carte_conducteur": "2027-06-09", "fco": "2027-06-08", "visite_medicale": "2027-02-15"},
    {"name": "BOUKZINE Mouloud", "carte_identite": "2032-01-29", "permis_conduire": "2026-12-06", "adr": "2023-03-01", "carte_conducteur": "2029-09-30", "fco": "2028-01-06"},
    {"name": "BRILLANT Eddy", "carte_identite": "2031-12-13", "permis_conduire": "2028-05-22", "adr": "2028-01-05", "carte_conducteur": "2028-06-20", "fco": "2028-04-07", "visite_medicale": "2027-12-14"},
    {"name": "CHENHAOUI Rachid", "carte_identite": "2025-02-06", "permis_conduire": "2025-11-20", "adr": "2026-11-05", "carte_conducteur": "2028-09-21", "fco": "2029-03-08", "visite_medicale": "2025-11-20"},
    {"name": "DAHDOUD Abdelhadi", "carte_identite": "2029-09-21", "permis_conduire": "2027-01-14", "adr": "2026-10-07", "carte_conducteur": "2029-01-15", "fco": "2029-01-12", "visite_medicale": "2026-12-14"},
    {"name": "DOUZI Mohammed", "carte_identite": "2026-05-09", "permis_conduire": "2029-05-10", "adr": "2030-12-24", "carte_conducteur": "2028-12-10", "fco": "2029-12-06"},
    {"name": "DRAME Abdou", "carte_identite": "2026-11-28", "permis_conduire": "2029-08-01", "carte_conducteur": "2029-10-06", "fco": "2030-05-30", "visite_medicale": "2029-04-16"},
    {"name": "EL IDRISSI Rachid", "carte_identite": "2033-03-20", "permis_conduire": "2029-10-16", "adr": "2030-06-06", "carte_conducteur": "2030-04-13", "fco": "2028-12-01", "visite_medicale": "2028-08-27"},
    {"name": "GHANDOUR Abdallah", "permis_conduire": "2028-12-20", "adr": "2029-02-27"},
    {"name": "GOMIS Yohan", "carte_identite": "2035-12-04", "permis_conduire": "2030-11-06", "carte_conducteur": "2030-12-15"},
    {"name": "KARRADA Youssef", "permis_conduire": "2026-05-28", "carte_conducteur": "2027-04-18", "fco": "2027-02-03", "visite_medicale": "2026-03-23"},
    {"name": "KONATE Youssouf", "carte_identite": "2035-02-09", "permis_conduire": "2029-08-14", "adr": "2029-07-05", "carte_conducteur": "2029-08-11", "fco": "2029-07-05", "visite_medicale": "2029-04-02"},
    {"name": "MADJID Abdarrahmane", "carte_identite": "2035-05-03", "permis_conduire": "2030-03-04", "adr": "2026-04-09", "carte_conducteur": "2028-04-24", "fco": "2028-11-10", "visite_medicale": "2030-03-04"},
    {"name": "MAJD Rachid", "carte_identite": "2033-02-07", "permis_conduire": "2028-03-08", "fco": "2030-09-11", "visite_medicale": "2028-02-21"},
    {"name": "OULAIN Mustapha", "carte_identite": "2034-04-09", "permis_conduire": "2030-01-28", "adr": "2030-05-13", "carte_conducteur": "2030-04-29", "fco": "2030-04-28", "visite_medicale": "2029-08-25"},
    {"name": "WAMBA Christian", "carte_identite": "2031-07-21", "permis_conduire": "2027-12-06", "adr": "2029-05-22", "carte_conducteur": "2027-12-26", "fco": "2027-06-07", "visite_medicale": "2026-09-10"},
]

# Document type code → compliance template code mapping
DOC_TYPE_MAP = {
    "carte_identite": "carte_identite",
    "permis_conduire": "permis_conduire",
    "fco": "fco",
    "adr": "adr",
    "carte_conducteur": "carte_conducteur",
    "visite_medicale": "visite_medicale",
}

# SAF Logistique tenant ID
TENANT_ID = "10000000-0000-0000-0000-000000000001"


def _to_date(v: str | None) -> date | None:
    if not v:
        return None
    try:
        return date.fromisoformat(v)
    except (ValueError, TypeError):
        return None


async def backfill(db: AsyncSession) -> None:
    tid = TENANT_ID
    today = date.today()
    stats = {"created": 0, "skipped": 0, "expired_found": 0}

    # ── 1. DRIVER DOCUMENTS ──────────────────────────────────────────
    print("Backfilling driver documents...")

    for dd in DRIVER_DOCUMENTS:
        # Find driver by name (NOM Prenom pattern)
        name_parts = dd["name"].strip().split(" ", 1)
        nom = name_parts[0].upper()
        prenom = name_parts[1] if len(name_parts) > 1 else ""

        driver = (await db.execute(text("""
            SELECT id FROM drivers
            WHERE tenant_id = :tid AND UPPER(nom) = :nom
            LIMIT 1
        """), {"tid": tid, "nom": nom})).first()

        if not driver:
            # Try with last_name fallback
            driver = (await db.execute(text("""
                SELECT id FROM drivers
                WHERE tenant_id = :tid AND UPPER(last_name) = :nom
                LIMIT 1
            """), {"tid": tid, "nom": nom})).first()

        if not driver:
            print(f"  SKIP: driver not found: {dd['name']}")
            stats["skipped"] += 1
            continue

        driver_id = str(driver.id)

        for field_key, doc_type_code in DOC_TYPE_MAP.items():
            expiry_str = dd.get(field_key)
            expiry = _to_date(expiry_str)
            if not expiry:
                continue

            # Idempotency: check if document already exists
            existing = (await db.execute(text("""
                SELECT id FROM documents
                WHERE tenant_id = :tid AND entity_type = 'driver' AND entity_id = :eid
                  AND doc_type = :dtype
                  AND COALESCE(statut, 'VALIDE') NOT IN ('ARCHIVE', 'REJETE')
                LIMIT 1
            """), {"tid": tid, "eid": driver_id, "dtype": doc_type_code})).first()

            if existing:
                stats["skipped"] += 1
                continue

            # Determine status
            is_expired = expiry < today
            statut = "EXPIRE" if is_expired else "VALIDE"
            compliance_status = "expired" if is_expired else "valid"
            if is_expired:
                stats["expired_found"] += 1

            doc_id = uuid.uuid4()
            await db.execute(text("""
                INSERT INTO documents (
                    id, tenant_id, entity_type, entity_id, doc_type,
                    date_expiration, expiry_date, date_emission, issue_date,
                    statut, compliance_status, is_critical,
                    notes, created_at
                ) VALUES (
                    :id, :tid, 'driver', :eid, :dtype,
                    :exp, :exp, :exp, :exp,
                    :statut, :cs, :crit,
                    :notes, NOW()
                )
            """), {
                "id": str(doc_id), "tid": tid, "eid": driver_id, "dtype": doc_type_code,
                "exp": expiry, "statut": statut, "cs": compliance_status,
                "crit": doc_type_code in ("permis_conduire", "fco", "carte_conducteur", "visite_medicale"),
                "notes": f"Importe depuis donnees integration SAF ({dd['name']})",
            })
            stats["created"] += 1

    # ── 2. VEHICLE DOCUMENTS ─────────────────────────────────────────
    print("Backfilling vehicle documents...")

    # Get all vehicles with inspection dates
    vehicles = (await db.execute(text("""
        SELECT id, COALESCE(immatriculation, plate_number) AS plate,
               controle_technique_date, limiteur_vitesse_date, tachygraphe_date,
               assurance_compagnie
        FROM vehicles WHERE tenant_id = :tid
    """), {"tid": tid})).fetchall()

    vehicle_doc_map = {
        "controle_technique_date": "controle_technique",
        "limiteur_vitesse_date": "controle_technique",  # limiteur tracked as sub-type of CT
        "tachygraphe_date": "controle_technique",       # tachygraphe tracked as sub-type of CT
    }

    for v in vehicles:
        vehicle_id = str(v.id)

        # Contrôle technique
        if v.controle_technique_date:
            existing = (await db.execute(text("""
                SELECT id FROM documents
                WHERE tenant_id = :tid AND entity_type = 'vehicle' AND entity_id = :eid
                  AND doc_type = 'controle_technique'
                  AND COALESCE(statut, 'VALIDE') NOT IN ('ARCHIVE', 'REJETE')
                LIMIT 1
            """), {"tid": tid, "eid": vehicle_id})).first()

            if not existing:
                is_expired = v.controle_technique_date < today
                doc_id = uuid.uuid4()
                await db.execute(text("""
                    INSERT INTO documents (
                        id, tenant_id, entity_type, entity_id, doc_type,
                        date_expiration, expiry_date, statut, compliance_status, is_critical,
                        notes, created_at
                    ) VALUES (
                        :id, :tid, 'vehicle', :eid, 'controle_technique',
                        :exp, :exp, :statut, :cs, true,
                        :notes, NOW()
                    )
                """), {
                    "id": str(doc_id), "tid": tid, "eid": vehicle_id,
                    "exp": v.controle_technique_date,
                    "statut": "EXPIRE" if is_expired else "VALIDE",
                    "cs": "expired" if is_expired else "valid",
                    "notes": f"CT vehicule {v.plate}",
                })
                stats["created"] += 1
                if is_expired:
                    stats["expired_found"] += 1

        # Assurance (create as document if insurance company is known)
        if v.assurance_compagnie:
            existing = (await db.execute(text("""
                SELECT id FROM documents
                WHERE tenant_id = :tid AND entity_type = 'vehicle' AND entity_id = :eid
                  AND doc_type = 'assurance'
                  AND COALESCE(statut, 'VALIDE') NOT IN ('ARCHIVE', 'REJETE')
                LIMIT 1
            """), {"tid": tid, "eid": vehicle_id})).first()

            if not existing:
                # Insurance typically valid 1 year — set expiry to end of current year
                exp = date(today.year, 12, 31)
                doc_id = uuid.uuid4()
                await db.execute(text("""
                    INSERT INTO documents (
                        id, tenant_id, entity_type, entity_id, doc_type,
                        date_expiration, expiry_date, statut, compliance_status, is_critical,
                        organisme_emetteur, notes, created_at
                    ) VALUES (
                        :id, :tid, 'vehicle', :eid, 'assurance',
                        :exp, :exp, 'VALIDE', 'valid', true,
                        :org, :notes, NOW()
                    )
                """), {
                    "id": str(doc_id), "tid": tid, "eid": vehicle_id,
                    "exp": exp, "org": v.assurance_compagnie,
                    "notes": f"Assurance {v.assurance_compagnie} - {v.plate}",
                })
                stats["created"] += 1

    await db.commit()

    # ── 3. TRIGGER COMPLIANCE RECALCULATION ──────────────────────────
    print("Recalculating compliance checklists...")
    # Get all entities that have documents
    entities = (await db.execute(text("""
        SELECT DISTINCT entity_type, entity_id FROM documents WHERE tenant_id = :tid
    """), {"tid": tid})).fetchall()

    for ent in entities:
        # Get templates for this entity type
        templates = (await db.execute(text("""
            SELECT type_document, obligatoire, bloquant FROM compliance_templates
            WHERE tenant_id = :tid AND entity_type = UPPER(:etype) AND is_active = true
        """), {"tid": tid, "etype": ent.entity_type})).fetchall()

        nb_requis = len(templates)
        nb_valides = 0
        nb_manquants = 0
        nb_expires = 0
        nb_expirant = 0
        has_blocking_issue = False

        for tmpl in templates:
            doc = (await db.execute(text("""
                SELECT date_expiration, statut FROM documents
                WHERE tenant_id = :tid AND entity_type = :etype AND entity_id = :eid
                  AND doc_type = :dtype
                  AND COALESCE(statut, 'VALIDE') NOT IN ('ARCHIVE', 'REJETE', 'BROUILLON')
                ORDER BY version DESC, created_at DESC LIMIT 1
            """), {"tid": tid, "etype": ent.entity_type, "eid": str(ent.entity_id), "dtype": tmpl.type_document})).first()

            if not doc:
                nb_manquants += 1
                if tmpl.bloquant:
                    has_blocking_issue = True
            elif doc.statut == "EXPIRE" or (doc.date_expiration and doc.date_expiration < today):
                nb_expires += 1
                if tmpl.bloquant:
                    has_blocking_issue = True
            elif doc.date_expiration and (doc.date_expiration - today).days <= 60:
                nb_expirant += 1
                nb_valides += 1
            else:
                nb_valides += 1

        taux = (nb_valides / nb_requis * 100) if nb_requis > 0 else 100
        if has_blocking_issue:
            statut_global = "BLOQUANT"
        elif nb_manquants > 0 or nb_expires > 0 or nb_expirant > 0:
            statut_global = "A_REGULARISER"
        else:
            statut_global = "OK"

        await db.execute(text("""
            INSERT INTO compliance_checklists (
                id, tenant_id, entity_type, entity_id,
                statut_global, nb_documents_requis, nb_documents_valides,
                nb_documents_manquants, nb_documents_expires, nb_documents_expirant_bientot,
                taux_conformite_pourcent, derniere_mise_a_jour
            ) VALUES (
                :id, :tid, :etype, :eid,
                :sg, :req, :val, :man, :exp, :soon, :taux, NOW()
            )
            ON CONFLICT (tenant_id, entity_type, entity_id) DO UPDATE SET
                statut_global = EXCLUDED.statut_global,
                nb_documents_requis = EXCLUDED.nb_documents_requis,
                nb_documents_valides = EXCLUDED.nb_documents_valides,
                nb_documents_manquants = EXCLUDED.nb_documents_manquants,
                nb_documents_expires = EXCLUDED.nb_documents_expires,
                nb_documents_expirant_bientot = EXCLUDED.nb_documents_expirant_bientot,
                taux_conformite_pourcent = EXCLUDED.taux_conformite_pourcent,
                derniere_mise_a_jour = NOW()
        """), {
            "id": str(uuid.uuid4()), "tid": tid,
            "etype": ent.entity_type, "eid": str(ent.entity_id),
            "sg": statut_global, "req": nb_requis, "val": nb_valides,
            "man": nb_manquants, "exp": nb_expires, "soon": nb_expirant,
            "taux": round(taux, 2),
        })

        # Update entity conformite_statut
        table = "drivers" if ent.entity_type == "driver" else "vehicles"
        await db.execute(text(f"""
            UPDATE {table} SET conformite_statut = :sg WHERE id = :eid AND tenant_id = :tid
        """), {"sg": statut_global, "eid": str(ent.entity_id), "tid": tid})

    await db.commit()

    print("=" * 60)
    print("Compliance backfill completed.")
    print(f"  Documents created:  {stats['created']}")
    print(f"  Documents skipped:  {stats['skipped']} (already exist)")
    print(f"  Already expired:    {stats['expired_found']}")
    print(f"  Entities updated:   {len(entities)}")
    print("=" * 60)


async def main() -> None:
    async with async_session_factory() as db:
        await backfill(db)


if __name__ == "__main__":
    asyncio.run(main())
