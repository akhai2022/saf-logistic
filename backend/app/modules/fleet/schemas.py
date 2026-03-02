"""Pydantic schemas for Module H — Fleet & Maintenance."""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field

# ── Enums as sets ──────────────────────────────────────────────────

TYPES_MAINTENANCE = {
    "CT", "VIDANGE", "PNEUS", "FREINS", "REVISION",
    "TACHYGRAPHE", "ATP", "ASSURANCE", "OTHER",
}

STATUTS_MAINTENANCE = {"PLANIFIE", "EN_COURS", "TERMINE", "ANNULE"}

CATEGORIES_COUT = {
    "CARBURANT", "PEAGE", "ASSURANCE", "LOCATION", "ENTRETIEN",
    "REPARATION", "PNEUMATIQUES", "CONTROLE_TECHNIQUE",
    "AMENDE", "LAVAGE", "AUTRE",
}

TYPES_SINISTRE = {
    "ACCIDENT_CIRCULATION", "ACCROCHAGE", "VOL", "VANDALISME",
    "BRIS_GLACE", "INCENDIE", "AUTRE",
}

RESPONSABILITES = {"RESPONSABLE", "NON_RESPONSABLE", "PARTAGE", "A_DETERMINER"}

STATUTS_SINISTRE = {"DECLARE", "EN_EXPERTISE", "EN_REPARATION", "CLOS", "REMBOURSE"}

# ── Maintenance Schedules ─────────────────────────────────────────

class ScheduleCreate(BaseModel):
    type_maintenance: str
    libelle: str
    description: str | None = None
    frequence_jours: int | None = None
    frequence_km: int | None = None
    derniere_date_realisation: date | None = None
    dernier_km_realisation: int | None = None
    prochaine_date_prevue: date | None = None
    prochain_km_prevu: int | None = None
    prestataire_par_defaut: str | None = None
    cout_estime: Decimal | None = None
    alerte_jours_avant: int = 30
    alerte_km_avant: int | None = None
    notes: str | None = None


class ScheduleUpdate(ScheduleCreate):
    type_maintenance: str | None = None  # type: ignore[assignment]
    libelle: str | None = None  # type: ignore[assignment]


class ScheduleOut(BaseModel):
    id: str
    vehicle_id: str
    type_maintenance: str
    libelle: str
    description: str | None = None
    frequence_jours: int | None = None
    frequence_km: int | None = None
    derniere_date_realisation: date | None = None
    dernier_km_realisation: int | None = None
    prochaine_date_prevue: date | None = None
    prochain_km_prevu: int | None = None
    prestataire_par_defaut: str | None = None
    cout_estime: Decimal | None = None
    alerte_jours_avant: int | None = None
    alerte_km_avant: int | None = None
    is_active: bool = True
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

# ── Maintenance Records ───────────────────────────────────────────

class MaintenanceCreate(BaseModel):
    schedule_id: str | None = None
    type_maintenance: str
    libelle: str
    description: str | None = None
    date_debut: date
    date_fin: date | None = None
    km_vehicule: int | None = None
    prestataire: str | None = None
    lieu: str | None = None
    cout_pieces_ht: Decimal | None = None
    cout_main_oeuvre_ht: Decimal | None = None
    cout_total_ht: Decimal | None = None
    cout_tva: Decimal | None = None
    cout_total_ttc: Decimal | None = None
    facture_ref: str | None = None
    is_planifie: bool = False
    statut: str = "PLANIFIE"
    resultat: str | None = None
    notes: str | None = None


class MaintenanceUpdate(BaseModel):
    type_maintenance: str | None = None
    libelle: str | None = None
    description: str | None = None
    date_debut: date | None = None
    date_fin: date | None = None
    km_vehicule: int | None = None
    prestataire: str | None = None
    lieu: str | None = None
    cout_pieces_ht: Decimal | None = None
    cout_main_oeuvre_ht: Decimal | None = None
    cout_total_ht: Decimal | None = None
    cout_tva: Decimal | None = None
    cout_total_ttc: Decimal | None = None
    facture_ref: str | None = None
    resultat: str | None = None
    notes: str | None = None


class MaintenanceOut(BaseModel):
    id: str
    vehicle_id: str
    schedule_id: str | None = None
    type_maintenance: str
    libelle: str
    description: str | None = None
    date_debut: date
    date_fin: date | None = None
    km_vehicule: int | None = None
    prestataire: str | None = None
    lieu: str | None = None
    cout_pieces_ht: Decimal | None = None
    cout_main_oeuvre_ht: Decimal | None = None
    cout_total_ht: Decimal | None = None
    cout_tva: Decimal | None = None
    cout_total_ttc: Decimal | None = None
    facture_ref: str | None = None
    is_planifie: bool = False
    statut: str = "PLANIFIE"
    resultat: str | None = None
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StatusChange(BaseModel):
    statut: str

