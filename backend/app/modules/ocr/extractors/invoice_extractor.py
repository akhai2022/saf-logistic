"""Invoice field extractor — extracts supplier, amounts, dates, references."""
from __future__ import annotations

import re

from app.modules.ocr.extractors.base import ExtractionResult
from app.modules.ocr.extractors.utils_text import (
    find_value_near_label,
    parse_date,
    parse_french_amount,
)
from app.modules.ocr.extractors.validators import (
    check_totals_consistency,
    extract_iban_from_text,
)


class InvoiceExtractor:
    """Extract structured fields from invoice text."""

    def extract(self, text: str, lines: list[str]) -> ExtractionResult:
        fields: dict = {}
        confidences: dict[str, float] = {}
        errors: list[str] = []

        # ── Supplier name ────────────────────────────────────────
        supplier = self._extract_supplier(text, lines)
        fields["supplier_name"] = supplier
        confidences["supplier_name"] = 0.7 if supplier else 0.0

        # ── Invoice number ───────────────────────────────────────
        inv_num = self._extract_invoice_number(text)
        fields["invoice_number"] = inv_num
        confidences["invoice_number"] = 0.8 if inv_num else 0.0

        # ── Invoice date ─────────────────────────────────────────
        inv_date = self._extract_invoice_date(text)
        fields["invoice_date"] = inv_date
        confidences["invoice_date"] = 0.8 if inv_date else 0.0

        # ── Due date ─────────────────────────────────────────────
        due_date = self._extract_due_date(text)
        fields["due_date"] = due_date
        confidences["due_date"] = 0.7 if due_date else 0.0

        # ── Amounts ──────────────────────────────────────────────
        total_ht = self._extract_amount(text, [
            r"total\s*h\.?t\.?",
            r"montant\s*h\.?t\.?",
            r"sous[\s\-]?total",
        ])
        fields["total_ht"] = total_ht
        confidences["total_ht"] = 0.85 if total_ht is not None else 0.0

        tva = self._extract_amount(text, [
            r"t\.?v\.?a\.?\s*(?:\d+[,.]?\d*\s*%)?",
            r"taxe",
            r"montant\s*(?:de\s*la\s*)?t\.?v\.?a",
        ])
        fields["tva"] = tva
        confidences["tva"] = 0.8 if tva is not None else 0.0

        total_ttc = self._extract_amount(text, [
            r"total\s*t\.?t\.?c\.?",
            r"montant\s*t\.?t\.?c\.?",
            r"net\s*[àa]\s*payer",
            r"total\s*général",
            r"total\s*general",
        ])
        fields["total_ttc"] = total_ttc
        confidences["total_ttc"] = 0.85 if total_ttc is not None else 0.0

        # ── TVA rate ─────────────────────────────────────────────
        tva_rate = self._extract_tva_rate(text)
        fields["tva_rate"] = tva_rate
        confidences["tva_rate"] = 0.7 if tva_rate is not None else 0.0

        # ── Purchase order reference ─────────────────────────────
        po_ref = find_value_near_label(text, [
            r"(?:bon\s*de\s*commande|b\.?c\.?|purchase\s*order|p\.?o\.?)\s*(?:n°|:)?",
        ])
        fields["purchase_order"] = po_ref
        confidences["purchase_order"] = 0.6 if po_ref else 0.0

        # ── IBAN (if present on invoice) ─────────────────────────
        iban = extract_iban_from_text(text)
        if iban:
            fields["iban"] = iban
            confidences["iban"] = 0.9

        # ── Totals consistency check ─────────────────────────────
        consistent, err_msg = check_totals_consistency(total_ht, tva, total_ttc)
        if not consistent and err_msg:
            errors.append(err_msg)

        # ── Global confidence ────────────────────────────────────
        non_zero = [v for v in confidences.values() if v > 0]
        global_confidence = round(sum(non_zero) / max(len(non_zero), 1), 4)

        return ExtractionResult(
            extracted_fields=fields,
            field_confidences=confidences,
            global_confidence=global_confidence,
            errors=errors,
        )

    def _extract_supplier(self, text: str, lines: list[str]) -> str | None:
        """Extract supplier name — usually first prominent uppercase text."""
        # Try the first few lines for a company-name-looking string
        for line in lines[:10]:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            # Skip lines that look like dates, amounts, or labels
            if re.match(r"^\d", line):
                continue
            if re.match(r"(?i)^(facture|invoice|date|total|tva|page|n°|ref)", line):
                continue
            # Uppercase-dominant line with 3+ chars is likely a company name
            upper_ratio = sum(1 for c in line if c.isupper()) / max(len(line.replace(" ", "")), 1)
            if upper_ratio > 0.5 and len(line) <= 60:
                return line
        return None

    def _extract_invoice_number(self, text: str) -> str | None:
        patterns = [
            r"(?:facture|invoice)\s*(?:n°|n°|no|num|#|:)\s*([A-Z0-9][\w\-/]{2,30})",
            r"(?:n°|n°|no|num)\s*(?:facture|invoice)?\s*:?\s*([A-Z0-9][\w\-/]{2,30})",
            r"(?:FA|INV|FCT)[\-/]?\d{4,}",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1).strip() if m.lastindex else m.group(0).strip()
        return None

    def _extract_invoice_date(self, text: str) -> str | None:
        # Try label-based extraction first
        raw = find_value_near_label(text, [
            r"date\s*(?:de\s*)?(?:facture|facturation|émission|emission)",
            r"date\s*:",
            r"(?:facturé|facture|émis|emis)\s*le",
        ])
        if raw:
            parsed = parse_date(raw)
            if parsed:
                return parsed

        # Fallback: first date-like pattern in text
        m = re.search(r"\b(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})\b", text)
        if m:
            return parse_date(m.group(1))
        return None

    def _extract_due_date(self, text: str) -> str | None:
        raw = find_value_near_label(text, [
            r"(?:date\s*d['\u2019]?échéance|date\s*d['\u2019]?echeance|échéance|echeance)",
            r"(?:date\s*limite\s*(?:de\s*)?paiement)",
            r"(?:à\s*payer\s*(?:avant|le))",
        ])
        if raw:
            return parse_date(raw)
        return None

    def _extract_amount(self, text: str, label_patterns: list[str]) -> float | None:
        """Extract a monetary amount near a label."""
        for pattern in label_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                # Look for amount after the label
                after = text[m.end():m.end() + 80]
                amt_m = re.search(r"[:\s]*([\d\s]+[,\.]\d{2})\s*[€E]?", after)
                if amt_m:
                    return parse_french_amount(amt_m.group(1))
                # Try integer amount
                amt_m = re.search(r"[:\s]*(\d[\d\s]*)\s*[€E]", after)
                if amt_m:
                    return parse_french_amount(amt_m.group(1))
        return None

    def _extract_tva_rate(self, text: str) -> float | None:
        """Extract TVA rate percentage."""
        patterns = [
            r"(?:tva|t\.v\.a\.?)\s*(?:à|a|:)?\s*(\d{1,2}[,.]?\d{0,2})\s*%",
            r"(\d{1,2}[,.]?\d{0,2})\s*%\s*(?:tva|t\.v\.a)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                rate_str = m.group(1).replace(",", ".")
                try:
                    rate = float(rate_str)
                    if rate in (5.5, 10.0, 20.0, 0.0, 2.1):  # valid French TVA rates
                        return rate
                except ValueError:
                    pass
        return None
