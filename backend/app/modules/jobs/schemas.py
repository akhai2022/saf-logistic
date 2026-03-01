"""Pydantic v2 schemas for Module C — Missions, Delivery Points, Goods, POD, Disputes."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# ── Enums ─────────────────────────────────────────────────────────

MISSION_STATUTS = {"BROUILLON", "PLANIFIEE", "AFFECTEE", "EN_COURS", "LIVREE", "CLOTUREE", "FACTUREE", "ANNULEE"}
TYPES_MISSION = {"LOT_COMPLET", "MESSAGERIE", "GROUPAGE", "AFFRETEMENT", "COURSE_URGENTE"}
PRIORITES = {"BASSE", "NORMALE", "HAUTE", "URGENTE"}

DP_STATUTS = {"EN_ATTENTE", "EN_COURS", "LIVRE", "ECHEC", "REPORTE"}

GOODS_NATURES = {"PALETTE", "COLIS", "VRAC", "CONTENEUR", "VEHICULE", "DIVERS"}
GOODS_UNITES = {"PALETTE", "COLIS", "KG", "TONNE", "M3", "LITRE", "UNITE"}

POD_TYPES = {"PHOTO", "PDF_SCAN", "E_SIGNATURE"}
POD_STATUTS = {"EN_ATTENTE", "VALIDE", "REJETE"}
RESERVES_CATEGORIES = {"AVARIE", "MANQUANT", "RETARD", "COLIS_ENDOMMAGE", "AUTRE"}
POD_MIME_TYPES = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}

DISPUTE_TYPES = {"AVARIE", "PERTE_TOTALE", "PERTE_PARTIELLE", "RETARD", "REFUS_LIVRAISON", "ECART_QUANTITE", "ERREUR_ADRESSE", "AUTRE"}
DISPUTE_RESPONSABILITES = {"TRANSPORTEUR", "CLIENT", "SOUS_TRAITANT", "TIERS", "A_DETERMINER"}
DISPUTE_STATUTS = {"OUVERT", "EN_INSTRUCTION", "RESOLU", "CLOS_ACCEPTE", "CLOS_REFUSE", "CLOS_SANS_SUITE"}
DISPUTE_IMPACTS = {"AUCUN", "AVOIR_TOTAL", "AVOIR_PARTIEL", "REMISE_PROCHAINE_FACTURE"}

# Status transitions map (spec C.6.1) — using new status names
VALID_TRANSITIONS = {
    "BROUILLON": ["PLANIFIEE", "ANNULEE"],
    "PLANIFIEE": ["AFFECTEE", "BROUILLON", "ANNULEE"],
    "AFFECTEE": ["EN_COURS", "PLANIFIEE", "ANNULEE"],
    "EN_COURS": ["LIVREE", "AFFECTEE", "ANNULEE"],
    "LIVREE": ["CLOTUREE"],
    "CLOTUREE": ["FACTUREE"],
    # Legacy lowercase support
    "draft": ["planned", "PLANIFIEE"],
    "planned": ["assigned", "draft", "AFFECTEE", "BROUILLON"],
    "assigned": ["in_progress", "planned", "EN_COURS", "PLANIFIEE"],
    "in_progress": ["delivered", "assigned", "LIVREE", "AFFECTEE"],
    "delivered": ["closed", "CLOTUREE"],
}


# ══════════════════════════════════════════════════════════════════
# DELIVERY POINT
# ══════════════════════════════════════════════════════════════════

class DeliveryPointCreate(BaseModel):
    ordre: int = 1
    adresse_id: str | None = None
    adresse_libre: dict[str, Any] | None = None
    contact_nom: str | None = None
    contact_telephone: str | None = None
    date_livraison_prevue: str | None = None
    instructions: str | None = None

class DeliveryPointOut(BaseModel):
    id: str
    mission_id: str
    ordre: int
    adresse_id: str | None = None
    adresse_libre: dict[str, Any] | None = None
    contact_nom: str | None = None
    contact_telephone: str | None = None
    date_livraison_prevue: str | None = None
    date_livraison_reelle: str | None = None
    instructions: str | None = None
    statut: str
    motif_echec: str | None = None

class DeliveryPointStatusChange(BaseModel):
    statut: str
    motif_echec: str | None = None

    @field_validator("statut")
    @classmethod
    def check_statut(cls, v: str) -> str:
        if v not in DP_STATUTS:
            raise ValueError(f"Statut invalide. Valeurs: {', '.join(sorted(DP_STATUTS))}")
        return v


# ══════════════════════════════════════════════════════════════════
# GOODS
# ══════════════════════════════════════════════════════════════════

class GoodsCreate(BaseModel):
    delivery_point_id: str | None = None
    description: str
    nature: str
    quantite: Decimal
    unite: str
    poids_brut_kg: Decimal
    poids_net_kg: Decimal | None = None
    volume_m3: Decimal | None = None
    longueur_m: Decimal | None = None
    largeur_m: Decimal | None = None
    hauteur_m: Decimal | None = None
    valeur_declaree_eur: Decimal | None = None
    adr_classe: str | None = None
    adr_numero_onu: str | None = None
    adr_designation: str | None = None
    temperature_min: Decimal | None = None
    temperature_max: Decimal | None = None
    references_colis: list[str] | None = None

    @field_validator("nature")
    @classmethod
    def check_nature(cls, v: str) -> str:
        if v not in GOODS_NATURES:
            raise ValueError(f"Nature invalide. Valeurs: {', '.join(sorted(GOODS_NATURES))}")
        return v

    @field_validator("unite")
    @classmethod
    def check_unite(cls, v: str) -> str:
        if v not in GOODS_UNITES:
            raise ValueError(f"Unite invalide. Valeurs: {', '.join(sorted(GOODS_UNITES))}")
        return v

class GoodsOut(BaseModel):
    id: str
    mission_id: str
    delivery_point_id: str | None = None
    description: str
    nature: str
    quantite: Decimal
    unite: str
    poids_brut_kg: Decimal
    poids_net_kg: Decimal | None = None
    volume_m3: Decimal | None = None
    valeur_declaree_eur: Decimal | None = None
    adr_classe: str | None = None
    temperature_min: Decimal | None = None
    temperature_max: Decimal | None = None
    references_colis: list[str] | None = None


# ══════════════════════════════════════════════════════════════════
# POD
# ══════════════════════════════════════════════════════════════════

class PodCreate(BaseModel):
    delivery_point_id: str | None = None
    type: str = "PHOTO"
    fichier_s3_key: str
    fichier_nom_original: str
    fichier_taille_octets: int
    fichier_mime_type: str
    geoloc_latitude: Decimal | None = None
    geoloc_longitude: Decimal | None = None
    geoloc_precision_m: int | None = None
    has_reserves: bool = False
    reserves_texte: str | None = None
    reserves_categorie: str | None = None

    @field_validator("type")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in POD_TYPES:
            raise ValueError(f"Type POD invalide. Valeurs: {', '.join(sorted(POD_TYPES))}")
        return v

    @field_validator("fichier_mime_type")
    @classmethod
    def check_mime(cls, v: str) -> str:
        if v not in POD_MIME_TYPES:
            raise ValueError("Format de fichier non supporte. Utilisez JPG, PNG ou PDF.")  # RG-C-020
        return v

    @field_validator("fichier_taille_octets")
    @classmethod
    def check_size(cls, v: int) -> int:
        if v > 10 * 1024 * 1024:
            raise ValueError("Le fichier depasse la taille maximale de 10 Mo.")  # RG-C-021
        return v

    @field_validator("reserves_categorie")
    @classmethod
    def check_reserves_cat(cls, v: str | None) -> str | None:
        if v is not None and v not in RESERVES_CATEGORIES:
            raise ValueError(f"Categorie reserve invalide. Valeurs: {', '.join(sorted(RESERVES_CATEGORIES))}")
        return v

class PodOut(BaseModel):
    id: str
    mission_id: str
    delivery_point_id: str | None = None
    type: str
    fichier_s3_key: str
    fichier_nom_original: str
    fichier_taille_octets: int
    fichier_mime_type: str
    date_upload: str | None = None
    uploaded_by: str | None = None
    geoloc_latitude: Decimal | None = None
    geoloc_longitude: Decimal | None = None
    has_reserves: bool = False
    reserves_texte: str | None = None
    reserves_categorie: str | None = None
    statut: str
    date_validation: str | None = None
    validated_by: str | None = None
    motif_rejet: str | None = None

class PodValidation(BaseModel):
    statut: str  # VALIDE or REJETE
    motif_rejet: str | None = None

    @field_validator("statut")
    @classmethod
    def check_statut(cls, v: str) -> str:
        if v not in {"VALIDE", "REJETE"}:
            raise ValueError("Statut invalide. Valeurs: VALIDE, REJETE")
        return v


# ══════════════════════════════════════════════════════════════════
# DISPUTE
# ══════════════════════════════════════════════════════════════════

class DisputeCreate(BaseModel):
    type: str
    description: str
    responsabilite: str
    responsable_entity_id: str | None = None
    montant_estime_eur: Decimal | None = None
    assigned_to: str | None = None
    notes_internes: str | None = None

    @field_validator("type")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in DISPUTE_TYPES:
            raise ValueError(f"Type litige invalide. Valeurs: {', '.join(sorted(DISPUTE_TYPES))}")
        return v

    @field_validator("responsabilite")
    @classmethod
    def check_resp(cls, v: str) -> str:
        if v not in DISPUTE_RESPONSABILITES:
            raise ValueError(f"Responsabilite invalide. Valeurs: {', '.join(sorted(DISPUTE_RESPONSABILITES))}")
        return v

class DisputeUpdate(BaseModel):
    statut: str | None = None
    description: str | None = None
    responsabilite: str | None = None
    montant_estime_eur: Decimal | None = None
    montant_retenu_eur: Decimal | None = None
    resolution_texte: str | None = None
    impact_facturation: str | None = None
    assigned_to: str | None = None
    notes_internes: str | None = None

    @field_validator("statut")
    @classmethod
    def check_statut(cls, v: str | None) -> str | None:
        if v is not None and v not in DISPUTE_STATUTS:
            raise ValueError(f"Statut invalide. Valeurs: {', '.join(sorted(DISPUTE_STATUTS))}")
        return v

    @field_validator("impact_facturation")
    @classmethod
    def check_impact(cls, v: str | None) -> str | None:
        if v is not None and v not in DISPUTE_IMPACTS:
            raise ValueError(f"Impact invalide. Valeurs: {', '.join(sorted(DISPUTE_IMPACTS))}")
        return v

class DisputeOut(BaseModel):
    id: str
    numero: str | None = None
    mission_id: str
    type: str
    description: str
    responsabilite: str
    responsable_entity_id: str | None = None
    montant_estime_eur: Decimal | None = None
    montant_retenu_eur: Decimal | None = None
    statut: str
    date_ouverture: str | None = None
    date_resolution: str | None = None
    resolution_texte: str | None = None
    impact_facturation: str | None = None
    opened_by: str | None = None
    assigned_to: str | None = None
    notes_internes: str | None = None
    created_at: str | None = None

class DisputeAttachmentCreate(BaseModel):
    fichier_s3_key: str
    fichier_nom_original: str
    fichier_taille_octets: int
    fichier_mime_type: str
    description: str | None = None

class DisputeAttachmentOut(BaseModel):
    id: str
    dispute_id: str
    fichier_s3_key: str
    fichier_nom_original: str
    fichier_taille_octets: int
    fichier_mime_type: str
    description: str | None = None
    uploaded_by: str | None = None
    created_at: str | None = None


# ══════════════════════════════════════════════════════════════════
# MISSION
# ══════════════════════════════════════════════════════════════════

class MissionCreate(BaseModel):
    reference_client: str | None = None
    client_id: str
    type_mission: str = "LOT_COMPLET"
    priorite: str = "NORMALE"
    date_chargement_prevue: str | None = None
    date_livraison_prevue: str | None = None
    adresse_chargement_id: str | None = None
    adresse_chargement_libre: dict[str, Any] | None = None
    adresse_chargement_contact: str | None = None
    adresse_chargement_instructions: str | None = None
    distance_estimee_km: Decimal | None = None
    montant_vente_ht: Decimal | None = None
    contraintes: dict[str, Any] | None = None
    notes_exploitation: str | None = None
    notes_internes: str | None = None
    # Legacy compat
    reference: str | None = None
    pickup_address: str | None = None
    delivery_address: str | None = None
    pickup_date: str | None = None
    delivery_date: str | None = None
    distance_km: float | None = None
    weight_kg: float | None = None
    goods_description: str | None = None
    notes: str | None = None

    @field_validator("type_mission")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in TYPES_MISSION:
            raise ValueError(f"Type mission invalide. Valeurs: {', '.join(sorted(TYPES_MISSION))}")
        return v

    @field_validator("priorite")
    @classmethod
    def check_priorite(cls, v: str) -> str:
        if v not in PRIORITES:
            raise ValueError(f"Priorite invalide. Valeurs: {', '.join(sorted(PRIORITES))}")
        return v

class MissionUpdate(MissionCreate):
    client_id: str | None = None  # type: ignore[assignment]

class MissionAssign(BaseModel):
    driver_id: str | None = None
    vehicle_id: str | None = None
    trailer_id: str | None = None
    subcontractor_id: str | None = None
    is_subcontracted: bool = False
    montant_achat_ht: Decimal | None = None

class MissionStatusChange(BaseModel):
    statut: str
    motif: str | None = None  # required for ANNULEE

class MissionOut(BaseModel):
    id: str
    numero: str | None = None
    reference: str | None = None
    reference_client: str | None = None
    client_id: str | None = None
    client_raison_sociale: str | None = None
    type_mission: str | None = None
    priorite: str | None = None
    # New status field + legacy
    statut: str | None = None
    status: str | None = None
    # Dates
    date_chargement_prevue: str | None = None
    date_livraison_prevue: str | None = None
    date_cloture: str | None = None
    # Assignment
    driver_id: str | None = None
    vehicle_id: str | None = None
    trailer_id: str | None = None
    subcontractor_id: str | None = None
    is_subcontracted: bool = False
    # Financial
    montant_vente_ht: Decimal | None = None
    montant_achat_ht: Decimal | None = None
    montant_tva: Decimal | None = None
    montant_vente_ttc: Decimal | None = None
    marge_brute: Decimal | None = None
    # Addresses
    adresse_chargement_libre: dict[str, Any] | None = None
    distance_estimee_km: Decimal | None = None
    distance_reelle_km: Decimal | None = None
    contraintes: dict[str, Any] | None = None
    notes_exploitation: str | None = None
    # Legacy compat
    pickup_address: str | None = None
    delivery_address: str | None = None
    distance_km: float | None = None
    weight_kg: float | None = None
    goods_description: str | None = None
    notes: str | None = None
    pod_s3_key: str | None = None
    created_at: str | None = None
    agency_id: str | None = None

class MissionDetail(MissionOut):
    date_chargement_reelle: str | None = None
    date_livraison_reelle: str | None = None
    adresse_chargement_id: str | None = None
    adresse_chargement_contact: str | None = None
    adresse_chargement_instructions: str | None = None
    notes_internes: str | None = None
    delivery_points: list[DeliveryPointOut] = []
    goods: list[GoodsOut] = []
    pods: list[PodOut] = []
    disputes: list[DisputeOut] = []