# ── Vehicle Costs ─────────────────────────────────────────────────

class CostCreate(BaseModel):
    categorie: str
    sous_categorie: str | None = None
    libelle: str
    date_cout: date
    montant_ht: Decimal
    montant_tva: Decimal | None = None
    montant_ttc: Decimal | None = None
    km_vehicule: int | None = None
    quantite: Decimal | None = None
    unite: str | None = None
    fournisseur: str | None = None
    facture_ref: str | None = None
    notes: str | None = None


class CostUpdate(BaseModel):
    categorie: str | None = None
    sous_categorie: str | None = None
    libelle: str | None = None
    date_cout: date | None = None
    montant_ht: Decimal | None = None
    montant_tva: Decimal | None = None
    montant_ttc: Decimal | None = None
    km_vehicule: int | None = None
    quantite: Decimal | None = None
    unite: str | None = None
    fournisseur: str | None = None
    facture_ref: str | None = None
    notes: str | None = None


class CostOut(BaseModel):
    id: str
    vehicle_id: str
    maintenance_record_id: str | None = None
    categorie: str
    sous_categorie: str | None = None
    libelle: str
    date_cout: date
    montant_ht: Decimal
    montant_tva: Decimal | None = None
    montant_ttc: Decimal | None = None
    km_vehicule: int | None = None
    quantite: Decimal | None = None
    unite: str | None = None
    fournisseur: str | None = None
    facture_ref: str | None = None
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CostSummary(BaseModel):
    categorie: str
    total_ht: Decimal
    total_ttc: Decimal | None = None
    count: int

# ── Vehicle Claims ────────────────────────────────────────────────

class ClaimCreate(BaseModel):
    date_sinistre: date
    heure_sinistre: time | None = None
    lieu: str | None = None
    type_sinistre: str
    description: str | None = None
    driver_id: str | None = None
    tiers_implique: bool = False
    tiers_nom: str | None = None
    tiers_immatriculation: str | None = None
    tiers_assurance: str | None = None
    tiers_police: str | None = None
    assurance_ref: str | None = None
    assurance_declaration_date: date | None = None
    responsabilite: str = "A_DETERMINER"
    cout_reparation_ht: Decimal | None = None
    franchise: Decimal | None = None
    cout_immobilisation_estime: Decimal | None = None
    jours_immobilisation: int | None = None
    notes: str | None = None


class ClaimUpdate(BaseModel):
    date_sinistre: date | None = None
    heure_sinistre: time | None = None
    lieu: str | None = None
    type_sinistre: str | None = None
    description: str | None = None
    driver_id: str | None = None
    tiers_implique: bool | None = None
    tiers_nom: str | None = None
    tiers_immatriculation: str | None = None
    tiers_assurance: str | None = None
    tiers_police: str | None = None
    assurance_ref: str | None = None
    assurance_declaration_date: date | None = None
    responsabilite: str | None = None
    cout_reparation_ht: Decimal | None = None
    franchise: Decimal | None = None
    indemnisation_recue: Decimal | None = None
    cout_immobilisation_estime: Decimal | None = None
    jours_immobilisation: int | None = None
    date_cloture: date | None = None
    notes: str | None = None


class ClaimOut(BaseModel):
    id: str
    vehicle_id: str
    numero: str
    date_sinistre: date
    heure_sinistre: time | None = None
    lieu: str | None = None
    type_sinistre: str
    description: str | None = None
    driver_id: str | None = None
    tiers_implique: bool = False
    tiers_nom: str | None = None
    tiers_immatriculation: str | None = None
    tiers_assurance: str | None = None
    tiers_police: str | None = None
    constat_s3_key: str | None = None
    assurance_ref: str | None = None
    assurance_declaration_date: date | None = None
    responsabilite: str | None = None
    cout_reparation_ht: Decimal | None = None
    franchise: Decimal | None = None
    indemnisation_recue: Decimal | None = None
    cout_immobilisation_estime: Decimal | None = None
    jours_immobilisation: int | None = None
    statut: str = "DECLARE"
    date_cloture: date | None = None
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

# ── Fleet Dashboard ───────────────────────────────────────────────

class FleetDashboardStats(BaseModel):
    total_vehicles: int = 0
    vehicles_actifs: int = 0
    vehicles_en_maintenance: int = 0
    vehicles_immobilises: int = 0
    taux_disponibilite: float = 0.0
    maintenances_a_venir_30j: int = 0
    maintenances_en_retard: int = 0
    sinistres_ouverts: int = 0
    cout_total_mois_ht: Decimal = Decimal("0")
    cout_moyen_km: Decimal | None = None
