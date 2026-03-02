"""Bank RIB extractor — extracts IBAN, BIC, bank name, account holder."""
from __future__ import annotations

import re

from app.modules.ocr.extractors.base import ExtractionResult
from app.modules.ocr.extractors.utils_text import find_value_near_label
from app.modules.ocr.extractors.validators import (
    extract_bic_from_text,
    extract_iban_from_text,
    validate_bic,
    validate_iban,
)


class BankRibExtractor:
    """Extract structured fields from a bank RIB document."""

    def extract(self, text: str, lines: list[str]) -> ExtractionResult:
        fields: dict = {}
        confidences: dict[str, float] = {}
        errors: list[str] = []

        # ── IBAN ─────────────────────────────────────────────────
        iban = extract_iban_from_text(text)
        if iban:
            fields["iban"] = iban
            confidences["iban"] = 0.95
        else:
            # Try label-based extraction
            raw_iban = find_value_near_label(text, [r"IBAN\s*:?", r"I\.B\.A\.N"])
            if raw_iban:
                cleaned = re.sub(r"\s+", "", raw_iban)
                if validate_iban(cleaned):
                    fields["iban"] = cleaned
                    confidences["iban"] = 0.90
                else:
                    fields["iban"] = cleaned
                    confidences["iban"] = 0.4
                    errors.append(f"IBAN '{cleaned}' failed mod-97 validation")
            else:
                fields["iban"] = None
                confidences["iban"] = 0.0

        # ── BIC / SWIFT ──────────────────────────────────────────
        bic = extract_bic_from_text(text)
        if bic:
            fields["bic"] = bic
            confidences["bic"] = 0.95
        else:
            raw_bic = find_value_near_label(text, [
                r"(?:BIC|SWIFT|B\.I\.C)\s*:?",
            ])
            if raw_bic:
                cleaned = re.sub(r"\s+", "", raw_bic.upper())
                # Take first word if multiple
                cleaned = cleaned.split()[0] if " " in raw_bic else cleaned
                if validate_bic(cleaned):
                    fields["bic"] = cleaned
                    confidences["bic"] = 0.90
                else:
                    fields["bic"] = cleaned
                    confidences["bic"] = 0.4
                    errors.append(f"BIC '{cleaned}' failed format validation")
            else:
                fields["bic"] = None
                confidences["bic"] = 0.0

        # ── Bank name ────────────────────────────────────────────
        bank_name = self._extract_bank_name(text, lines)
        fields["bank_name"] = bank_name
        confidences["bank_name"] = 0.7 if bank_name else 0.0

        # ── Account holder (titulaire) ───────────────────────────
        holder = find_value_near_label(text, [
            r"(?:titulaire|nom\s*du\s*(?:titulaire|compte|client))\s*:?",
            r"(?:bénéficiaire|beneficiaire)\s*:?",
        ])
        fields["account_holder"] = holder
        confidences["account_holder"] = 0.75 if holder else 0.0

        # ── Domiciliation ────────────────────────────────────────
        domiciliation = find_value_near_label(text, [
            r"domiciliation\s*:?",
            r"agence\s*:?",
            r"(?:établissement|etablissement)\s*:?",
        ])
        fields["domiciliation"] = domiciliation
        confidences["domiciliation"] = 0.6 if domiciliation else 0.0

        # ── RIB key components (code banque, guichet, compte, clé) ──
        rib = self._extract_rib_components(text)
        if rib:
            fields["code_banque"] = rib["code_banque"]
            fields["code_guichet"] = rib["code_guichet"]
            fields["numero_compte"] = rib["numero_compte"]
            fields["cle_rib"] = rib["cle_rib"]
            confidences["code_banque"] = 0.85
            confidences["code_guichet"] = 0.85
            confidences["numero_compte"] = 0.85
            confidences["cle_rib"] = 0.85

        # ── Global confidence ────────────────────────────────────
        non_zero = [v for v in confidences.values() if v > 0]
        global_confidence = round(sum(non_zero) / max(len(non_zero), 1), 4)

        return ExtractionResult(
            extracted_fields=fields,
            field_confidences=confidences,
            global_confidence=global_confidence,
            errors=errors,
        )

    def _extract_bank_name(self, text: str, lines: list[str]) -> str | None:
        """Extract bank name from text."""
        # Try label-based
        name = find_value_near_label(text, [
            r"(?:banque|établissement bancaire|etablissement bancaire)\s*:?",
        ])
        if name:
            return name

        # Known French bank names
        known_banks = [
            "CREDIT AGRICOLE", "CREDIT MUTUEL", "SOCIETE GENERALE",
            "BNP PARIBAS", "BANQUE POPULAIRE", "CAISSE D'EPARGNE",
            "CAISSE D EPARGNE", "LA BANQUE POSTALE", "LCL",
            "CREDIT LYONNAIS", "HSBC", "CIC", "BRED",
            "BANQUE DE FRANCE", "CREDIT COOPERATIF",
        ]
        text_upper = text.upper()
        for bank in known_banks:
            if bank in text_upper:
                return bank.title()
        return None

    def _extract_rib_components(self, text: str) -> dict | None:
        """Extract traditional RIB components: code banque (5), guichet (5), compte (11), clé (2)."""
        # Pattern: 5 digits - 5 digits - 11 digits - 2 digits
        m = re.search(
            r"\b(\d{5})\s+(\d{5})\s+(\d{11})\s+(\d{2})\b",
            text,
        )
        if m:
            return {
                "code_banque": m.group(1),
                "code_guichet": m.group(2),
                "numero_compte": m.group(3),
                "cle_rib": m.group(4),
            }

        # Try label-based extraction for each component
        code_banque = find_value_near_label(text, [r"code\s*banque\s*:?"])
        code_guichet = find_value_near_label(text, [r"code\s*guichet\s*:?"])
        num_compte = find_value_near_label(text, [r"(?:n°?\s*de\s*)?compte\s*:?"])
        cle = find_value_near_label(text, [r"cl[ée]\s*(?:rib|r\.i\.b)?\s*:?"])

        if code_banque and code_guichet:
            return {
                "code_banque": re.sub(r"\D", "", code_banque)[:5],
                "code_guichet": re.sub(r"\D", "", code_guichet)[:5],
                "numero_compte": re.sub(r"\D", "", num_compte)[:11] if num_compte else None,
                "cle_rib": re.sub(r"\D", "", cle)[:2] if cle else None,
            }

        return None
