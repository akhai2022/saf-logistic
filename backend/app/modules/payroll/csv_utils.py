"""CSV parsing helpers for payroll import."""
from __future__ import annotations

import csv
import io


def parse_payroll_csv(content: bytes) -> list[dict]:
    """Parse payroll CSV: delimiter ;, BOM tolerant, decimal comma accepted."""
    text_content = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text_content), delimiter=";")
    rows = []
    for row in reader:
        cleaned = {}
        for k, v in row.items():
            cleaned[k.strip().lower()] = v.strip() if v else ""
        rows.append(cleaned)
    return rows


def normalize_decimal(value: str) -> float | None:
    """Parse a decimal value that may use comma as decimal separator."""
    if not value:
        return None
    value = value.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None
