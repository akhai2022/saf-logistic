"""Column mapping definitions and auto-detection for each entity type.

Maps French CSV header names (lowercased) to the Pydantic schema field names
used in DriverCreate, VehicleCreate, ClientCreate, SubcontractorCreate.
"""
from __future__ import annotations

from difflib import SequenceMatcher

# ══════════════════════════════════════════════════════════════════
# DRIVER FIELD MAP
# ══════════════════════════════════════════════════════════════════

DRIVER_FIELD_MAP: dict[str, str] = {
    # Core identity
    "matricule": "matricule",
    "n\u00b0 matricule": "matricule",
    "num\u00e9ro matricule": "matricule",
    "civilit\u00e9": "civilite",
    "civilite": "civilite",
    "nom": "nom",
    "nom de famille": "nom",
    "pr\u00e9nom": "prenom",
    "prenom": "prenom",
    "date de naissance": "date_naissance",
    "date naissance": "date_naissance",
    "n\u00e9 le": "date_naissance",
    "lieu de naissance": "lieu_naissance",
    "nationalit\u00e9": "nationalite",
    "nationalite": "nationalite",
    # Social security
    "nir": "nir",
    "n\u00b0 s\u00e9curit\u00e9 sociale": "nir",
    "num\u00e9ro s\u00e9curit\u00e9 sociale": "nir",
    "s\u00e9curit\u00e9 sociale": "nir",
    # Address
    "adresse": "adresse_ligne1",
    "adresse ligne 1": "adresse_ligne1",
    "adresse ligne 2": "adresse_ligne2",
    "code postal": "code_postal",
    "cp": "code_postal",
    "ville": "ville",
    "pays": "pays",
    # Contact
    "t\u00e9l\u00e9phone": "telephone_mobile",
    "telephone": "telephone_mobile",
    "t\u00e9l\u00e9phone mobile": "telephone_mobile",
    "tel mobile": "telephone_mobile",
    "portable": "telephone_mobile",
    "email": "email",
    "e-mail": "email",
    "email personnel": "email_personnel",
    # Employment
    "statut emploi": "statut_emploi",
    "type contrat": "type_contrat",
    "type de contrat": "type_contrat",
    "date d'entr\u00e9e": "date_entree",
    "date entr\u00e9e": "date_entree",
    "date entree": "date_entree",
    "date de sortie": "date_sortie",
    "date sortie": "date_sortie",
    "motif sortie": "motif_sortie",
    "motif de sortie": "motif_sortie",
    "poste": "poste",
    # Driving
    "cat\u00e9gorie permis": "categorie_permis",
    "categorie permis": "categorie_permis",
    "permis": "categorie_permis",
    "n\u00b0 permis": "permis_numero",
    "num\u00e9ro permis": "permis_numero",
    "numero permis": "permis_numero",
    "carte conducteur": "carte_conducteur_numero",
    "n\u00b0 carte conducteur": "carte_conducteur_numero",
    # Qualifications
    "fimo": "qualification_fimo",
    "fco": "qualification_fco",
    "adr": "qualification_adr",
    # Pay
    "coefficient": "coefficient",
    "groupe": "groupe",
    "salaire base": "salaire_base_mensuel",
    "salaire de base": "salaire_base_mensuel",
    "taux horaire": "taux_horaire",
    # Other
    "site affectation": "site_affectation",
    "agence int\u00e9rim": "agence_interim_nom",
    "agence interim": "agence_interim_nom",
    "carte gasoil r\u00e9f": "carte_gazoil_ref",
    "carte gazoil ref": "carte_gazoil_ref",
    "carte gazoil enseigne": "carte_gazoil_enseigne",
    "notes": "notes",
}

DRIVER_REQUIRED_FIELDS = {"nom", "prenom"}

# ══════════════════════════════════════════════════════════════════
# VEHICLE FIELD MAP
# ══════════════════════════════════════════════════════════════════

VEHICLE_FIELD_MAP: dict[str, str] = {
    "immatriculation": "immatriculation",
    "plaque": "immatriculation",
    "n\u00b0 immatriculation": "immatriculation",
    "type entit\u00e9": "type_entity",
    "type entite": "type_entity",
    "type": "type_entity",
    "cat\u00e9gorie": "categorie",
    "categorie": "categorie",
    "marque": "marque",
    "mod\u00e8le": "modele",
    "modele": "modele",
    "ann\u00e9e mise en circulation": "annee_mise_en_circulation",
    "annee mise en circulation": "annee_mise_en_circulation",
    "ann\u00e9e": "annee_mise_en_circulation",
    "date premi\u00e8re immatriculation": "date_premiere_immatriculation",
    "date 1\u00e8re immatriculation": "date_premiere_immatriculation",
    "vin": "vin",
    "n\u00b0 vin": "vin",
    "carrosserie": "carrosserie",
    "ptac": "ptac_kg",
    "ptac kg": "ptac_kg",
    "ptac (kg)": "ptac_kg",
    "ptra": "ptra_kg",
    "ptra kg": "ptra_kg",
    "charge utile": "charge_utile_kg",
    "charge utile kg": "charge_utile_kg",
    "charge utile (kg)": "charge_utile_kg",
    "volume": "volume_m3",
    "volume m3": "volume_m3",
    "volume (m3)": "volume_m3",
    "nb palettes": "nb_palettes_europe",
    "nb palettes europe": "nb_palettes_europe",
    "nb essieux": "nb_essieux",
    "motorisation": "motorisation",
    "norme euro": "norme_euro",
    "euro": "norme_euro",
    "propri\u00e9taire": "proprietaire",
    "proprietaire": "proprietaire",
    "loueur": "loueur_nom",
    "loueur nom": "loueur_nom",
    "km compteur": "km_compteur_actuel",
    "kilom\u00e9trage": "km_compteur_actuel",
    "km": "km_compteur_actuel",
    "assurance compagnie": "assurance_compagnie",
    "assurance n\u00b0 police": "assurance_numero_police",
    "contr\u00f4le technique date": "controle_technique_date",
    "controle technique date": "controle_technique_date",
    "notes": "notes",
}

