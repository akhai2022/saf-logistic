"""File parsing utilities for CSV and Excel import files.

Handles:
- CSV with BOM (utf-8-sig) and latin-1 fallback
- Semicolon and comma delimiter auto-detection
- Excel (.xlsx, .xls) via openpyxl read-only mode
- French date formats (DD/MM/YYYY)
- Decimal comma normalisation
"""
from __future__ import annotations

import csv
import io
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Pattern for French-style dates: DD/MM/YYYY
_FR_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")


def _normalise_value(value: str) -> str:
    """Normalise a single cell value.

    - Strip whitespace
    - Convert French dates DD/MM/YYYY -> YYYY-MM-DD
    - Replace decimal comma -> dot *only* when value looks numeric
    """
    value = value.strip()
    if not value:
        return value

    # French date conversion
    m = _FR_DATE_RE.match(value)
    if m:
        day, month, year = m.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass  # not a valid date, keep original

    # Decimal comma: only convert if value matches a numeric pattern with comma
    # e.g. "1 234,56" or "1234,56" but not "Paris, France"
    stripped = value.replace(" ", "")
    if re.match(r"^-?\d+,\d+$", stripped):
        return stripped.replace(",", ".")

    return value


def _detect_delimiter(text_content: str) -> str:
    """Heuristic: pick the more frequent delimiter in the first 5 lines."""
    first_lines = text_content.split("\n", 5)[:5]
    sample = "\n".join(first_lines)
    semicolons = sample.count(";")
    commas = sample.count(",")
    return ";" if semicolons >= commas else ","


def _parse_csv(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    """Parse CSV bytes, returning (headers, rows_as_dicts)."""
    # Try utf-8-sig first (handles BOM), fall back to latin-1
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            text_content = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Impossible de decoder le fichier CSV (encodages utf-8, latin-1 echoues).")

    delimiter = _detect_delimiter(text_content)
    reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)

    if not reader.fieldnames:
        raise ValueError("Le fichier CSV ne contient pas d'en-tetes.")

    headers = [h.strip() for h in reader.fieldnames]
    rows: list[dict[str, str]] = []

    for row in reader:
        normalised = {}
        for key, val in row.items():
            if key is None:
                continue
            normalised[key.strip()] = _normalise_value(val or "")
        rows.append(normalised)

    return headers, rows


def _parse_excel(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    """Parse Excel bytes using openpyxl in read-only mode."""
    try:
        import openpyxl
    except ImportError:
        raise ValueError("Le package openpyxl est requis pour importer des fichiers Excel.")

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    if ws is None:
        raise ValueError("Le fichier Excel ne contient aucune feuille.")

    rows_iter = ws.iter_rows()

    # First row = headers
    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise ValueError("Le fichier Excel est vide.")

    headers = [str(cell.value).strip() if cell.value is not None else "" for cell in header_row]

    # Filter out fully-empty trailing header columns
    while headers and headers[-1] == "":
        headers.pop()

    if not headers:
        raise ValueError("Le fichier Excel ne contient pas d'en-tetes.")

    nb_cols = len(headers)
    rows: list[dict[str, str]] = []

    for excel_row in rows_iter:
        values = [cell.value for cell in excel_row[:nb_cols]]
        # Skip fully empty rows
        if all(v is None or (isinstance(v, str) and v.strip() == "") for v in values):
            continue
        row_dict: dict[str, str] = {}
        for i, header in enumerate(headers):
            raw = values[i] if i < len(values) else None
            if raw is None:
                row_dict[header] = ""
            elif isinstance(raw, datetime):
                row_dict[header] = raw.strftime("%Y-%m-%d")
            elif isinstance(raw, (int, float)):
                # Keep as string, no comma replacement needed for Excel numbers
                row_dict[header] = str(raw)
            else:
                row_dict[header] = _normalise_value(str(raw))
        rows.append(row_dict)

    wb.close()
    return headers, rows


def parse_file(content: bytes, file_name: str) -> tuple[list[str], list[dict[str, str]]]:
    """Parse a file (CSV or Excel) based on its extension.

    Returns:
        (headers, rows) where rows is a list of dicts {header: value}.
    """
    lower = file_name.lower()
    if lower.endswith((".xlsx", ".xls")):
        return _parse_excel(content)
    elif lower.endswith(".csv") or lower.endswith(".tsv") or lower.endswith(".txt"):
        return _parse_csv(content)
    else:
        raise ValueError(
            f"Format de fichier non supporte: {file_name}. "
            "Formats acceptes: .csv, .xlsx, .xls"
        )
