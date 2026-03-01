#!/usr/bin/env python3
"""Generate deterministic PDF fixtures using ReportLab.

Creates:
  - backend/app/tests/fixtures/pod.pdf            (Proof of Delivery)
  - backend/app/tests/fixtures/supplier_invoice.pdf (French supplier invoice)

Usage:
    python -m scripts.generate_fixtures
    # or from backend/:
    python scripts/generate_fixtures.py
"""
from __future__ import annotations

import os
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "tests", "fixtures")


def generate_pod_pdf() -> bytes:
    """Generate a deterministic Proof of Delivery PDF."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=12)
    normal = styles["Normal"]

    elements = []

    # Header
    elements.append(Paragraph("PREUVE DE LIVRAISON", title_style))
    elements.append(Paragraph("Proof of Delivery", normal))
    elements.append(Spacer(1, 1 * cm))

    # Metadata table
    meta_data = [
        ["N° Mission:", "JOB-2024-0042"],
        ["Date de livraison:", "15/01/2024"],
        ["Transporteur:", "SAF Transport Demo"],
        ["Conducteur:", "Jean Dupont (SAF-001)"],
        ["Immatriculation:", "AB-123-CD"],
    ]
    meta_table = Table(meta_data, colWidths=[5 * cm, 10 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.8 * cm))

    # Shipment details
    elements.append(Paragraph("<b>Expéditeur:</b> Carrefour Logistique — 1 Av. des Champs, 75008 Paris", normal))
    elements.append(Paragraph("<b>Destinataire:</b> Entrepôt Lyon Sud — 42 Rue Garibaldi, 69007 Lyon", normal))
    elements.append(Spacer(1, 0.5 * cm))

    # Goods table
    goods_data = [
        ["Description", "Quantité", "Poids (kg)", "État"],
        ["Palettes alimentaires", "12", "4 800", "Conforme"],
        ["Colis frigorifiques", "6", "1 200", "Conforme"],
    ]
    goods_table = Table(goods_data, colWidths=[7 * cm, 3 * cm, 3 * cm, 3 * cm])
    goods_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(goods_table)
    elements.append(Spacer(1, 1 * cm))

    # Signature block
    elements.append(Paragraph("<b>Réserves:</b> Aucune", normal))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Signature du destinataire: ___________________________", normal))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Nom: ___________________________    Date: 15/01/2024", normal))

    doc.build(elements)
    return buf.getvalue()


def generate_supplier_invoice_pdf() -> bytes:
    """Generate a deterministic French supplier invoice PDF."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("InvTitle", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#2563eb"))
    normal = styles["Normal"]
    bold = ParagraphStyle("Bold", parent=normal, fontName="Helvetica-Bold")

    elements = []

    # Supplier header
    elements.append(Paragraph("TRANSPORTS MARTIN SARL", bold))
    elements.append(Paragraph("42 Boulevard Haussmann, 75009 Paris", normal))
    elements.append(Paragraph("SIREN: 512345678 — TVA: FR12512345678", normal))
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph("FACTURE", title_style))
    elements.append(Spacer(1, 0.3 * cm))

    # Invoice metadata
    meta_data = [
        ["N° Facture:", "FOUR-2024-001"],
        ["Date:", "15/01/2024"],
        ["Échéance:", "14/02/2024"],
        ["Client:", "SAF Transport Demo"],
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, 10 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.8 * cm))

    # Line items
    line_data = [
        ["Description", "Qté", "P.U. HT", "Montant HT"],
        ["Transport Paris → Lyon (465 km)", "1", "697,50 €", "697,50 €"],
        ["Surcharge carburant", "1", "50,00 €", "50,00 €"],
        ["Manutention", "1", "120,00 €", "120,00 €"],
    ]
    line_table = Table(line_data, colWidths=[8 * cm, 2 * cm, 3 * cm, 3 * cm])
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 0.5 * cm))

    # Totals
    totals_data = [
        ["Total HT:", "867,50 €"],
        ["TVA 20%:", "173,50 €"],
        ["Total TTC:", "1 041,00 €"],
    ]
    totals_table = Table(totals_data, colWidths=[4 * cm, 3 * cm], hAlign="RIGHT")
    totals_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTSIZE", (0, 2), (-1, 2), 12),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (0, 2), (-1, 2), 1.5, colors.HexColor("#2563eb")),
        ("TOPPADDING", (0, 2), (-1, 2), 8),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 1 * cm))

    # Payment info
    elements.append(Paragraph("<b>Conditions de paiement:</b> 30 jours date de facture", normal))
    elements.append(Paragraph("<b>IBAN:</b> FR76 3000 4000 0300 0001 2345 N02", normal))

    doc.build(elements)
    return buf.getvalue()


def main():
    os.makedirs(FIXTURES_DIR, exist_ok=True)

    pod_path = os.path.join(FIXTURES_DIR, "pod.pdf")
    pod_bytes = generate_pod_pdf()
    with open(pod_path, "wb") as f:
        f.write(pod_bytes)
    print(f"Generated {pod_path} ({len(pod_bytes)} bytes)")

    inv_path = os.path.join(FIXTURES_DIR, "supplier_invoice.pdf")
    inv_bytes = generate_supplier_invoice_pdf()
    with open(inv_path, "wb") as f:
        f.write(inv_bytes)
    print(f"Generated {inv_path} ({len(inv_bytes)} bytes)")


if __name__ == "__main__":
    main()
