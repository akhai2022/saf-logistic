"""French business-rule validators for Module B."""
from __future__ import annotations

import re


def _luhn_check(digits: str) -> bool:
    """Verify a digit string passes the Luhn algorithm."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def validate_siren(siren: str) -> bool:
    """9 digits + Luhn."""
    siren = siren.strip()
    if not re.fullmatch(r"\d{9}", siren):
        return False
    return _luhn_check(siren)


def validate_siret(siret: str) -> bool:
    """14 digits, first 9 = valid SIREN, full 14 passes Luhn."""
    siret = siret.strip()
    if not re.fullmatch(r"\d{14}", siret):
        return False
    if not validate_siren(siret[:9]):
        return False
    return _luhn_check(siret)


def validate_tva_intracom(tva: str) -> bool:
    """FR + 2 check digits + 9 digit SIREN.
    Key = (12 + 3 * (SIREN mod 97)) mod 97.
    """
    tva = tva.strip().upper().replace(" ", "")
    m = re.fullmatch(r"FR(\d{2})(\d{9})", tva)
    if not m:
        return False
    check = int(m.group(1))
    siren = int(m.group(2))
    expected = (12 + 3 * (siren % 97)) % 97
    return check == expected


def validate_nir(nir: str) -> bool:
    """French social security number: 13 digits + 2-digit key.
    Key = 97 - (first_13 mod 97).
    Corsica: handle 2A/2B department codes.
    """
    nir = nir.strip().replace(" ", "")
    if len(nir) != 15:
        return False
    # Handle Corsica (2A → 19, 2B → 18 for modulo computation)
    nir_for_mod = nir[:13]
    if nir[5:7] == "2A":
        nir_for_mod = nir[:5] + "19" + nir[7:13]
    elif nir[5:7] == "2B":
        nir_for_mod = nir[:5] + "18" + nir[7:13]

    if not re.fullmatch(r"\d{13}", nir_for_mod):
        return False
    if not re.fullmatch(r"\d{2}", nir[13:15]):
        return False

    base = int(nir_for_mod)
    key = int(nir[13:15])
    return key == 97 - (base % 97)


def validate_iban(iban: str) -> bool:
    """ISO 13616 modulo 97 check."""
    iban = iban.strip().upper().replace(" ", "")
    if len(iban) < 5:
        return False
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", iban):
        return False
    # Move first 4 chars to end
    rearranged = iban[4:] + iban[:4]
    # Replace letters: A=10, B=11, ..., Z=35
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - ord("A") + 10)
    return int(numeric) % 97 == 1


def validate_french_plate(plate: str) -> bool:
    """SIV format: AA-123-BB or FNI format: 1234 AB 69."""
    plate = plate.strip().upper()
    # SIV: AA-123-BB
    if re.fullmatch(r"[A-Z]{2}-\d{3}-[A-Z]{2}", plate):
        return True
    # FNI: 1234 AB 69 (or without spaces)
    normalized = plate.replace(" ", "").replace("-", "")
    if re.fullmatch(r"\d{1,4}[A-Z]{1,3}\d{2,3}", normalized):
        return True
    return False


def validate_vin(vin: str) -> bool:
    """17 alphanumeric chars, excluding I, O, Q."""
    vin = vin.strip().upper()
    if len(vin) != 17:
        return False
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin):
        return False
    return True


def validate_code_postal(cp: str) -> bool:
    """French postal code: 5 digits, department 01-95 or 97x (DOM-TOM)."""
    cp = cp.strip()
    if not re.fullmatch(r"\d{5}", cp):
        return False
    dept = int(cp[:2])
    if dept == 0:
        return False
    if dept <= 95:
        return True
    # DOM-TOM: 97x
    if cp[:3] in ("971", "972", "973", "974", "976"):
        return True
    return False
