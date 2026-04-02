"""Pydantic schemas for operational data tables.

Covers: customer_complaints, driver_infractions, traffic_violations,
        driver_leaves, staff_schedules, vehicle_repairs.
"""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field

# ── Enum-like sets for validation ────────────────────────────────

SEVERITIES = {"NORMAL", "GRAVE", "CRITIQUE"}
COMPLAINT_STATUSES = {"OUVERTE", "EN_COURS", "RESOLUE", "CLASSEE"}

PAYMENT_STATUSES = {"A_PAYER", "PAYE", "CONTESTE"}

LEAVE_TYPES = {"CONGES_PAYES", "RTT", "MALADIE", "SANS_SOLDE", "AUTRE"}
LEAVE_STATUSES = {"DEMANDE", "APPROUVE", "REFUSE", "ANNULE"}

SCHEDULE_STATUSES = {"SERVICE", "REPOS", "CONGE", "MALADIE", "FORMATION"}

REPAIR_CATEGORIES = {
    "VIDANGE", "CLEF", "LIMITEUR", "CONTROLE_TECHNIQUE", "VALISE_ADR",
    "ETIQUETTE_ANGLES_MORTS", "TACHYGRAPHE", "REPARATION", "AUTRE",
}
REPAIR_STATUSES = {"OK", "A_FAIRE", "EN_COURS", "FAIT"}


# ── Customer Complaints (RECLAMATIONS) ───────────────────────────

class ComplaintCreate(BaseModel):
    date_incident: date | None = None
    client_name: str | None = Field(None, max_length=200)
    client_id: str | None = None
    contact_name: str | None = Field(None, max_length=200)
    subject: str = Field(..., min_length=1)
    driver_id: str | None = None
    severity: str = "NORMAL"
    status: str = "OUVERTE"
    resolution: str | None = None


class ComplaintOut(BaseModel):
    id: str
    tenant_id: str
    date_incident: date | None = None
    client_name: str | None = None
    client_id: str | None = None
    contact_name: str | None = None
    subject: str
    driver_id: str | None = None
    driver_nom: str | None = None
    driver_prenom: str | None = None
    severity: str = "NORMAL"
    status: str = "OUVERTE"
    resolution: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Driver Infractions (INFRACTIONS CHAUFFEURS) ──────────────────

class InfractionCreate(BaseModel):
    driver_id: str
    year: int
    month: int = Field(..., ge=1, le=12)
    infraction_count: int = 0
    anomaly_count: int = 0
    notes: str | None = None


class InfractionOut(BaseModel):
    id: str
    tenant_id: str
    driver_id: str
    driver_matricule: str | None = None
    driver_nom: str | None = None
    driver_prenom: str | None = None
    year: int
    month: int
    infraction_count: int = 0
    anomaly_count: int = 0
    notes: str | None = None
    created_at: datetime | None = None


# ── Traffic Violations (CONTRAVENTIONS) ──────────────────────────

class ViolationCreate(BaseModel):
    date_infraction: date | None = None
    lieu: str | None = Field(None, max_length=200)
    vehicle_id: str | None = None
    immatriculation: str | None = Field(None, max_length=15)
    description: str | None = None
    numero_avis: str | None = Field(None, max_length=50)
    montant: Decimal | None = None
    statut_paiement: str = "A_PAYER"
    statut_dossier: str | None = None
    driver_id: str | None = None


class ViolationOut(BaseModel):
    id: str
    tenant_id: str
    date_infraction: date | None = None
    lieu: str | None = None
    vehicle_id: str | None = None
    immatriculation: str | None = None
    description: str | None = None
    numero_avis: str | None = None
    montant: Decimal | None = None
    statut_paiement: str = "A_PAYER"
    statut_dossier: str | None = None
    driver_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Driver Leaves (Tableau des congés) ───────────────────────────

class LeaveCreate(BaseModel):
    driver_id: str
    date_debut: date
    date_fin: date
    type_conge: str = "CONGES_PAYES"
    statut: str = "APPROUVE"
    notes: str | None = None


class LeaveOut(BaseModel):
    id: str
    tenant_id: str
    driver_id: str
    driver_matricule: str | None = None
    driver_nom: str | None = None
    driver_prenom: str | None = None
    date_debut: date
    date_fin: date
    type_conge: str = "CONGES_PAYES"
    statut: str = "APPROUVE"
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Staff Schedules (Planning de travail SAF AT) ───────────────

class ScheduleCreate(BaseModel):
    driver_id: str
    date: date
    status: str = "SERVICE"
    shift_start: time | None = None
    shift_end: time | None = None
    notes: str | None = None


class ScheduleOut(BaseModel):
    id: str
    tenant_id: str
    driver_id: str
    date: date
    status: str = "SERVICE"
    shift_start: time | None = None
    shift_end: time | None = None
    notes: str | None = None
    created_at: datetime | None = None


# ── Vehicle Repairs (tableau REPARATION 3 mois format) ─────────

class RepairCreate(BaseModel):
    vehicle_id: str
    immatriculation: str | None = Field(None, max_length=15)
    category: str
    description: str | None = None
    status: str = "A_FAIRE"
    date_signalement: date | None = None
    date_realisation: date | None = None
    cout: Decimal | None = None
    prestataire: str | None = Field(None, max_length=200)
    notes: str | None = None


class RepairOut(BaseModel):
    id: str
    tenant_id: str
    vehicle_id: str
    immatriculation: str | None = None
    category: str
    description: str | None = None
    status: str = "A_FAIRE"
    date_signalement: date | None = None
    date_realisation: date | None = None
    cout: Decimal | None = None
    prestataire: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
