"""Schemas for Route Runs (Exécution / Tournée du jour)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

RUN_STATUSES = {"DRAFT", "PLANNED", "DISPATCHED", "IN_PROGRESS", "COMPLETED", "CANCELLED"}

RUN_TRANSITIONS = {
    "DRAFT": {"PLANNED", "CANCELLED"},
    "PLANNED": {"DISPATCHED", "DRAFT", "CANCELLED"},
    "DISPATCHED": {"IN_PROGRESS", "PLANNED", "CANCELLED"},
    "IN_PROGRESS": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


class RouteRunCreate(BaseModel):
    route_template_id: str | None = None
    code: str | None = None  # auto-generated if not provided
    service_date: date
    assigned_driver_id: str | None = None
    assigned_vehicle_id: str | None = None
    planned_start_at: str | None = None
    planned_end_at: str | None = None
    notes: str | None = None


class RouteRunUpdate(RouteRunCreate):
    pass


class RouteRunMissionOut(BaseModel):
    id: str
    mission_id: str
    mission_code: str | None = None
    sequence: int
    assignment_status: str | None = None
    planned_eta: str | None = None
    actual_eta: str | None = None
    customer_name: str | None = None
    mission_status: str | None = None
    montant_vente_ht: Decimal | None = None


class RouteRunOut(BaseModel):
    id: str
    route_template_id: str | None = None
    template_code: str | None = None
    template_label: str | None = None
    code: str
    service_date: date
    status: str
    assigned_driver_id: str | None = None
    assigned_driver_name: str | None = None
    assigned_vehicle_id: str | None = None
    assigned_vehicle_plate: str | None = None
    planned_start_at: str | None = None
    planned_end_at: str | None = None
    actual_start_at: str | None = None
    actual_end_at: str | None = None
    aggregated_sale_amount_ht: Decimal | None = None
    aggregated_purchase_amount_ht: Decimal | None = None
    aggregated_margin_ht: Decimal | None = None
    nb_missions: int = 0
    notes: str | None = None
    created_at: str | None = None


class RouteRunDetail(RouteRunOut):
    missions: list[RouteRunMissionOut] = []


class AssignMissionRequest(BaseModel):
    mission_id: str
    sequence: int | None = None  # auto-calculated if not provided


class ReorderRequest(BaseModel):
    mission_ids: list[str]  # ordered list of mission IDs
