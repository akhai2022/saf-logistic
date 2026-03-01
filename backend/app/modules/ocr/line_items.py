"""Line-item extraction from PDF tables using pdfplumber."""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


def _parse_number(s: str) -> float | None:
    s = s.strip().replace(" ", "").replace("\u00a0", "").replace(",", ".")
    s = re.sub(r"[€$]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def extract_line_items(pdf_path: str) -> list[dict]:
    import pdfplumber

    items: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue

                header = [str(c).lower().strip() if c else "" for c in table[0]]

                # Try to identify columns
                desc_idx = next((i for i, h in enumerate(header) if "descri" in h or "désig" in h or "libel" in h), None)
                qty_idx = next((i for i, h in enumerate(header) if "qté" in h or "quant" in h or "qty" in h), None)
                price_idx = next((i for i, h in enumerate(header) if "prix" in h or "p.u" in h or "unit" in h), None)
                amount_idx = next((i for i, h in enumerate(header) if "montant" in h or "total" in h or "ht" in h), None)

                if desc_idx is None and amount_idx is None:
                    continue

                for row in table[1:]:
                    if not row or all(not c for c in row):
                        continue

                    item = {}
                    if desc_idx is not None and desc_idx < len(row):
                        item["description"] = str(row[desc_idx] or "").strip()
                    if qty_idx is not None and qty_idx < len(row):
                        item["quantity"] = _parse_number(str(row[qty_idx] or ""))
                    if price_idx is not None and price_idx < len(row):
                        item["unit_price"] = _parse_number(str(row[price_idx] or ""))
                    if amount_idx is not None and amount_idx < len(row):
                        item["amount"] = _parse_number(str(row[amount_idx] or ""))

                    if item.get("description") or item.get("amount"):
                        items.append(item)

    return items
