"""Integration tests for PDF generation — catches template rendering bugs at test time."""
from __future__ import annotations

import pytest


class _AttrDict(dict):
    """Dict with attribute-style access for building fake DB row objects."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None


def _make_mission(**overrides):
    base = {
        "id": "aaaaaaaa-0000-0000-0000-000000000001",
        "numero": "M-2024-001",
        "reference": "REF-001",
        "pickup_address": "12 Rue de Paris, 75001 Paris",
        "delivery_address": "45 Avenue de Lyon, 69001 Lyon",
        "adresse_chargement_libre": None,
        "date_chargement_prevue": "2024-06-15",
        "date_chargement_reelle": "2024-06-15",
        "date_livraison_prevue": "2024-06-16",
        "montant_vente_ht": 1500.00,
        "contraintes": {"temperature": "2-8°C", "adr": False, "hayon": True},
        "notes_exploitation": "Livraison le matin avant 10h",
        "notes": None,
        "is_subcontracted": False,
        "subcontractor_id": None,
        "cmr_numero": "CMR-M-2024-001",
        "goods_description": "Palettes de marchandises diverses",
    }
    base.update(overrides)
    return _AttrDict(base)


def _make_customer(**overrides):
    base = {
        "name": "Transports Dupont SAS",
        "raison_sociale": "Transports Dupont SAS",
        "address": "10 Boulevard Haussmann",
        "adresse_facturation_ligne1": "10 Boulevard Haussmann",
        "adresse_facturation_cp": "75009",
        "adresse_facturation_ville": "Paris",
        "adresse_facturation_pays": "FR",
        "siren": "123456789",
    }
    base.update(overrides)
    return _AttrDict(base)


def _make_company(**overrides):
    base = {
        "name": "SAF Transport",
        "address": "1 Rue Test, 75001 Paris",
        "siren": "987654321",
        "telephone": "01 23 45 67 89",
    }
    base.update(overrides)
    return _AttrDict(base)


def _make_goods_list():
    return [
        _AttrDict(description="Palette Europe", nature="Palette", quantite=10.0, unite="palette", poids_kg=500.0, volume_m3=2.5),
        _AttrDict(description="Colis fragile", nature="Colis", quantite=5.0, unite="colis", poids_kg=120.0, volume_m3=0.8),
    ]


def _make_delivery_points():
    return [
        _AttrDict(
            contact_nom="Jean Martin",
            contact_telephone="06 12 34 56 78",
            date_livraison_prevue="2024-06-16",
            date_livraison_reelle=None,
            instructions="Appeler avant livraison",
            statut="PLANIFIE",
            adresse_libre=_AttrDict(
                rue="45 Avenue de Lyon",
                code_postal="69001",
                ville="Lyon",
                pays="FR",
            ),
        ),
    ]


def _make_invoice(**overrides):
    base = {
        "invoice_number": "FAC-2024-0001",
        "issue_date": "2024-06-20",
        "due_date": "2024-07-20",
        "total_ht": 1500.00,
        "total_tva": 300.00,
        "total_ttc": 1800.00,
        "tva_rate": 20.0,
    }
    base.update(overrides)
    return _AttrDict(base)


def _make_invoice_lines():
    return [
        _AttrDict(description="Transport Paris-Lyon", quantity=1.0, unit_price=1000.00, amount_ht=1000.00),
        _AttrDict(description="Surcharge carburant", quantity=1.0, unit_price=300.00, amount_ht=300.00),
        _AttrDict(description="Frais de manutention", quantity=2.0, unit_price=100.00, amount_ht=200.00),
    ]


def _make_credit_note(**overrides):
    base = {
        "credit_note_number": "AV-2024-0001",
        "issue_date": "2024-07-01",
        "invoice_id": "bbbbbbbb-0000-0000-0000-000000000001",
        "total_ht": -500.00,
        "total_tva": -100.00,
        "total_ttc": -600.00,
        "tva_rate": 20.0,
    }
    base.update(overrides)
    return _AttrDict(base)


def _make_credit_note_lines():
    return [
        _AttrDict(description="Remise commerciale", quantity=1.0, unit_price=-500.00, amount_ht=-500.00),
    ]


def _make_tenant(**overrides):
    base = {
        "name": "SAF Transport",
        "address": "1 Rue Test, 75001 Paris",
        "siren": "987654321",
    }
    base.update(overrides)
    return _AttrDict(base)


# ---- CMR PDF Tests ----

def test_cmr_pdf_renders_with_full_data():
    """CMR with goods, customer, driver, vehicle — should produce valid PDF."""
    from app.modules.jobs.cmr_service import generate_cmr_pdf

    pdf = generate_cmr_pdf(
        mission=_make_mission(),
        delivery_points=_make_delivery_points(),
        goods=_make_goods_list(),
        customer=_make_customer(),
        company=_make_company(),
        driver=_AttrDict(prenom="Pierre", nom="Martin"),
        vehicle=_AttrDict(immatriculation="AB-123-CD"),
    )
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000


def test_cmr_pdf_renders_with_empty_goods():
    """CMR with no goods — should fall back to mission.goods_description."""
    from app.modules.jobs.cmr_service import generate_cmr_pdf

    pdf = generate_cmr_pdf(
        mission=_make_mission(),
        delivery_points=_make_delivery_points(),
        goods=[],
        customer=_make_customer(),
        company=_make_company(),
        driver=None,
        vehicle=None,
    )
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000


def test_cmr_pdf_renders_with_no_customer():
    """CMR with customer=None — should show N/A."""
    from app.modules.jobs.cmr_service import generate_cmr_pdf

    pdf = generate_cmr_pdf(
        mission=_make_mission(),
        delivery_points=_make_delivery_points(),
        goods=_make_goods_list(),
        customer=None,
        company=_make_company(),
        driver=None,
        vehicle=None,
    )
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"


def test_cmr_pdf_renders_with_no_driver_no_vehicle():
    """CMR with driver=None and vehicle=None — should show N/A for both."""
    from app.modules.jobs.cmr_service import generate_cmr_pdf

    pdf = generate_cmr_pdf(
        mission=_make_mission(),
        delivery_points=[],
        goods=_make_goods_list(),
        customer=_make_customer(),
        company=_make_company(),
        driver=None,
        vehicle=None,
    )
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"


def test_cmr_pdf_customer_address_fields():
    """CMR customer address uses adresse_facturation_* fields from DB."""
    from app.modules.jobs.cmr_service import generate_cmr_pdf
    from jinja2 import Environment, FileSystemLoader
    import os

    # Render just the HTML to check address fields are present
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "modules", "jobs", "templates")
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    template = env.get_template("cmr.html")

    customer = _make_customer()
    html = template.render(
        mission=_make_mission(),
        delivery_points=_make_delivery_points(),
        goods=_make_goods_list(),
        customer=customer,
        company=_make_company(),
        driver_name="Pierre Martin",
        vehicle_plate="AB-123-CD",
        cmr_numero="CMR-TEST",
    )
    assert "75009" in html  # adresse_facturation_cp
    assert "Paris" in html  # adresse_facturation_ville
    assert "FR" in html  # adresse_facturation_pays
    assert "10 Boulevard Haussmann" in html  # adresse_facturation_ligne1


def test_cmr_pdf_goods_totals():
    """CMR goods totals row computes correct sums."""
    from jinja2 import Environment, FileSystemLoader
    import os

    templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "modules", "jobs", "templates")
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    template = env.get_template("cmr.html")

    goods = _make_goods_list()
    html = template.render(
        mission=_make_mission(),
        delivery_points=[],
        goods=goods,
        customer=_make_customer(),
        company=_make_company(),
        driver_name="Test",
        vehicle_plate="XX-000-XX",
        cmr_numero="CMR-TOTAL-TEST",
    )
    # quantite: 10+5=15, poids: 500+120=620, volume: 2.5+0.8=3.3
    assert "15" in html  # total quantite (integer display)
    assert "620.00" in html  # total poids_kg
    assert "3.30" in html  # total volume_m3


# ---- Invoice PDF Tests ----

def test_invoice_pdf_renders_with_lines():
    """Invoice PDF with line items — should produce valid PDF."""
    from app.modules.billing.pdf_service import generate_invoice_pdf

    pdf = generate_invoice_pdf(
        invoice=_make_invoice(),
        lines=_make_invoice_lines(),
        customer=_make_customer(),
        tenant=_make_tenant(),
    )
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000


def test_invoice_pdf_renders_with_no_lines():
    """Invoice PDF with empty lines list — should still render."""
    from app.modules.billing.pdf_service import generate_invoice_pdf

    pdf = generate_invoice_pdf(
        invoice=_make_invoice(),
        lines=[],
        customer=_make_customer(),
        tenant=_make_tenant(),
    )
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"


# ---- Credit Note PDF Tests ----

def test_credit_note_pdf_renders():
    """Credit note PDF with lines — should produce valid PDF."""
    from app.modules.billing.pdf_service import generate_credit_note_pdf

    pdf = generate_credit_note_pdf(
        credit_note=_make_credit_note(),
        lines=_make_credit_note_lines(),
        customer=_make_customer(),
        tenant=_make_tenant(),
    )
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000


def test_credit_note_pdf_renders_without_invoice_ref():
    """Credit note without invoice reference — should still render."""
    from app.modules.billing.pdf_service import generate_credit_note_pdf

    pdf = generate_credit_note_pdf(
        credit_note=_make_credit_note(invoice_id=None),
        lines=_make_credit_note_lines(),
        customer=_make_customer(),
        tenant=_make_tenant(),
    )
    assert isinstance(pdf, bytes)
    assert pdf[:5] == b"%PDF-"
