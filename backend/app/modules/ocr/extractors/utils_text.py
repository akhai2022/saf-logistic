"""Text utilities for OCR extraction: normalization, amount/date parsing."""
from __future__ import annotations

import re
from datetime import datetime


# ── Amount parsing ────────────────────────────────────────────────

def parse_french_amount(s: str | None) -> float | None:
    """Parse French-formatted amounts: '1 234,56' or '1.234,56' or '1234.56'."""
    if not s:
        return None
    s = s.strip()
    # Remove currency symbols and whitespace
    s = re.sub(r"[€$£\s\u00a0]", "", s)
    if not s:
        return None

    # Detect format: if comma is last separator, it's decimal
    # "1.234,56" => remove dots, replace comma
    if "," in s:
        # Remove thousand separators (dots or spaces before the comma)
        parts = s.rsplit(",", 1)
        integer_part = parts[0].replace(".", "").replace(" ", "")
        decimal_part = parts[1] if len(parts) > 1 else ""
        s = f"{integer_part}.{decimal_part}"
    else:
        # Pure dot format: "1234.56" or "1,234.56" already handled
        s = s.replace(",", "")  # remove thousand commas if any

    s = re.sub(r"[^\d.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


# ── Date parsing ─────────────────────────────────────────────────

FRENCH_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}


def parse_date(s: str | None) -> str | None:
    """Parse a date string (French or standard) and return ISO YYYY-MM-DD or None."""
    if not s:
        return None
    s = s.strip()

    # Try dd/mm/yyyy or dd-mm-yyyy or dd.mm.yyyy
    m = re.match(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})", s)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Try "le 12 janvier 2026" or "12 janvier 2026"
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", s, re.IGNORECASE)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        month = FRENCH_MONTHS.get(month_name)
        if month:
            try:
                return datetime(year, month, day).strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Try yyyy-mm-dd (ISO)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


# ── Text normalization ───────────────────────────────────────────

def normalize_text(raw: str) -> str:
    """Normalize OCR text: fix common artifacts, collapse whitespace."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Remove zero-width chars
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    return text.strip()


def find_value_near_label(text: str, label_patterns: list[str], max_distance: int = 100) -> str | None:
    """Find a value following a label pattern within max_distance chars."""
    for pattern in label_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            # Get text after the match
            after = text[m.end():m.end() + max_distance].strip()
            # Take the first meaningful token(s)
            value_m = re.match(r"[:\s]*(.+?)(?:\n|$)", after)
            if value_m:
                return value_m.group(1).strip()
    return None
