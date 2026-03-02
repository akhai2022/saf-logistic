"""Pydantic schemas for Module I — Reporting & KPI."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class KpiCard(BaseModel):
    key: str
    label: str
    value: Decimal | float | int
    unite: str | None = None
    trend: str | None = None  # "up", "down", "stable"
    variation_pourcent: float | None = None


class DashboardResponse(BaseModel):
    role: str
    kpis: list[KpiCard]


class FinancialReport(BaseModel):
    ca_mensuel: Decimal = Decimal("0")
    ca_cumule_annuel: Decimal = Decimal("0")
    marge_brute: Decimal = Decimal("0")
    taux_marge_pourcent: float = 0.0
    dso_jours: float = 0.0
    nb_factures_impayees: int = 0
    total_impaye: Decimal = Decimal("0")
    nb_factures_emises_mois: int = 0


class OperationsReport(BaseModel):
    missions_en_cours: int = 0
    missions_terminees_mois: int = 0
    taux_cloture_j1: float = 0.0
    pod_delai_moyen_h: float = 0.0
    litiges_ouverts: int = 0
    litiges_resolus_mois: int = 0
    taux_litige: float = 0.0
    nb_missions_mois: int = 0


class FleetReport(BaseModel):
    total_vehicles: int = 0
    taux_disponibilite: float = 0.0
    taux_conformite_vehicules: float = 0.0
    cout_total_mois_ht: Decimal = Decimal("0")
    cout_moyen_km: Decimal | None = None
    pannes_non_planifiees: int = 0
    maintenances_a_venir: int = 0
    sinistres_ouverts: int = 0


class HrReport(BaseModel):
    nb_conducteurs_actifs: int = 0
    taux_conformite_conducteurs: float = 0.0
    nb_periodes_paie_ouvertes: int = 0
    anomalies_paie: int = 0


class ExportRequest(BaseModel):
    dataset: str  # "financial", "operations", "fleet", "hr"
    format: str = "csv"


class ExportResponse(BaseModel):
    filename: str
    content_type: str
    rows: int
