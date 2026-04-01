"""Business logic for the bulk import module.

Orchestrates file storage, parsing, validation, and upsert for
drivers, vehicles, clients, and subcontractors.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.imports.field_maps import (
    ENTITY_REQUIRED_FIELDS,
    VALID_ENTITY_TYPES,
    auto_detect_mapping,
)
from app.modules.imports.parsers import parse_file
from app.modules.imports.schemas import ApplyResult, ImportError as ImportErrorSchema, PreviewResult
from app.modules.masterdata.schemas import (
    ClientCreate,
    DriverCreate,
    SubcontractorCreate,
    VehicleCreate,
)

logger = logging.getLogger(__name__)

# Schema class per entity type
_ENTITY_SCHEMA = {
    "driver": DriverCreate,
    "vehicle": VehicleCreate,
    "client": ClientCreate,
    "subcontractor": SubcontractorCreate,
}

# Boolean-like values accepted from CSV
_TRUTHY = {"oui", "o", "yes", "y", "1", "true", "vrai", "x"}
_FALSY = {"non", "n", "no", "0", "false", "faux", ""}

# Fields that should be parsed as lists (comma-separated in CSV)
_LIST_FIELDS = {
    "categorie_permis", "qualification_adr_classes",
    "zones_geographiques", "types_vehicules_disponibles", "specialites",
}

# Fields that represent booleans on the Pydantic schemas
_BOOL_FIELDS = {
    "qualification_fimo", "qualification_fco", "qualification_adr",
    "tacite_reconduction", "telematique", "presence_matiere_dangereuse",
    "is_contact_principal", "is_contact_facturation", "is_contact_exploitation",
    "is_active",
}

# Fields that represent integers
_INT_FIELDS = {
    "ptac_kg", "ptra_kg", "charge_utile_kg", "nb_palettes_europe", "nb_essieux",
    "km_compteur_actuel", "annee_mise_en_circulation", "nombre_places",
    "delai_paiement_jours", "sla_delai_livraison_heures",
}

# Fields that represent decimals
_DECIMAL_FIELDS = {
    "volume_m3", "longueur_utile_m", "largeur_utile_m", "hauteur_utile_m",
    "temperature_min", "temperature_max", "salaire_base_mensuel", "taux_horaire",
    "escompte_pourcent", "penalite_retard_pourcent", "indemnite_recouvrement",
    "plafond_encours", "sla_taux_service_pourcent", "note_qualite",
    "valeur_assuree_ht",
}


def _coerce_value(field_name: str, raw: str) -> Any:
    """Coerce a raw string value to the expected Python type for a schema field."""
    if field_name in _BOOL_FIELDS:
        low = raw.strip().lower()
        if low in _TRUTHY:
            return True
        if low in _FALSY:
            return False
        return raw  # let Pydantic validation report the error

    if field_name in _LIST_FIELDS:
        if not raw.strip():
            return None
        # Accept comma or semicolon as list separator
        sep = "," if "," in raw else ";"
        return [item.strip() for item in raw.split(sep) if item.strip()]

    if field_name in _INT_FIELDS:
        raw = raw.strip()
        if not raw:
            return None
        # Remove spaces, handle decimal comma
        raw = raw.replace(" ", "").replace(",", ".")
        try:
            return int(float(raw))
        except (ValueError, OverflowError):
            return raw  # let Pydantic report

    if field_name in _DECIMAL_FIELDS:
        raw = raw.strip()
        if not raw:
            return None
        raw = raw.replace(" ", "").replace(",", ".")
        try:
            return Decimal(raw)
        except InvalidOperation:
            return raw

    # Default: return stripped string, or None if empty
    raw = raw.strip()
    return raw if raw else None


def _map_row(row: dict[str, str], mapping: dict[str, str]) -> dict[str, Any]:
    """Apply column mapping and type coercion to a single parsed row."""
    result: dict[str, Any] = {}
    for csv_header, field_name in mapping.items():
        raw = row.get(csv_header, "")
        result[field_name] = _coerce_value(field_name, raw)
    return result


def _validate_row(
    row_data: dict[str, Any],
    entity_type: str,
    row_num: int,
) -> tuple[Any | None, list[ImportErrorSchema]]:
    """Validate a single mapped row against the entity's Pydantic schema.

    Returns (validated_model_or_None, list_of_errors).
    """
    schema_cls = _ENTITY_SCHEMA[entity_type]
    errors: list[ImportErrorSchema] = []

    try:
        model = schema_cls(**row_data)
        return model, []
    except ValidationError as exc:
        for err in exc.errors():
            loc = err.get("loc", ())
            col = str(loc[-1]) if loc else None
            errors.append(ImportErrorSchema(
                row=row_num,
                column=col,
                message=err.get("msg", "Erreur de validation"),
                value=str(row_data.get(col, "")) if col else None,
            ))
        return None, errors


# ══════════════════════════════════════════════════════════════════
# SERVICE FUNCTIONS
# ══════════════════════════════════════════════════════════════════


async def create_import_job(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    entity_type: str,
    file_name: str,
    content_type: str,
    file_content: bytes,
) -> dict[str, Any]:
    """Upload file to S3 and create the import_jobs DB row.

    Returns the row as a dict.
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(f"Type d'entite inconnu: {entity_type}. Valeurs: {', '.join(sorted(VALID_ENTITY_TYPES))}")

    # Upload to S3
    from app.infra.s3 import _get_s3_client
    from app.core.settings import settings

    job_id = uuid.uuid4()
    ext = file_name.rsplit(".", 1)[-1] if "." in file_name else "bin"
    s3_key = f"{tenant_id}/imports/{job_id}.{ext}"

    s3 = _get_s3_client()
    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=s3_key,
        Body=file_content,
        ContentType=content_type,
    )

    await db.execute(text("""
        INSERT INTO import_jobs (id, tenant_id, entity_type, status, file_name, file_s3_key, content_type, created_by)
        VALUES (:id, :tid, :etype, 'uploaded', :fname, :s3key, :ctype, :uid)
    """), {
        "id": str(job_id),
        "tid": str(tenant_id),
        "etype": entity_type,
        "fname": file_name,
        "s3key": s3_key,
        "ctype": content_type,
        "uid": str(user_id),
    })
    await db.commit()

    return {
        "id": str(job_id),
        "tenant_id": str(tenant_id),
        "entity_type": entity_type,
        "status": "uploaded",
        "file_name": file_name,
        "file_s3_key": s3_key,
        "content_type": content_type,
    }


