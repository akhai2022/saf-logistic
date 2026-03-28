"""Schemas for Route Templates (Tournée modèle)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

TEMPLATE_STATUSES = {"DRAFT", "ACTIVE", "SUSPENDED", "ARCHIVED"}
RECURRENCE_RULES = {"QUOTIDIENNE", "LUN_VEN", "LUN_SAM", "HEBDOMADAIRE", "BIMENSUELLE", "MENSUELLE"}
STOP_TYPES = {"PICKUP", "DELIVERY", "RELAY"}


class RouteTemplateCreate(BaseModel):
    code: str
    label: str
    customer_id: str | None = None
    site: str | None = None
    recurrence_rule: str = "LUN_VEN"
    valid_from: date
    valid_to: date | None = None
    default_driver_id: str | None = None
    default_vehicle_id: str | None = None
    is_subcontracted: bool = False
    default_subcontractor_id: str | None = None
    default_mission_type: str = "LOT_COMPLET"
    default_sale_amount_ht: Decimal | None = None
    default_purchase_amount_ht: Decimal | None = None
    default_loading_address: str | None = None
    default_estimated_distance_km: Decimal | None = None
    default_constraints_json: dict | None = None
    notes: str | None = None
    agency_id: str | None = None


class RouteTemplateUpdate(RouteTemplateCreate):
    status: str | None = None


class RouteTemplateOut(BaseModel):
    id: str
    code: str
    label: str
    customer_id: str | None = None
    customer_name: str | None = None
    site: str | None = None
    status: str
    recurrence_rule: str
    valid_from: date | None = None
    valid_to: date | None = None
    default_driver_id: str | None = None
    default_driver_name: str | None = None
    default_vehicle_id: str | None = None
    default_vehicle_plate: str | None = None
    default_mission_type: str | None = None
    default_sale_amount_ht: Decimal | None = None
    default_purchase_amount_ht: Decimal | None = None
    is_subcontracted: bool = False
    nb_runs: int = 0
    nb_missions: int = 0
    created_at: str | None = None


class StopOut(BaseModel):
    id: str
    sequence: int
    stop_type: str | None = None
    name: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    instructions: str | None = None


class RouteTemplateDetail(RouteTemplateOut):
    default_loading_address: str | None = None
    default_estimated_distance_km: Decimal | None = None
    default_constraints_json: dict | None = None
    notes: str | None = None
    agency_id: str | None = None
    default_subcontractor_id: str | None = None
    stops: list[StopOut] = []


class StopCreate(BaseModel):
    sequence: int
    stop_type: str = "DELIVERY"
    name: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    instructions: str | None = None


class GenerateRunsRequest(BaseModel):
    start_date: date
    end_date: date
    override_driver_id: str | None = None
    override_vehicle_id: str | None = None
    auto_create_missions: bool = True
