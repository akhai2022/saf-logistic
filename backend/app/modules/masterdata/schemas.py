"""Pydantic v2 schemas for Module B — Referentiels Metier."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.validators import (
    validate_french_plate,
    validate_nir,
    validate_siret,
    validate_tva_intracom,
    validate_vin,
)

# ── Enums as literals ──────────────────────────────────────────────

CLIENT_STATUTS = {"ACTIF", "INACTIF", "PROSPECT", "BLOQUE"}
MODES_PAIEMENT = {"VIREMENT", "CHEQUE", "PRELEVEMENT", "LCR", "TRAITE"}
SUB_STATUTS = {"ACTIF", "INACTIF", "EN_COURS_VALIDATION", "BLOQUE", "SUSPENDU"}
CONTRACT_STATUTS = {"BROUILLON", "ACTIF", "EXPIRE", "RESILIE"}
TYPES_PRESTATION = {"LOT_COMPLET", "MESSAGERIE", "AFFRETEMENT", "DEMENAGEMENT"}
DRIVER_STATUTS = {"ACTIF", "INACTIF", "SUSPENDU"}
STATUTS_EMPLOI = {"SALARIE", "INTERIMAIRE"}
TYPES_CONTRAT = {"CDI", "CDD", "INTERIM", "APPRENTISSAGE"}
MOTIFS_SORTIE = {"DEMISSION", "LICENCIEMENT", "FIN_CDD", "RUPTURE_CONV", "RETRAITE", "AUTRE"}
VEHICLE_STATUTS = {"ACTIF", "INACTIF", "EN_MAINTENANCE", "IMMOBILISE", "VENDU", "RESTITUE"}
TYPES_ENTITY_VEHICLE = {"VEHICULE", "REMORQUE", "SEMI_REMORQUE"}
CATEGORIES_VEHICLE = {"VL", "PL_3_5T_19T", "PL_PLUS_19T", "SPL", "REMORQUE", "SEMI_REMORQUE", "TRACTEUR"}
CARROSSERIES = {"BACHE", "FOURGON", "FRIGORIFIQUE", "PLATEAU", "CITERNE", "BENNE", "PORTE_CONTENEUR", "SAVOYARDE", "AUTRE"}
MOTORISATIONS = {"DIESEL", "GNL", "GNC", "ELECTRIQUE", "HYDROGENE", "HYBRIDE"}
NORMES_EURO = {"EURO_3", "EURO_4", "EURO_5", "EURO_6", "EURO_6D", "EURO_7"}
PROPRIETAIRE_TYPES = {"PROPRE", "LOCATION_LONGUE_DUREE", "CREDIT_BAIL", "LOCATION_COURTE"}
ADDRESS_TYPES = {"LIVRAISON", "CHARGEMENT", "MIXTE"}
CONFORMITE_STATUTS = {"OK", "A_REGULARISER", "BLOQUANT"}
CIVILITES = {"M", "MME"}


# ══════════════════════════════════════════════════════════════════
# CLIENT
# ══════════════════════════════════════════════════════════════════

class ClientContactCreate(BaseModel):
    civilite: str | None = None
    nom: str
    prenom: str
    fonction: str | None = None
    email: str | None = None
    telephone_fixe: str | None = None
    telephone_mobile: str | None = None
    is_contact_principal: bool = False
    is_contact_facturation: bool = False
    is_contact_exploitation: bool = False
    notes: str | None = None
    is_active: bool = True

    @field_validator("civilite")
    @classmethod
    def check_civilite(cls, v: str | None) -> str | None:
        if v is not None and v not in CIVILITES:
            raise ValueError(f"Civilite invalide. Valeurs acceptees: {', '.join(sorted(CIVILITES))}")
        return v


class ClientContactOut(ClientContactCreate):
    id: str
    client_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ClientAddressCreate(BaseModel):
    libelle: str
    type: str
    adresse_ligne1: str
    adresse_ligne2: str | None = None
    code_postal: str
    ville: str
    pays: str = "FR"
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    contact_site_nom: str | None = None
    contact_site_telephone: str | None = None
    horaires_ouverture: str | None = None
    instructions_acces: str | None = None
    contraintes: dict[str, Any] | None = None
    is_active: bool = True

    @field_validator("type")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in ADDRESS_TYPES:
            raise ValueError(f"Type invalide. Valeurs acceptees: {', '.join(sorted(ADDRESS_TYPES))}")
        return v


class ClientAddressOut(ClientAddressCreate):
    id: str
    client_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ClientCreate(BaseModel):
    code: str | None = None
    raison_sociale: str
    nom_commercial: str | None = None
    siret: str | None = None
    tva_intracom: str | None = None
    code_naf: str | None = None
    adresse_facturation_ligne1: str | None = None
    adresse_facturation_ligne2: str | None = None
    adresse_facturation_cp: str | None = None
    adresse_facturation_ville: str | None = None
    adresse_facturation_pays: str = "FR"
    telephone: str | None = None
    email: str | None = None
    site_web: str | None = None
    delai_paiement_jours: int = 30
    mode_paiement: str = "VIREMENT"
    condition_paiement_texte: str | None = None
    escompte_pourcent: Decimal | None = None
    penalite_retard_pourcent: Decimal | None = None
    indemnite_recouvrement: Decimal | None = None
    plafond_encours: Decimal | None = None
    sla_delai_livraison_heures: int | None = None
    sla_taux_service_pourcent: Decimal | None = None
    sla_penalite_texte: str | None = None
    agency_ids: list[str] | None = None
    notes: str | None = None
    statut: str = "PROSPECT"
    date_debut_relation: date | None = None

    @field_validator("siret")
    @classmethod
    def check_siret(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            v = v.strip()
            if not validate_siret(v):
                raise ValueError("Le SIRET client est invalide.")  # RG-B-002
        return v

    @field_validator("tva_intracom")
    @classmethod
    def check_tva(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            if not validate_tva_intracom(v):
                raise ValueError("Le numero de TVA intracommunautaire est invalide.")
        return v

    @field_validator("mode_paiement")
    @classmethod
    def check_mode_paiement(cls, v: str) -> str:
        if v not in MODES_PAIEMENT:
            raise ValueError(f"Mode de paiement invalide. Valeurs acceptees: {', '.join(sorted(MODES_PAIEMENT))}")
        return v

    @field_validator("statut")
    @classmethod
    def check_statut(cls, v: str) -> str:
        if v not in CLIENT_STATUTS:
            raise ValueError(f"Statut invalide. Valeurs acceptees: {', '.join(sorted(CLIENT_STATUTS))}")
        return v

    @model_validator(mode="after")
    def check_business_rules(self) -> "ClientCreate":
        # RG-B-003: delai paiement max 60 jours
        if self.delai_paiement_jours > 60:
            raise ValueError(
                "Le delai de paiement depasse le maximum legal (60 jours nets ou 45 jours fin de mois)."
            )
        # RG-B-004: indemnite recouvrement >= 40 EUR
        if self.indemnite_recouvrement is not None and self.indemnite_recouvrement < 40:
            raise ValueError(
                "L'indemnite de recouvrement ne peut etre inferieure a 40 EUR."
            )
        return self


class ClientUpdate(ClientCreate):
    pass


class ClientOut(BaseModel):
    id: str
    code: str | None = None
    raison_sociale: str | None = None
    nom_commercial: str | None = None
    siret: str | None = None
    siren: str | None = None
    tva_intracom: str | None = None
    code_naf: str | None = None
    adresse_facturation_ligne1: str | None = None
    adresse_facturation_ligne2: str | None = None
    adresse_facturation_cp: str | None = None
    adresse_facturation_ville: str | None = None
    adresse_facturation_pays: str | None = None
    telephone: str | None = None
    email: str | None = None
    site_web: str | None = None
    delai_paiement_jours: int | None = None
    mode_paiement: str | None = None
    condition_paiement_texte: str | None = None
    escompte_pourcent: Decimal | None = None
    penalite_retard_pourcent: Decimal | None = None
    indemnite_recouvrement: Decimal | None = None
    plafond_encours: Decimal | None = None
    statut: str | None = None
    notes: str | None = None
    date_debut_relation: date | None = None
    agency_ids: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Legacy compat
    name: str | None = None
    is_active: bool = True


class ClientDetail(ClientOut):
    contacts: list[ClientContactOut] = []
    addresses: list[ClientAddressOut] = []


# ══════════════════════════════════════════════════════════════════
# SUBCONTRACTOR
# ══════════════════════════════════════════════════════════════════

class SubcontractorContractCreate(BaseModel):
    reference: str
    type_prestation: str
    date_debut: date
    date_fin: date | None = None
    tacite_reconduction: bool = False
    preavis_resiliation_jours: int | None = None
    document_s3_key: str | None = None
    tarification: dict[str, Any] | None = None
    statut: str = "BROUILLON"
    notes: str | None = None

    @field_validator("type_prestation")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in TYPES_PRESTATION:
            raise ValueError(f"Type de prestation invalide. Valeurs acceptees: {', '.join(sorted(TYPES_PRESTATION))}")
        return v

    @field_validator("statut")
    @classmethod
    def check_statut(cls, v: str) -> str:
        if v not in CONTRACT_STATUTS:
            raise ValueError(f"Statut invalide. Valeurs acceptees: {', '.join(sorted(CONTRACT_STATUTS))}")
        return v


class SubcontractorContractOut(SubcontractorContractCreate):
    id: str
    subcontractor_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SubcontractorCreate(BaseModel):
    code: str
    raison_sociale: str
    siret: str
    siren: str | None = None
    tva_intracom: str | None = None
    licence_transport: str | None = None
    adresse_ligne1: str
    adresse_ligne2: str | None = None
    code_postal: str
    ville: str
    pays: str = "FR"
    telephone: str | None = None
    email: str
    contact_principal_nom: str | None = None
    contact_principal_telephone: str | None = None
    contact_principal_email: str | None = None
    zones_geographiques: list[str] | None = None
    types_vehicules_disponibles: list[str] | None = None
    specialites: list[str] | None = None
    delai_paiement_jours: int = 45
    mode_paiement: str = "VIREMENT"
    rib_iban: str | None = None
    rib_bic: str | None = None
    statut: str = "EN_COURS_VALIDATION"
    conformite_statut: str = "A_REGULARISER"
    note_qualite: Decimal | None = None
    agency_ids: list[str] | None = None
    notes: str | None = None

    @field_validator("siret")
    @classmethod
    def check_siret(cls, v: str) -> str:
        # RG-B-010: SIRET obligatoire et valide
        v = v.strip()
        if not v:
            raise ValueError("Le SIRET est obligatoire pour un sous-traitant.")
        if not validate_siret(v):
            raise ValueError("Le SIRET du sous-traitant est invalide.")
        return v

    @field_validator("tva_intracom")
    @classmethod
    def check_tva(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            if not validate_tva_intracom(v):
                raise ValueError("Le numero de TVA intracommunautaire est invalide.")
        return v

    @field_validator("statut")
    @classmethod
    def check_statut(cls, v: str) -> str:
        if v not in SUB_STATUTS:
            raise ValueError(f"Statut invalide. Valeurs acceptees: {', '.join(sorted(SUB_STATUTS))}")
        return v

    @field_validator("mode_paiement")
    @classmethod
    def check_mode_paiement(cls, v: str) -> str:
        if v not in MODES_PAIEMENT:
            raise ValueError(f"Mode de paiement invalide. Valeurs acceptees: {', '.join(sorted(MODES_PAIEMENT))}")
        return v


class SubcontractorUpdate(SubcontractorCreate):
    pass


class SubcontractorOut(BaseModel):
    id: str
    code: str
    raison_sociale: str
    siret: str
    siren: str | None = None
    tva_intracom: str | None = None
    licence_transport: str | None = None
    adresse_ligne1: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    pays: str | None = None
    telephone: str | None = None
    email: str | None = None
    contact_principal_nom: str | None = None
    zones_geographiques: list[str] | None = None
    types_vehicules_disponibles: list[str] | None = None
    specialites: list[str] | None = None
    delai_paiement_jours: int | None = None
    mode_paiement: str | None = None
    statut: str | None = None
    conformite_statut: str | None = None
    note_qualite: Decimal | None = None
    agency_ids: list[str] | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SubcontractorDetail(SubcontractorOut):
    adresse_ligne2: str | None = None
    contact_principal_telephone: str | None = None
    contact_principal_email: str | None = None
    rib_iban: str | None = None
    rib_bic: str | None = None
    contracts: list[SubcontractorContractOut] = []


# ══════════════════════════════════════════════════════════════════
# DRIVER
# ══════════════════════════════════════════════════════════════════

class DriverCreate(BaseModel):
    matricule: str | None = None
    civilite: str | None = None
    nom: str
    prenom: str
    date_naissance: date | None = None
    lieu_naissance: str | None = None
    nationalite: str | None = None
    nir: str | None = None
    adresse_ligne1: str | None = None
    adresse_ligne2: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    pays: str = "FR"
    telephone_mobile: str | None = None
    email: str | None = None
    statut_emploi: str = "SALARIE"
    agence_interim_nom: str | None = None
    agence_interim_contact: str | None = None
    type_contrat: str = "CDI"
    date_entree: date | None = None
    date_sortie: date | None = None
    motif_sortie: str | None = None
    poste: str | None = None
    categorie_permis: list[str] | None = None
    coefficient: str | None = None
    groupe: str | None = None
    salaire_base_mensuel: Decimal | None = None
    taux_horaire: Decimal | None = None
    qualification_fimo: bool = False
    qualification_fco: bool = False
    qualification_adr: bool = False
    qualification_adr_classes: list[str] | None = None
    carte_conducteur_numero: str | None = None
    # New fields (migration 0010)
    carte_gazoil_ref: str | None = None
    carte_gazoil_enseigne: str | None = None
    medecine_travail_dernier_rdv: date | None = None
    medecine_travail_prochain_rdv: date | None = None
    site_affectation: str | None = None
    licence_intracom_numero: str | None = None
    email_personnel: str | None = None
    permis_numero: str | None = None
    agency_id: str | None = None
    notes: str | None = None
    # Legacy compat
    first_name: str | None = None
    last_name: str | None = None
    license_number: str | None = None
    license_categories: str | None = None
    phone: str | None = None
    hire_date: str | None = None

    @field_validator("nir")
    @classmethod
    def check_nir(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            v = v.strip()
            if not validate_nir(v):
                raise ValueError("Le numero de securite sociale est invalide.")  # RG-B-020
        return v

    @field_validator("civilite")
    @classmethod
    def check_civilite(cls, v: str | None) -> str | None:
        if v is not None and v not in CIVILITES:
            raise ValueError(f"Civilite invalide. Valeurs acceptees: {', '.join(sorted(CIVILITES))}")
        return v

    @field_validator("statut_emploi")
    @classmethod
    def check_statut_emploi(cls, v: str) -> str:
        if v not in STATUTS_EMPLOI:
            raise ValueError(f"Statut emploi invalide. Valeurs acceptees: {', '.join(sorted(STATUTS_EMPLOI))}")
        return v

    @field_validator("type_contrat")
    @classmethod
    def check_type_contrat(cls, v: str) -> str:
        if v not in TYPES_CONTRAT:
            raise ValueError(f"Type contrat invalide. Valeurs acceptees: {', '.join(sorted(TYPES_CONTRAT))}")
        return v

    @field_validator("motif_sortie")
    @classmethod
    def check_motif_sortie(cls, v: str | None) -> str | None:
        if v is not None and v not in MOTIFS_SORTIE:
            raise ValueError(f"Motif sortie invalide. Valeurs acceptees: {', '.join(sorted(MOTIFS_SORTIE))}")
        return v

    @model_validator(mode="after")
    def check_business_rules(self) -> "DriverCreate":
        # RG-B-022: interimaire requires agence_interim_nom
        if self.statut_emploi == "INTERIMAIRE" and not self.agence_interim_nom:
            raise ValueError(
                "Le nom de l'agence d'interim est obligatoire pour un conducteur interimaire."
            )
        # RG-B-025: date_sortie >= date_entree
        if self.date_sortie and self.date_entree and self.date_sortie < self.date_entree:
            raise ValueError(
                "La date de sortie ne peut pas etre anterieure a la date d'entree."
            )
        return self


class DriverUpdate(DriverCreate):
    pass


class DriverOut(BaseModel):
    id: str
    matricule: str | None = None
    civilite: str | None = None
    nom: str | None = None
    prenom: str | None = None
    date_naissance: date | None = None
    telephone_mobile: str | None = None
    email: str | None = None
    statut_emploi: str | None = None
    type_contrat: str | None = None
    date_entree: date | None = None
    date_sortie: date | None = None
    poste: str | None = None
    categorie_permis: list[str] | None = None
    qualification_fimo: bool | None = None
    qualification_fco: bool | None = None
    qualification_adr: bool | None = None
    conformite_statut: str | None = None
    statut: str | None = None
    site_affectation: str | None = None
    agency_id: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Legacy compat
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    is_active: bool = True


class DriverDetail(DriverOut):
    lieu_naissance: str | None = None
    nationalite: str | None = None
    nir: str | None = None
    adresse_ligne1: str | None = None
    adresse_ligne2: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    pays: str | None = None
    agence_interim_nom: str | None = None
    agence_interim_contact: str | None = None
    motif_sortie: str | None = None
    coefficient: str | None = None
    groupe: str | None = None
    salaire_base_mensuel: Decimal | None = None
    taux_horaire: Decimal | None = None
    qualification_adr_classes: list[str] | None = None
    carte_conducteur_numero: str | None = None
    photo_s3_key: str | None = None
    # New fields (migration 0010)
    carte_gazoil_ref: str | None = None
    carte_gazoil_enseigne: str | None = None
    medecine_travail_dernier_rdv: date | None = None
    medecine_travail_prochain_rdv: date | None = None
    licence_intracom_numero: str | None = None
    email_personnel: str | None = None
    permis_numero: str | None = None


# ══════════════════════════════════════════════════════════════════
# VEHICLE
# ══════════════════════════════════════════════════════════════════

class VehicleCreate(BaseModel):
    immatriculation: str
    type_entity: str = "VEHICULE"
    categorie: str | None = None
    marque: str | None = None
    modele: str | None = None
    annee_mise_en_circulation: int | None = None
    date_premiere_immatriculation: date | None = None
    vin: str | None = None
    carrosserie: str | None = None
    ptac_kg: int | None = None
    ptra_kg: int | None = None
    charge_utile_kg: int | None = None
    volume_m3: Decimal | None = None
    longueur_utile_m: Decimal | None = None
    largeur_utile_m: Decimal | None = None
    hauteur_utile_m: Decimal | None = None
    nb_palettes_europe: int | None = None
    nb_essieux: int | None = None
    motorisation: str | None = None
    norme_euro: str | None = None
    equipements: dict[str, Any] | None = None
    temperature_min: Decimal | None = None
    temperature_max: Decimal | None = None
    proprietaire: str = "PROPRE"
    loueur_nom: str | None = None
    contrat_location_ref: str | None = None
    date_fin_contrat_location: date | None = None
    km_compteur_actuel: int | None = None
    date_dernier_releve_km: date | None = None
    # New fields (migration 0010)
    nombre_places: int | None = None
    mode_achat: str | None = None
    valeur_assuree_ht: Decimal | None = None
    telematique: bool = False
    reference_client: str | None = None
    date_entree_flotte: date | None = None
    date_sortie_flotte: date | None = None
    presence_matiere_dangereuse: bool = False
    assurance_compagnie: str | None = None
    assurance_numero_police: str | None = None
    controle_technique_date: date | None = None
    limiteur_vitesse_date: date | None = None
    tachygraphe_date: date | None = None
    siren_proprietaire: str | None = None
    agency_id: str | None = None
    notes: str | None = None
    # Legacy compat
    plate_number: str | None = None
    brand: str | None = None
    model: str | None = None
    vehicle_type: str | None = None
    payload_kg: float | None = None
    first_registration: str | None = None

    @field_validator("immatriculation")
    @classmethod
    def check_plate(cls, v: str) -> str:
        v = v.strip().upper()
        if not validate_french_plate(v):
            raise ValueError("Format de plaque invalide.")  # RG-B-031
        return v

    @field_validator("vin")
    @classmethod
    def check_vin(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            v = v.strip().upper()
            if not validate_vin(v):
                raise ValueError("Le numero VIN est invalide.")  # RG-B-032
        return v

    @field_validator("type_entity")
    @classmethod
    def check_type_entity(cls, v: str) -> str:
        if v not in TYPES_ENTITY_VEHICLE:
            raise ValueError(f"Type entite invalide. Valeurs acceptees: {', '.join(sorted(TYPES_ENTITY_VEHICLE))}")
        return v

    @field_validator("categorie")
    @classmethod
    def check_categorie(cls, v: str | None) -> str | None:
        if v is not None and v not in CATEGORIES_VEHICLE:
            raise ValueError(f"Categorie invalide. Valeurs acceptees: {', '.join(sorted(CATEGORIES_VEHICLE))}")
        return v

    @field_validator("carrosserie")
    @classmethod
    def check_carrosserie(cls, v: str | None) -> str | None:
        if v is not None and v not in CARROSSERIES:
            raise ValueError(f"Carrosserie invalide. Valeurs acceptees: {', '.join(sorted(CARROSSERIES))}")
        return v

    @field_validator("motorisation")
    @classmethod
    def check_motorisation(cls, v: str | None) -> str | None:
        if v is not None and v not in MOTORISATIONS:
            raise ValueError(f"Motorisation invalide. Valeurs acceptees: {', '.join(sorted(MOTORISATIONS))}")
        return v

    @field_validator("norme_euro")
    @classmethod
    def check_norme_euro(cls, v: str | None) -> str | None:
        if v is not None and v not in NORMES_EURO:
            raise ValueError(f"Norme Euro invalide. Valeurs acceptees: {', '.join(sorted(NORMES_EURO))}")
        return v

    @field_validator("proprietaire")
    @classmethod
    def check_proprietaire(cls, v: str) -> str:
        if v not in PROPRIETAIRE_TYPES:
            raise ValueError(f"Type proprietaire invalide. Valeurs acceptees: {', '.join(sorted(PROPRIETAIRE_TYPES))}")
        return v

    @model_validator(mode="after")
    def check_business_rules(self) -> "VehicleCreate":
        # RG-B-033: charge utile <= PTAC
        if self.charge_utile_kg and self.ptac_kg and self.charge_utile_kg > self.ptac_kg:
            raise ValueError("La charge utile ne peut pas depasser le PTAC.")
        return self


class VehicleUpdate(VehicleCreate):
    pass


class VehicleOut(BaseModel):
    id: str
    immatriculation: str | None = None
    type_entity: str | None = None
    categorie: str | None = None
    marque: str | None = None
    modele: str | None = None
    annee_mise_en_circulation: int | None = None
    carrosserie: str | None = None
    ptac_kg: int | None = None
    charge_utile_kg: int | None = None
    motorisation: str | None = None
    norme_euro: str | None = None
    proprietaire: str | None = None
    km_compteur_actuel: int | None = None
    conformite_statut: str | None = None
    statut: str | None = None
    assurance_compagnie: str | None = None
    agency_id: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Legacy compat
    plate_number: str | None = None
    brand: str | None = None
    model: str | None = None
    vehicle_type: str | None = None
    payload_kg: float | None = None
    is_active: bool = True


class VehicleDetail(VehicleOut):
    date_premiere_immatriculation: date | None = None
    vin: str | None = None
    ptra_kg: int | None = None
    volume_m3: Decimal | None = None
    longueur_utile_m: Decimal | None = None
    largeur_utile_m: Decimal | None = None
    hauteur_utile_m: Decimal | None = None
    nb_palettes_europe: int | None = None
    nb_essieux: int | None = None
    equipements: dict[str, Any] | None = None
    temperature_min: Decimal | None = None
    temperature_max: Decimal | None = None
    loueur_nom: str | None = None
    contrat_location_ref: str | None = None
    date_fin_contrat_location: date | None = None
    date_dernier_releve_km: date | None = None
    # New fields (migration 0010)
    nombre_places: int | None = None
    mode_achat: str | None = None
    valeur_assuree_ht: Decimal | None = None
    telematique: bool | None = None
    reference_client: str | None = None
    date_entree_flotte: date | None = None
    date_sortie_flotte: date | None = None
    presence_matiere_dangereuse: bool | None = None
    assurance_numero_police: str | None = None
    controle_technique_date: date | None = None
    limiteur_vitesse_date: date | None = None
    tachygraphe_date: date | None = None
    siren_proprietaire: str | None = None


# ══════════════════════════════════════════════════════════════════
# STATUS CHANGE
# ══════════════════════════════════════════════════════════════════

class StatusChange(BaseModel):
    statut: str