VEHICLE_REQUIRED_FIELDS = {"immatriculation"}

# ══════════════════════════════════════════════════════════════════
# CLIENT FIELD MAP
# ══════════════════════════════════════════════════════════════════

CLIENT_FIELD_MAP: dict[str, str] = {
    "code": "code",
    "code client": "code",
    "raison sociale": "raison_sociale",
    "nom commercial": "nom_commercial",
    "siret": "siret",
    "tva intracommunautaire": "tva_intracom",
    "tva intracom": "tva_intracom",
    "code naf": "code_naf",
    "adresse facturation": "adresse_facturation_ligne1",
    "adresse facturation ligne 1": "adresse_facturation_ligne1",
    "adresse facturation ligne 2": "adresse_facturation_ligne2",
    "cp facturation": "adresse_facturation_cp",
    "code postal facturation": "adresse_facturation_cp",
    "ville facturation": "adresse_facturation_ville",
    "t\u00e9l\u00e9phone": "telephone",
    "telephone": "telephone",
    "email": "email",
    "site web": "site_web",
    "d\u00e9lai paiement": "delai_paiement_jours",
    "delai paiement jours": "delai_paiement_jours",
    "mode paiement": "mode_paiement",
    "notes": "notes",
    "statut": "statut",
}

CLIENT_REQUIRED_FIELDS = {"raison_sociale"}

# ══════════════════════════════════════════════════════════════════
# SUBCONTRACTOR FIELD MAP
# ══════════════════════════════════════════════════════════════════

SUBCONTRACTOR_FIELD_MAP: dict[str, str] = {
    "code": "code",
    "code sous-traitant": "code",
    "raison sociale": "raison_sociale",
    "siret": "siret",
    "tva intracommunautaire": "tva_intracom",
    "tva intracom": "tva_intracom",
    "licence transport": "licence_transport",
    "adresse": "adresse_ligne1",
    "adresse ligne 1": "adresse_ligne1",
    "adresse ligne 2": "adresse_ligne2",
    "code postal": "code_postal",
    "cp": "code_postal",
    "ville": "ville",
    "pays": "pays",
    "t\u00e9l\u00e9phone": "telephone",
    "telephone": "telephone",
    "email": "email",
    "contact nom": "contact_principal_nom",
    "contact t\u00e9l\u00e9phone": "contact_principal_telephone",
    "contact email": "contact_principal_email",
    "d\u00e9lai paiement": "delai_paiement_jours",
    "delai paiement jours": "delai_paiement_jours",
    "mode paiement": "mode_paiement",
    "iban": "rib_iban",
    "bic": "rib_bic",
    "notes": "notes",
    "statut": "statut",
}

SUBCONTRACTOR_REQUIRED_FIELDS = {"code", "raison_sociale", "siret", "adresse_ligne1", "code_postal", "ville", "email"}


# ══════════════════════════════════════════════════════════════════
# ENTITY REGISTRY
# ══════════════════════════════════════════════════════════════════

ENTITY_FIELD_MAPS: dict[str, dict[str, str]] = {
    "driver": DRIVER_FIELD_MAP,
    "vehicle": VEHICLE_FIELD_MAP,
    "client": CLIENT_FIELD_MAP,
    "subcontractor": SUBCONTRACTOR_FIELD_MAP,
}

ENTITY_REQUIRED_FIELDS: dict[str, set[str]] = {
    "driver": DRIVER_REQUIRED_FIELDS,
    "vehicle": VEHICLE_REQUIRED_FIELDS,
    "client": CLIENT_REQUIRED_FIELDS,
    "subcontractor": SUBCONTRACTOR_REQUIRED_FIELDS,
}

VALID_ENTITY_TYPES = set(ENTITY_FIELD_MAPS.keys())


def auto_detect_mapping(headers: list[str], entity_type: str) -> dict[str, str]:
    """Build a mapping from CSV header -> schema field name.

    First tries exact lowercase match against the entity field map.
    Falls back to fuzzy matching for headers that did not match exactly.

    Returns:
        dict mapping each CSV header to a schema field name (only for matched headers).
    """
    field_map = ENTITY_FIELD_MAPS.get(entity_type, {})
    if not field_map:
        raise ValueError(f"Type d'entite inconnu: {entity_type}")

    mapping: dict[str, str] = {}
    used_fields: set[str] = set()

    # Pass 1: exact match (case-insensitive)
    for header in headers:
        normalised = header.strip().lower()
        if normalised in field_map:
            target = field_map[normalised]
            if target not in used_fields:
                mapping[header] = target
                used_fields.add(target)

    # Pass 2: fuzzy match for remaining headers
    unmatched_headers = [h for h in headers if h not in mapping]
    available_keys = [k for k, v in field_map.items() if v not in used_fields]

    for header in unmatched_headers:
        normalised = header.strip().lower()
        best_ratio = 0.0
        best_key = None
        for key in available_keys:
            ratio = SequenceMatcher(None, normalised, key).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_key = key
        if best_key and best_ratio >= 0.8:
            target = field_map[best_key]
            if target not in used_fields:
                mapping[header] = target
                used_fields.add(target)
                available_keys.remove(best_key)

    return mapping
