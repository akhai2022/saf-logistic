"""Validators for IBAN, BIC, SIREN, totals consistency, etc."""
from __future__ import annotations

import re


def validate_iban(iban: str) -> bool:
    """Validate IBAN using ISO 13616 mod-97 algorithm."""
    cleaned = re.sub(r"[^A-Z0-9]", "", iban.upper())
    if len(cleaned) < 15 or len(cleaned) > 34:
        return False
    # Move first 4 chars to end
    rearranged = cleaned[4:] + cleaned[:4]
    # Convert letters to digits (A=10..Z=35)
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - ord("A") + 10)
    return int(numeric) % 97 == 1


def validate_bic(bic: str) -> bool:
    """Validate BIC/SWIFT code format (ISO 9362)."""
    cleaned = re.sub(r"\s+", "", bic.upper())
    return bool(re.match(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$", cleaned))


def validate_siren_luhn(siren: str) -> bool:
    """Validate SIREN (9 digits) using Luhn algorithm."""
    cleaned = re.sub(r"\s+", "", siren)
    if not re.match(r"^\d{9}$", cleaned):
        return False
    total = 0
    for i, ch in enumerate(cleaned):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def validate_siret_luhn(siret: str) -> bool:
    """Validate SIRET (14 digits) using Luhn algorithm."""
    cleaned = re.sub(r"\s+", "", siret)
    if not re.match(r"^\d{14}$", cleaned):
        return False
    total = 0
    for i, ch in enumerate(cleaned):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def check_totals_consistency(
    total_ht: float | None, total_tva: float | None, total_ttc: float | None,
    tolerance: float = 0.05,
) -> tuple[bool, str | None]:
    """Check if HT + TVA ≈ TTC within tolerance.

    Returns (is_consistent, error_message).
    """
    if total_ht is None or total_tva is None or total_ttc is None:
        return True, None  # can't check, not an error
    expected_ttc = total_ht + total_tva
    diff = abs(expected_ttc - total_ttc)
    relative = diff / max(abs(total_ttc), 0.01)
    if relative > tolerance:
        return False, f"Totals inconsistent: HT({total_ht:.2f}) + TVA({total_tva:.2f}) = {expected_ttc:.2f} but TTC = {total_ttc:.2f}"
    return True, None


def extract_iban_from_text(text: str) -> str | None:
    """Find and normalize an IBAN in text."""
    # Match IBAN-like patterns: 2 letters + 2 digits + up to 30 alphanumerics with optional spaces
    pattern = r"\b([A-Z]{2}\s?\d{2}[\s]?(?:[A-Z0-9]{4}[\s]?){3,8}[A-Z0-9]{0,4})\b"
    for m in re.finditer(pattern, text.upper()):
        candidate = re.sub(r"\s+", "", m.group(1))
        if validate_iban(candidate):
            return candidate
    return None


_BIC_FALSE_POSITIVES = {
    "IDENTITE", "BANCAIRE", "RELEVE", "DOMICILI", "TITULAIRE",
    "ATTESTAT", "ASSURANCE", "GARANTIE", "FACTURE", "COMMERCE",
    "TRIBUNAL", "IMMATRICU", "FORMULAIR", "DOCUMENT", "CERTIFIA",
    "OBLIGATOI", "EXPLOITAT", "TRANSPORT", "PRESTATAI",
}


def extract_bic_from_text(text: str) -> str | None:
    """Find a BIC/SWIFT code in text."""
    pattern = r"\b([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b"
    for m in re.finditer(pattern, text.upper()):
        candidate = m.group(1)
        if candidate in _BIC_FALSE_POSITIVES:
            continue
        if validate_bic(candidate):
            return candidate
    return None


def mask_iban(iban: str | None) -> str | None:
    """Mask IBAN for display: show country code + last 4 only."""
    if not iban or len(iban) < 6:
        return iban
    return iban[:2] + "*" * (len(iban) - 6) + iban[-4:]
