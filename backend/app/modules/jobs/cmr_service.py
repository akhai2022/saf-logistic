"""CMR (Lettre de Voiture) PDF generation with WeasyPrint + Jinja2."""
from __future__ import annotations

import os

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)


def generate_cmr_pdf(
    mission,
    delivery_points,
    goods,
    customer,
    company,
    driver,
    vehicle,
) -> bytes:
    """Generate a CMR PDF document.

    Args:
        mission: The job/mission row object.
        delivery_points: List of delivery point rows.
        goods: List of goods rows.
        customer: Customer row object.
        company: Tenant/company settings row object.
        driver: Driver row object (or None).
        vehicle: Vehicle row object (or None).

    Returns:
        PDF as bytes.
    """
    # Build driver display name
    driver_name = None
    if driver:
        prenom = getattr(driver, "prenom", None) or getattr(driver, "first_name", "") or ""
        nom = getattr(driver, "nom", None) or getattr(driver, "last_name", "") or ""
        driver_name = f"{prenom} {nom}".strip() or None

    # Build vehicle plate
    vehicle_plate = None
    if vehicle:
        vehicle_plate = (
            getattr(vehicle, "immatriculation", None)
            or getattr(vehicle, "plate_number", None)
        )

    # Build CMR numero from mission data
    cmr_numero = (
        getattr(mission, "cmr_numero", None)
        or getattr(mission, "numero", None)
        or getattr(mission, "reference", None)
        or str(getattr(mission, "id", ""))
    )

    # Normalize delivery points adresse_libre for template access
    normalized_dps = []
    for dp in (delivery_points or []):
        normalized_dps.append(_normalize_dp(dp))

    # Normalize goods for safe template access
    normalized_goods = []
    for g in (goods or []):
        normalized_goods.append(_normalize_goods(g))

    template = env.get_template("cmr.html")
    html = template.render(
        mission=mission,
        delivery_points=normalized_dps,
        goods=normalized_goods,
        customer=customer,
        company=company,
        driver_name=driver_name,
        vehicle_plate=vehicle_plate,
        cmr_numero=cmr_numero,
    )
    from weasyprint import HTML
    return HTML(string=html).write_pdf()


class _AttrDict(dict):
    """Dict that supports attribute-style access (for Jinja2 templates)."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None


def _normalize_dp(dp):
    """Normalize a delivery point row into a template-friendly object."""
    import json
    d = _AttrDict()
    d["contact_nom"] = getattr(dp, "contact_nom", None)
    d["contact_telephone"] = getattr(dp, "contact_telephone", None)
    d["date_livraison_prevue"] = getattr(dp, "date_livraison_prevue", None)
    d["date_livraison_reelle"] = getattr(dp, "date_livraison_reelle", None)
    d["instructions"] = getattr(dp, "instructions", None)
    d["statut"] = getattr(dp, "statut", None)

    adresse_libre = getattr(dp, "adresse_libre", None)
    if adresse_libre:
        if isinstance(adresse_libre, str):
            try:
                adresse_libre = json.loads(adresse_libre)
            except (json.JSONDecodeError, TypeError):
                adresse_libre = {"rue": adresse_libre}
        if isinstance(adresse_libre, dict):
            d["adresse_libre"] = _AttrDict(adresse_libre)
        else:
            d["adresse_libre"] = None
    else:
        d["adresse_libre"] = None

    return d


def _normalize_goods(g):
    """Normalize a goods row into a template-friendly object."""
    d = _AttrDict()
    d["description"] = getattr(g, "description", None)
    d["nature"] = getattr(g, "nature", None)
    d["quantite"] = float(getattr(g, "quantite", 0) or 0)
    d["unite"] = getattr(g, "unite", None)
    d["poids_kg"] = float(getattr(g, "poids_kg", 0) or 0)
    d["volume_m3"] = float(getattr(g, "volume_m3", 0) or 0)
    return d
