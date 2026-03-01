"""Invoice PDF generation with WeasyPrint."""
from __future__ import annotations

import os

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)


def generate_invoice_pdf(invoice, lines, customer, tenant) -> bytes:
    template = env.get_template("invoice.html")
    html = template.render(
        invoice=invoice,
        lines=lines,
        customer=customer,
        tenant=tenant,
    )
    from weasyprint import HTML
    return HTML(string=html).write_pdf()