async def get_import_job(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    job_id: str,
) -> dict[str, Any] | None:
    """Fetch a single import job with tenant guard."""
    row = (await db.execute(
        text("SELECT * FROM import_jobs WHERE id = :id AND tenant_id = :tid"),
        {"id": job_id, "tid": str(tenant_id)},
    )).first()
    if not row:
        return None
    return _job_row_to_dict(row)


def _job_row_to_dict(row: Any) -> dict[str, Any]:
    """Convert a DB row to a plain dict."""
    return {
        "id": str(row.id),
        "tenant_id": str(row.tenant_id),
        "entity_type": row.entity_type,
        "status": row.status,
        "file_name": row.file_name,
        "file_s3_key": row.file_s3_key,
        "content_type": row.content_type,
        "total_rows": row.total_rows,
        "valid_rows": row.valid_rows,
        "error_rows": row.error_rows,
        "inserted_rows": row.inserted_rows,
        "updated_rows": row.updated_rows,
        "skipped_rows": row.skipped_rows,
        "column_mapping": row.column_mapping,
        "preview_data": row.preview_data,
        "errors_json": row.errors_json,
        "created_by": str(row.created_by) if row.created_by else None,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _download_file(s3_key: str) -> bytes:
    """Download a file from S3."""
    from app.infra.s3 import _get_s3_client
    from app.core.settings import settings

    s3 = _get_s3_client()
    resp = s3.get_object(Bucket=settings.S3_BUCKET, Key=s3_key)
    return resp["Body"].read()


async def preview_import(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    job_id: str,
    user_mapping: dict[str, str] | None = None,
) -> PreviewResult:
    """Parse file, detect/apply mapping, validate each row, return preview.

    Does NOT write any entity data -- only updates the import_jobs row with
    preview_data, column_mapping, and errors_json.
    """
    job = await get_import_job(db, tenant_id, job_id)
    if not job:
        raise ValueError("Import job introuvable.")

    file_content = _download_file(job["file_s3_key"])
    headers, rows = parse_file(file_content, job["file_name"])
    entity_type = job["entity_type"]

    # Build mapping
    if user_mapping:
        mapping = user_mapping
    else:
        mapping = auto_detect_mapping(headers, entity_type)

    # Check required fields coverage
    required = ENTITY_REQUIRED_FIELDS.get(entity_type, set())
    mapped_fields = set(mapping.values())
    missing_required = required - mapped_fields
    if missing_required:
        raise ValueError(
            f"Colonnes obligatoires non trouvees dans le fichier: {', '.join(sorted(missing_required))}. "
            f"Colonnes detectees: {', '.join(headers)}"
        )

    # Validate each row
    all_errors: list[ImportErrorSchema] = []
    valid_count = 0
    sample_rows: list[dict[str, Any]] = []

    for idx, raw_row in enumerate(rows):
        row_num = idx + 2  # header is row 1
        mapped = _map_row(raw_row, mapping)
        model, row_errors = _validate_row(mapped, entity_type, row_num)

        if row_errors:
            all_errors.extend(row_errors)
        else:
            valid_count += 1

        # Keep first 10 rows as preview sample
        if idx < 10:
            sample_rows.append({
                "row_num": row_num,
                "raw": raw_row,
                "mapped": {k: _serialise_value(v) for k, v in mapped.items()},
                "valid": len(row_errors) == 0,
                "errors": [e.model_dump() for e in row_errors],
            })

    total = len(rows)
    error_count = total - valid_count

    # Serialise errors for DB storage
    errors_json = [e.model_dump() for e in all_errors]

    # Update job
    await db.execute(text("""
        UPDATE import_jobs
        SET status = 'previewed',
            total_rows = :total,
            valid_rows = :valid,
            error_rows = :errors,
            column_mapping = CAST(:mapping AS jsonb),
            preview_data = CAST(:preview AS jsonb),
            errors_json = CAST(:errs AS jsonb),
            updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": job_id,
        "tid": str(tenant_id),
        "total": total,
        "valid": valid_count,
        "errors": error_count,
        "mapping": json.dumps(mapping),
        "preview": json.dumps(sample_rows, default=str),
        "errs": json.dumps(errors_json, default=str),
    })
    await db.commit()

    return PreviewResult(
        job_id=job_id,
        entity_type=entity_type,
        total_rows=total,
        valid_rows=valid_count,
        error_rows=error_count,
        detected_mapping=mapping,
        sample_rows=sample_rows,
        errors=all_errors,
    )


def _serialise_value(v: Any) -> Any:
    """Make a value JSON-serialisable."""
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, uuid.UUID):
        return str(v)
    return v


async def apply_import(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    job_id: str,
    user_mapping: dict[str, str] | None = None,
) -> ApplyResult:
    """Re-parse file, validate, and upsert valid rows into the database.

    Uses INSERT ON CONFLICT DO UPDATE with natural keys:
    - drivers: (tenant_id, matricule)
    - vehicles: (tenant_id, immatriculation)
    - clients: (tenant_id, code)
    - subcontractors: (tenant_id, code)
    """
    job = await get_import_job(db, tenant_id, job_id)
    if not job:
        raise ValueError("Import job introuvable.")

    if job["status"] == "applied":
        raise ValueError("Cet import a deja ete applique.")

    file_content = _download_file(job["file_s3_key"])
    headers, rows = parse_file(file_content, job["file_name"])
    entity_type = job["entity_type"]

    # Determine mapping
    mapping = user_mapping or job.get("column_mapping")
    if not mapping:
        mapping = auto_detect_mapping(headers, entity_type)

    inserted = 0
    updated = 0
    skipped = 0
    all_errors: list[ImportErrorSchema] = []

    for idx, raw_row in enumerate(rows):
        row_num = idx + 2
        mapped = _map_row(raw_row, mapping)
        model, row_errors = _validate_row(mapped, entity_type, row_num)

        if row_errors:
            all_errors.extend(row_errors)
            skipped += 1
            continue

        try:
            was_insert = await _upsert_entity(db, tenant_id, user_id, entity_type, model)
            if was_insert:
                inserted += 1
            else:
                updated += 1
        except Exception as exc:
            logger.warning("Import upsert failed row %d: %s", row_num, exc)
            all_errors.append(ImportErrorSchema(
                row=row_num,
                column=None,
                message=f"Erreur lors de l'insertion: {exc}",
                value=None,
            ))
            skipped += 1

    await db.commit()

    total = len(rows)
    errors_json = [e.model_dump() for e in all_errors]

    # Update job status
    await db.execute(text("""
        UPDATE import_jobs
        SET status = 'applied',
            total_rows = :total,
            valid_rows = :valid,
            error_rows = :err_count,
            inserted_rows = :ins,
            updated_rows = :upd,
            skipped_rows = :skip,
            errors_json = CAST(:errs AS jsonb),
            updated_at = NOW()
        WHERE id = :id AND tenant_id = :tid
    """), {
        "id": job_id,
        "tid": str(tenant_id),
        "total": total,
        "valid": inserted + updated,
        "err_count": skipped,
        "ins": inserted,
        "upd": updated,
        "skip": skipped,
        "errs": json.dumps(errors_json, default=str),
    })
    await db.commit()

    return ApplyResult(
        job_id=job_id,
        entity_type=entity_type,
        total_rows=total,
        inserted_rows=inserted,
        updated_rows=updated,
        skipped_rows=skipped,
        error_rows=len(all_errors),
        errors=all_errors,
    )


async def _upsert_entity(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    entity_type: str,
    model: Any,
) -> bool:
    """Upsert a single entity row. Returns True if inserted, False if updated."""
    if entity_type == "driver":
        return await _upsert_driver(db, tenant_id, user_id, model)
    elif entity_type == "vehicle":
        return await _upsert_vehicle(db, tenant_id, user_id, model)
    elif entity_type == "client":
        return await _upsert_client(db, tenant_id, user_id, model)
    elif entity_type == "subcontractor":
        return await _upsert_subcontractor(db, tenant_id, user_id, model)
    else:
        raise ValueError(f"Type d'entite non supporte: {entity_type}")


async def _upsert_driver(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    model: DriverCreate,
) -> bool:
    """Upsert driver using ON CONFLICT on (tenant_id, matricule)."""
    matricule = model.matricule
    if not matricule:
        # Generate one if missing
        matricule = f"IMP-{uuid.uuid4().hex[:8].upper()}"

    did = uuid.uuid4()
    result = await db.execute(text("""
        INSERT INTO drivers (
            id, tenant_id, matricule, first_name, last_name,
            civilite, nom, prenom, date_naissance, lieu_naissance, nationalite, nir,
            adresse_ligne1, adresse_ligne2, code_postal, ville, pays, telephone_mobile,
            email, statut_emploi, type_contrat, date_entree, date_sortie, motif_sortie,
            poste, categorie_permis, coefficient, groupe, salaire_base_mensuel, taux_horaire,
            qualification_fimo, qualification_fco, qualification_adr, qualification_adr_classes,
            carte_conducteur_numero, permis_numero, site_affectation,
            agence_interim_nom, agence_interim_contact,
            carte_gazoil_ref, carte_gazoil_enseigne,
            email_personnel, notes, statut, created_by, updated_by,
            phone, license_number, license_categories, hire_date
        ) VALUES (
            :id, :tid, :mat, :fn, :ln,
            :civ, :nom, :prenom, :dob, :lieuN, :nat, :nir,
            :al1, :al2, :cp, :ville, :pays, :tm,
            :em, :se, :tc, :de, :ds, :ms,
            :poste, CAST(:cpermis AS jsonb), :coeff, :groupe, :sbm, :th,
            :fimo, :fco, :adr, CAST(:adr_classes AS jsonb),
            :ccn, :pn, :site,
            :ain, :aic,
            :cgr, :cge,
            :ep, :notes, 'ACTIF', :uid, :uid2,
            :ph, :lic, :cats, :hd
        )
        ON CONFLICT ON CONSTRAINT uq_drivers_tenant_matricule
        DO UPDATE SET
            civilite = EXCLUDED.civilite,
            nom = EXCLUDED.nom, prenom = EXCLUDED.prenom,
            date_naissance = EXCLUDED.date_naissance,
            lieu_naissance = EXCLUDED.lieu_naissance,
            nationalite = EXCLUDED.nationalite,
            nir = COALESCE(EXCLUDED.nir, drivers.nir),
            adresse_ligne1 = COALESCE(EXCLUDED.adresse_ligne1, drivers.adresse_ligne1),
            adresse_ligne2 = COALESCE(EXCLUDED.adresse_ligne2, drivers.adresse_ligne2),
            code_postal = COALESCE(EXCLUDED.code_postal, drivers.code_postal),
            ville = COALESCE(EXCLUDED.ville, drivers.ville),
            telephone_mobile = COALESCE(EXCLUDED.telephone_mobile, drivers.telephone_mobile),
            email = COALESCE(EXCLUDED.email, drivers.email),
            statut_emploi = EXCLUDED.statut_emploi,
            type_contrat = EXCLUDED.type_contrat,
            date_entree = COALESCE(EXCLUDED.date_entree, drivers.date_entree),
            date_sortie = COALESCE(EXCLUDED.date_sortie, drivers.date_sortie),
            poste = COALESCE(EXCLUDED.poste, drivers.poste),
            categorie_permis = COALESCE(EXCLUDED.categorie_permis, drivers.categorie_permis),
            qualification_fimo = EXCLUDED.qualification_fimo,
            qualification_fco = EXCLUDED.qualification_fco,
            qualification_adr = EXCLUDED.qualification_adr,
            site_affectation = COALESCE(EXCLUDED.site_affectation, drivers.site_affectation),
            notes = COALESCE(EXCLUDED.notes, drivers.notes),
            updated_by = EXCLUDED.updated_by,
            updated_at = NOW(),
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            phone = COALESCE(EXCLUDED.phone, drivers.phone)
        RETURNING (xmax = 0) AS was_insert
    """), {
        "id": str(did), "tid": str(tenant_id),
        "mat": matricule,
        "fn": model.first_name or model.prenom,
        "ln": model.last_name or model.nom,
        "civ": model.civilite, "nom": model.nom, "prenom": model.prenom,
        "dob": model.date_naissance, "lieuN": model.lieu_naissance, "nat": model.nationalite,
        "nir": model.nir,
        "al1": model.adresse_ligne1, "al2": model.adresse_ligne2,
        "cp": model.code_postal, "ville": model.ville, "pays": model.pays,
        "tm": model.telephone_mobile,
        "em": model.email,
        "se": model.statut_emploi, "tc": model.type_contrat,
        "de": model.date_entree, "ds": model.date_sortie, "ms": model.motif_sortie,
        "poste": model.poste,
        "cpermis": json.dumps(model.categorie_permis) if model.categorie_permis else None,
        "coeff": model.coefficient, "groupe": model.groupe,
        "sbm": model.salaire_base_mensuel, "th": model.taux_horaire,
        "fimo": model.qualification_fimo, "fco": model.qualification_fco,
        "adr": model.qualification_adr,
        "adr_classes": json.dumps(model.qualification_adr_classes) if model.qualification_adr_classes else None,
        "ccn": model.carte_conducteur_numero, "pn": model.permis_numero,
        "site": model.site_affectation,
        "ain": model.agence_interim_nom, "aic": model.agence_interim_contact,
        "cgr": model.carte_gazoil_ref, "cge": model.carte_gazoil_enseigne,
        "ep": model.email_personnel,
        "notes": model.notes,
        "uid": str(user_id), "uid2": str(user_id),
        "ph": model.phone or model.telephone_mobile,
        "lic": model.license_number, "cats": model.license_categories,
        "hd": model.hire_date or (str(model.date_entree) if model.date_entree else None),
    })
    row = result.first()
    return bool(row and row.was_insert)


async def _upsert_vehicle(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    model: VehicleCreate,
) -> bool:
    """Upsert vehicle using ON CONFLICT on (tenant_id, immatriculation)."""
    vid = uuid.uuid4()
    result = await db.execute(text("""
        INSERT INTO vehicles (
            id, tenant_id, plate_number, immatriculation, type_entity, categorie,
            marque, modele, annee_mise_en_circulation, date_premiere_immatriculation,
            vin, carrosserie, ptac_kg, ptra_kg, charge_utile_kg,
            volume_m3, longueur_utile_m, largeur_utile_m, hauteur_utile_m,
            nb_palettes_europe, nb_essieux, motorisation, norme_euro,
            proprietaire, loueur_nom, contrat_location_ref, date_fin_contrat_location,
            km_compteur_actuel, date_dernier_releve_km,
            nombre_places, mode_achat, valeur_assuree_ht, telematique,
            reference_client, date_entree_flotte, date_sortie_flotte,
            presence_matiere_dangereuse,
            assurance_compagnie, assurance_numero_police,
            controle_technique_date, limiteur_vitesse_date, tachygraphe_date,
            siren_proprietaire,
            statut, notes, created_by, updated_by,
            brand, model, vehicle_type, payload_kg, first_registration
        ) VALUES (
            :id, :tid, :plate, :immat, :te, :cat,
            :marque, :modele, :amc, :dpi,
            :vin, :carros, :ptac, :ptra, :cu,
            :vol, :longueur, :largeur, :hauteur,
            :npe, :nbe, :motor, :euro,
            :proprio, :loueur, :clref, :dfcl,
            :km, :ddrk,
            :npl, :machat, :vaht, :telem,
            :refcli, :def_, :dsf,
            :pmd,
            :assu_cie, :assu_police,
            :ct_date, :lv_date, :tachy_date,
            :siren_prop,
            'ACTIF', :notes, :uid, :uid2,
            :brand, :model_legacy, :vtype, :payload, :reg
        )
        ON CONFLICT ON CONSTRAINT uq_vehicles_tenant_immat
        DO UPDATE SET
            type_entity = EXCLUDED.type_entity,
            categorie = COALESCE(EXCLUDED.categorie, vehicles.categorie),
            marque = COALESCE(EXCLUDED.marque, vehicles.marque),
            modele = COALESCE(EXCLUDED.modele, vehicles.modele),
            annee_mise_en_circulation = COALESCE(EXCLUDED.annee_mise_en_circulation, vehicles.annee_mise_en_circulation),
            vin = COALESCE(EXCLUDED.vin, vehicles.vin),
            carrosserie = COALESCE(EXCLUDED.carrosserie, vehicles.carrosserie),
            ptac_kg = COALESCE(EXCLUDED.ptac_kg, vehicles.ptac_kg),
            ptra_kg = COALESCE(EXCLUDED.ptra_kg, vehicles.ptra_kg),
            charge_utile_kg = COALESCE(EXCLUDED.charge_utile_kg, vehicles.charge_utile_kg),
            motorisation = COALESCE(EXCLUDED.motorisation, vehicles.motorisation),
            norme_euro = COALESCE(EXCLUDED.norme_euro, vehicles.norme_euro),
            proprietaire = EXCLUDED.proprietaire,
            km_compteur_actuel = COALESCE(EXCLUDED.km_compteur_actuel, vehicles.km_compteur_actuel),
            assurance_compagnie = COALESCE(EXCLUDED.assurance_compagnie, vehicles.assurance_compagnie),
            notes = COALESCE(EXCLUDED.notes, vehicles.notes),
            updated_by = EXCLUDED.updated_by,
            updated_at = NOW(),
            plate_number = EXCLUDED.plate_number,
            brand = COALESCE(EXCLUDED.brand, vehicles.brand)
        RETURNING (xmax = 0) AS was_insert
    """), {
        "id": str(vid), "tid": str(tenant_id),
        "plate": model.immatriculation, "immat": model.immatriculation,
        "te": model.type_entity, "cat": model.categorie,
        "marque": model.marque, "modele": model.modele,
        "amc": model.annee_mise_en_circulation, "dpi": model.date_premiere_immatriculation,
        "vin": model.vin, "carros": model.carrosserie,
        "ptac": model.ptac_kg, "ptra": model.ptra_kg, "cu": model.charge_utile_kg,
        "vol": model.volume_m3, "longueur": model.longueur_utile_m,
        "largeur": model.largeur_utile_m, "hauteur": model.hauteur_utile_m,
        "npe": model.nb_palettes_europe, "nbe": model.nb_essieux,
        "motor": model.motorisation, "euro": model.norme_euro,
        "proprio": model.proprietaire, "loueur": model.loueur_nom,
        "clref": model.contrat_location_ref, "dfcl": model.date_fin_contrat_location,
        "km": model.km_compteur_actuel, "ddrk": model.date_dernier_releve_km,
        "npl": model.nombre_places, "machat": model.mode_achat,
        "vaht": model.valeur_assuree_ht, "telem": model.telematique,
        "refcli": model.reference_client, "def_": model.date_entree_flotte, "dsf": model.date_sortie_flotte,
        "pmd": model.presence_matiere_dangereuse,
        "assu_cie": model.assurance_compagnie, "assu_police": model.assurance_numero_police,
        "ct_date": model.controle_technique_date, "lv_date": model.limiteur_vitesse_date,
        "tachy_date": model.tachygraphe_date,
        "siren_prop": model.siren_proprietaire,
        "notes": model.notes,
        "uid": str(user_id), "uid2": str(user_id),
        "brand": model.brand or model.marque,
        "model_legacy": model.model or model.modele,
        "vtype": model.vehicle_type or model.type_entity,
        "payload": model.payload_kg or (float(model.charge_utile_kg) if model.charge_utile_kg else None),
        "reg": model.first_registration or (str(model.date_premiere_immatriculation) if model.date_premiere_immatriculation else None),
    })
    row = result.first()
    return bool(row and row.was_insert)


async def _upsert_client(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    model: ClientCreate,
) -> bool:
    """Upsert client using ON CONFLICT on (tenant_id, code)."""
    code = model.code
    if not code:
        # Auto-generate code
        code = f"CLI-{uuid.uuid4().hex[:8].upper()}"

    cid = uuid.uuid4()
    # Extract SIREN from SIRET
    siren = model.siret[:9] if model.siret and len(model.siret) >= 9 else None

    result = await db.execute(text("""
        INSERT INTO customers (
            id, tenant_id, name, siren, address, contact_email, contact_phone, payment_terms_days,
            code, raison_sociale, nom_commercial, siret, tva_intracom, code_naf,
            adresse_facturation_ligne1, adresse_facturation_ligne2,
            adresse_facturation_cp, adresse_facturation_ville, adresse_facturation_pays,
            telephone, email, site_web,
            delai_paiement_jours, mode_paiement, condition_paiement_texte,
            escompte_pourcent, penalite_retard_pourcent, indemnite_recouvrement,
            plafond_encours,
            notes, statut, date_debut_relation,
            created_by, updated_by
        ) VALUES (
            :id, :tid, :name, :siren, :addr, :ce, :cp, :pt,
            :code, :raison_sociale, :nom_commercial, :siret, :tva_intracom, :code_naf,
            :afl1, :afl2, :afcp, :afville, :afpays,
            :tel, :email, :site_web,
            :dpj, :mp, :cpt,
            :escompte, :penalite, :indemnite,
            :plafond,
            :notes, :statut, :ddr,
            :uid, :uid2
        )
        ON CONFLICT ON CONSTRAINT uq_customers_tenant_code
        DO UPDATE SET
            raison_sociale = EXCLUDED.raison_sociale,
            nom_commercial = COALESCE(EXCLUDED.nom_commercial, customers.nom_commercial),
            siret = COALESCE(EXCLUDED.siret, customers.siret),
            siren = COALESCE(EXCLUDED.siren, customers.siren),
            tva_intracom = COALESCE(EXCLUDED.tva_intracom, customers.tva_intracom),
            adresse_facturation_ligne1 = COALESCE(EXCLUDED.adresse_facturation_ligne1, customers.adresse_facturation_ligne1),
            adresse_facturation_cp = COALESCE(EXCLUDED.adresse_facturation_cp, customers.adresse_facturation_cp),
            adresse_facturation_ville = COALESCE(EXCLUDED.adresse_facturation_ville, customers.adresse_facturation_ville),
            telephone = COALESCE(EXCLUDED.telephone, customers.telephone),
            email = COALESCE(EXCLUDED.email, customers.email),
            delai_paiement_jours = EXCLUDED.delai_paiement_jours,
            mode_paiement = EXCLUDED.mode_paiement,
            notes = COALESCE(EXCLUDED.notes, customers.notes),
            name = EXCLUDED.name,
            updated_by = EXCLUDED.updated_by,
            updated_at = NOW()
        RETURNING (xmax = 0) AS was_insert
    """), {
        "id": str(cid), "tid": str(tenant_id),
        "name": model.raison_sociale, "siren": siren,
        "addr": model.adresse_facturation_ligne1,
        "ce": model.email, "cp": model.telephone,
        "pt": model.delai_paiement_jours,
        "code": code, "raison_sociale": model.raison_sociale,
        "nom_commercial": model.nom_commercial,
        "siret": model.siret, "tva_intracom": model.tva_intracom,
        "code_naf": model.code_naf,
        "afl1": model.adresse_facturation_ligne1, "afl2": model.adresse_facturation_ligne2,
        "afcp": model.adresse_facturation_cp, "afville": model.adresse_facturation_ville,
        "afpays": model.adresse_facturation_pays,
        "tel": model.telephone, "email": model.email, "site_web": model.site_web,
        "dpj": model.delai_paiement_jours, "mp": model.mode_paiement,
        "cpt": model.condition_paiement_texte,
        "escompte": model.escompte_pourcent, "penalite": model.penalite_retard_pourcent,
        "indemnite": model.indemnite_recouvrement,
        "plafond": model.plafond_encours,
        "notes": model.notes, "statut": model.statut,
        "ddr": model.date_debut_relation,
        "uid": str(user_id), "uid2": str(user_id),
    })
    row = result.first()
    return bool(row and row.was_insert)


async def _upsert_subcontractor(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    model: SubcontractorCreate,
) -> bool:
    """Upsert subcontractor using ON CONFLICT on (tenant_id, code)."""
    siren = model.siren or (model.siret[:9] if model.siret and len(model.siret) >= 9 else None)
    sid = uuid.uuid4()

    result = await db.execute(text("""
        INSERT INTO subcontractors (
            id, tenant_id, code, raison_sociale, siret, siren, tva_intracom, licence_transport,
            adresse_ligne1, adresse_ligne2, code_postal, ville, pays,
            telephone, email,
            contact_principal_nom, contact_principal_telephone, contact_principal_email,
            zones_geographiques, types_vehicules_disponibles, specialites,
            delai_paiement_jours, mode_paiement, rib_iban, rib_bic,
            statut, conformite_statut, note_qualite, notes,
            created_by, updated_by
        ) VALUES (
            :id, :tid, :code, :rs, :siret, :siren, :tva, :licence,
            :al1, :al2, :cp, :ville, :pays,
            :tel, :email,
            :cpn, :cpt, :cpe,
            CAST(:zones AS jsonb), CAST(:types_veh AS jsonb), CAST(:spec AS jsonb),
            :dpj, :mp, :iban, :bic,
            :statut, :conf, :note_q, :notes,
            :uid, :uid2
        )
        ON CONFLICT ON CONSTRAINT uq_subcontractors_tenant_code
        DO UPDATE SET
            raison_sociale = EXCLUDED.raison_sociale,
            siret = EXCLUDED.siret,
            siren = COALESCE(EXCLUDED.siren, subcontractors.siren),
            tva_intracom = COALESCE(EXCLUDED.tva_intracom, subcontractors.tva_intracom),
            adresse_ligne1 = EXCLUDED.adresse_ligne1,
            code_postal = EXCLUDED.code_postal,
            ville = EXCLUDED.ville,
            telephone = COALESCE(EXCLUDED.telephone, subcontractors.telephone),
            email = EXCLUDED.email,
            contact_principal_nom = COALESCE(EXCLUDED.contact_principal_nom, subcontractors.contact_principal_nom),
            notes = COALESCE(EXCLUDED.notes, subcontractors.notes),
            updated_by = EXCLUDED.updated_by,
            updated_at = NOW()
        RETURNING (xmax = 0) AS was_insert
    """), {
        "id": str(sid), "tid": str(tenant_id),
        "code": model.code, "rs": model.raison_sociale,
        "siret": model.siret, "siren": siren, "tva": model.tva_intracom,
        "licence": model.licence_transport,
        "al1": model.adresse_ligne1, "al2": model.adresse_ligne2,
        "cp": model.code_postal, "ville": model.ville, "pays": model.pays,
        "tel": model.telephone, "email": model.email,
        "cpn": model.contact_principal_nom, "cpt": model.contact_principal_telephone,
        "cpe": model.contact_principal_email,
        "zones": json.dumps(model.zones_geographiques) if model.zones_geographiques else None,
        "types_veh": json.dumps(model.types_vehicules_disponibles) if model.types_vehicules_disponibles else None,
        "spec": json.dumps(model.specialites) if model.specialites else None,
        "dpj": model.delai_paiement_jours, "mp": model.mode_paiement,
        "iban": model.rib_iban, "bic": model.rib_bic,
        "statut": model.statut, "conf": model.conformite_statut, "note_q": model.note_qualite,
        "notes": model.notes,
        "uid": str(user_id), "uid2": str(user_id),
    })
    row = result.first()
    return bool(row and row.was_insert)


def generate_errors_csv(errors_json: list[dict[str, Any]]) -> bytes:
    """Generate a CSV file from error data.

    Returns UTF-8-BOM encoded bytes.
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Ligne", "Colonne", "Message", "Valeur"])

    for err in errors_json:
        writer.writerow([
            err.get("row", ""),
            err.get("column", ""),
            err.get("message", ""),
            err.get("value", ""),
        ])

    return output.getvalue().encode("utf-8-sig")
