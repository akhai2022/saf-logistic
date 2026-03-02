"""Compliance document extractor — handles KBIS, URSSAF, and INSURANCE documents."""
from __future__ import annotations

import re

from app.modules.ocr.extractors.base import DocType, ExtractionResult
from app.modules.ocr.extractors.utils_text import find_value_near_label, parse_date
from app.modules.ocr.extractors.validators import validate_siren_luhn, validate_siret_luhn


class ComplianceExtractor:
    """Extract metadata from KBIS, URSSAF attestation, or insurance certificates."""

    def extract(self, text: str, lines: list[str], doc_type: DocType = DocType.KBIS) -> ExtractionResult:
        if doc_type == DocType.KBIS:
            return self._extract_kbis(text, lines)
        elif doc_type == DocType.URSSAF:
            return self._extract_urssaf(text, lines)
        elif doc_type == DocType.INSURANCE:
            return self._extract_insurance(text, lines)
        else:
            return self._extract_generic(text, lines)

    # ── KBIS ─────────────────────────────────────────────────────

    def _extract_kbis(self, text: str, lines: list[str]) -> ExtractionResult:
        fields: dict = {}
        confidences: dict[str, float] = {}
        errors: list[str] = []

        # Company name (raison sociale)
        raison = find_value_near_label(text, [
            r"(?:dénomination|denomination|raison\s*sociale)\s*:?",
        ])
        fields["raison_sociale"] = raison
        confidences["raison_sociale"] = 0.8 if raison else 0.0

        # SIREN
        siren = self._extract_siren(text)
        fields["siren"] = siren
        if siren and validate_siren_luhn(siren):
            confidences["siren"] = 0.95
        elif siren:
            confidences["siren"] = 0.5
            errors.append(f"SIREN '{siren}' failed Luhn validation")
        else:
            confidences["siren"] = 0.0

        # SIRET
        siret = self._extract_siret(text)
        fields["siret"] = siret
        if siret and validate_siret_luhn(siret):
            confidences["siret"] = 0.95
        elif siret:
            confidences["siret"] = 0.5
            errors.append(f"SIRET '{siret}' failed Luhn validation")
        else:
            confidences["siret"] = 0.0

        # RCS number
        rcs = find_value_near_label(text, [r"RCS\s*:?", r"R\.C\.S\s*:?"])
        if not rcs:
            m = re.search(r"RCS\s+([A-Z\s]+\d{3}\s?\d{3}\s?\d{3})", text, re.IGNORECASE)
            if m:
                rcs = m.group(1).strip()
        fields["rcs"] = rcs
        confidences["rcs"] = 0.8 if rcs else 0.0

        # Legal form
        forme = find_value_near_label(text, [
            r"(?:forme\s*juridique|forme\s*sociale)\s*:?",
        ])
        fields["forme_juridique"] = forme
        confidences["forme_juridique"] = 0.7 if forme else 0.0

        # Capital social
        capital = find_value_near_label(text, [r"capital\s*(?:social)?\s*:?"])
        fields["capital_social"] = capital
        confidences["capital_social"] = 0.7 if capital else 0.0

        # Date of registration
        date_immat = find_value_near_label(text, [
            r"(?:date\s*d['\u2019]?immatriculation|immatricul[ée]e?\s*le)\s*:?",
        ])
        if date_immat:
            date_immat = parse_date(date_immat)
        fields["date_immatriculation"] = date_immat
        confidences["date_immatriculation"] = 0.7 if date_immat else 0.0

        # Dirigeant / représentant légal
        dirigeant = find_value_near_label(text, [
            r"(?:dirigeant|gérant|président|représentant\s*légal|representant\s*legal)\s*:?",
        ])
        fields["dirigeant"] = dirigeant
        confidences["dirigeant"] = 0.6 if dirigeant else 0.0

        # Address
        adresse = find_value_near_label(text, [
            r"(?:siège\s*social|siege\s*social|adresse)\s*:?",
        ])
        fields["siege_social"] = adresse
        confidences["siege_social"] = 0.6 if adresse else 0.0

        # NAF / APE code
        naf = self._extract_naf(text)
        fields["code_naf"] = naf
        confidences["code_naf"] = 0.8 if naf else 0.0

        # Document date
        doc_date = self._extract_document_date(text)
        fields["document_date"] = doc_date
        confidences["document_date"] = 0.6 if doc_date else 0.0

        return self._finalize(fields, confidences, errors)

    # ── URSSAF ───────────────────────────────────────────────────

    def _extract_urssaf(self, text: str, lines: list[str]) -> ExtractionResult:
        fields: dict = {}
        confidences: dict[str, float] = {}
        errors: list[str] = []

        # Company name
        raison = find_value_near_label(text, [
            r"(?:dénomination|denomination|raison\s*sociale|employeur|entreprise)\s*:?",
        ])
        fields["raison_sociale"] = raison
        confidences["raison_sociale"] = 0.7 if raison else 0.0

        # SIRET
        siret = self._extract_siret(text)
        fields["siret"] = siret
        if siret and validate_siret_luhn(siret):
            confidences["siret"] = 0.95
        elif siret:
            confidences["siret"] = 0.5
            errors.append(f"SIRET '{siret}' failed Luhn validation")
        else:
            confidences["siret"] = 0.0

        # Attestation reference number
        ref = find_value_near_label(text, [
            r"(?:n°\s*de\s*sécurité|référence|reference|n°)\s*:?",
        ])
        fields["reference"] = ref
        confidences["reference"] = 0.7 if ref else 0.0

        # Validity dates
        date_debut = find_value_near_label(text, [
            r"(?:valable\s*(?:à\s*compter|du)|début\s*de\s*validité|du)\s*:?",
        ])
        if date_debut:
            date_debut = parse_date(date_debut)
        fields["date_debut_validite"] = date_debut
        confidences["date_debut_validite"] = 0.7 if date_debut else 0.0

        date_fin = find_value_near_label(text, [
            r"(?:jusqu['\u2019]?au|fin\s*de\s*validité|valable\s*jusqu|expire\s*le)\s*:?",
        ])
        if date_fin:
            date_fin = parse_date(date_fin)
        fields["date_fin_validite"] = date_fin
        confidences["date_fin_validite"] = 0.7 if date_fin else 0.0

        # Issue date
        date_emission = find_value_near_label(text, [
            r"(?:délivré|delivre|établi|etabli|émis|emis)\s*le\s*:?",
            r"date\s*(?:de\s*)?(?:délivrance|delivrance|émission|emission)\s*:?",
        ])
        if date_emission:
            date_emission = parse_date(date_emission)
        fields["date_emission"] = date_emission
        confidences["date_emission"] = 0.6 if date_emission else 0.0

        # Number of employees (effectif)
        effectif = find_value_near_label(text, [
            r"(?:effectif|nombre\s*de\s*salariés|nombre\s*de\s*salaries)\s*:?",
        ])
        fields["effectif"] = effectif
        confidences["effectif"] = 0.5 if effectif else 0.0

        # Document date
        doc_date = self._extract_document_date(text)
        fields["document_date"] = doc_date
        confidences["document_date"] = 0.6 if doc_date else 0.0

        return self._finalize(fields, confidences, errors)

    # ── INSURANCE ────────────────────────────────────────────────

    def _extract_insurance(self, text: str, lines: list[str]) -> ExtractionResult:
        fields: dict = {}
        confidences: dict[str, float] = {}
        errors: list[str] = []

        # Insured company
        assure = find_value_near_label(text, [
            r"(?:assuré|assure|souscripteur|preneur\s*d['\u2019]?assurance)\s*:?",
        ])
        fields["assure"] = assure
        confidences["assure"] = 0.7 if assure else 0.0

        # Insurance company
        assureur = find_value_near_label(text, [
            r"(?:assureur|compagnie\s*d['\u2019]?assurance|société\s*d['\u2019]?assurance)\s*:?",
        ])
        fields["assureur"] = assureur
        confidences["assureur"] = 0.7 if assureur else 0.0

        # Policy number
        police = find_value_near_label(text, [
            r"(?:police|contrat)\s*(?:n°|numero|:)\s*:?",
            r"(?:n°\s*(?:de\s*)?(?:police|contrat))\s*:?",
        ])
        fields["numero_police"] = police
        confidences["numero_police"] = 0.8 if police else 0.0

        # Type of coverage
        garantie = find_value_near_label(text, [
            r"(?:garantie|type\s*(?:de\s*)?couverture|nature\s*(?:du\s*)?risque)\s*:?",
        ])
        if not garantie:
            # Check for common insurance types
            text_lower = text.lower()
            if "responsabilité civile" in text_lower or "responsabilite civile" in text_lower:
                garantie = "Responsabilité Civile Professionnelle"
            elif "marchandises" in text_lower or "transport" in text_lower:
                garantie = "Transport de Marchandises"
        fields["type_garantie"] = garantie
        confidences["type_garantie"] = 0.7 if garantie else 0.0

        # Coverage period
        date_debut = find_value_near_label(text, [
            r"(?:effet|début|prise\s*d['\u2019]?effet|du)\s*:?",
        ])
        if date_debut:
            date_debut = parse_date(date_debut)
        fields["date_debut"] = date_debut
        confidences["date_debut"] = 0.7 if date_debut else 0.0

        date_fin = find_value_near_label(text, [
            r"(?:échéance|echeance|expiration|jusqu['\u2019]?au|au)\s*:?",
        ])
        if date_fin:
            date_fin = parse_date(date_fin)
        fields["date_fin"] = date_fin
        confidences["date_fin"] = 0.7 if date_fin else 0.0

        # Coverage amount (montant de garantie)
        montant = find_value_near_label(text, [
            r"(?:montant\s*(?:de\s*la\s*)?garantie|plafond|capital\s*assuré)\s*:?",
        ])
        fields["montant_garantie"] = montant
        confidences["montant_garantie"] = 0.6 if montant else 0.0

        # Franchise
        franchise = find_value_near_label(text, [r"franchise\s*:?"])
        fields["franchise"] = franchise
        confidences["franchise"] = 0.5 if franchise else 0.0

        # Document date
        doc_date = self._extract_document_date(text)
        fields["document_date"] = doc_date
        confidences["document_date"] = 0.6 if doc_date else 0.0

        return self._finalize(fields, confidences, errors)

    # ── Generic fallback ─────────────────────────────────────────

    def _extract_generic(self, text: str, lines: list[str]) -> ExtractionResult:
        fields: dict = {}
        confidences: dict[str, float] = {}

        doc_date = self._extract_document_date(text)
        fields["document_date"] = doc_date
        confidences["document_date"] = 0.5 if doc_date else 0.0

        siret = self._extract_siret(text)
        if siret:
            fields["siret"] = siret
            confidences["siret"] = 0.7 if validate_siret_luhn(siret) else 0.3

        return self._finalize(fields, confidences, [])

    # ── Helpers ───────────────────────────────────────────────────

    def _extract_siren(self, text: str) -> str | None:
        """Extract 9-digit SIREN from text."""
        raw = find_value_near_label(text, [r"SIREN\s*:?"])
        if raw:
            cleaned = re.sub(r"\s+", "", raw)
            m = re.match(r"(\d{9})", cleaned)
            if m:
                return m.group(1)
        # Regex fallback
        for m in re.finditer(r"\b(\d{3})\s?(\d{3})\s?(\d{3})\b", text):
            candidate = m.group(1) + m.group(2) + m.group(3)
            if validate_siren_luhn(candidate):
                return candidate
        return None

    def _extract_siret(self, text: str) -> str | None:
        """Extract 14-digit SIRET from text."""
        raw = find_value_near_label(text, [r"SIRET\s*:?", r"N°\s*SIRET\s*:?"])
        if raw:
            cleaned = re.sub(r"\s+", "", raw)
            m = re.match(r"(\d{14})", cleaned)
            if m:
                return m.group(1)
        # Regex fallback
        for m in re.finditer(r"\b(\d{3})\s?(\d{3})\s?(\d{3})\s?(\d{5})\b", text):
            candidate = m.group(1) + m.group(2) + m.group(3) + m.group(4)
            if validate_siret_luhn(candidate):
                return candidate
        return None

    def _extract_naf(self, text: str) -> str | None:
        """Extract NAF/APE code (4 digits + 1 letter)."""
        raw = find_value_near_label(text, [r"(?:NAF|APE|code\s*NAF|code\s*APE)\s*:?"])
        if raw:
            m = re.match(r"(\d{4}\s?[A-Z])", raw.upper())
            if m:
                return m.group(1).replace(" ", "")
        # Regex fallback
        m = re.search(r"\b(\d{4}[A-Z])\b", text.upper())
        if m:
            return m.group(1)
        return None

    def _extract_document_date(self, text: str) -> str | None:
        """Extract the document issue/creation date."""
        raw = find_value_near_label(text, [
            r"(?:délivré|delivre|établi|etabli|émis|emis|fait)\s*le\s*:?",
            r"(?:date\s*(?:du\s*document|d['\u2019]?émission|d['\u2019]?emission))\s*:?",
            r"(?:en\s*date\s*du)\s*:?",
        ])
        if raw:
            return parse_date(raw)
        return None

    def _finalize(
        self, fields: dict, confidences: dict[str, float], errors: list[str],
    ) -> ExtractionResult:
        non_zero = [v for v in confidences.values() if v > 0]
        global_confidence = round(sum(non_zero) / max(len(non_zero), 1), 4)
        return ExtractionResult(
            extracted_fields=fields,
            field_confidences=confidences,
            global_confidence=global_confidence,
            errors=errors,
        )
