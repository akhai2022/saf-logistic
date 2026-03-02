"""Unit tests for OCR extractors — classifier, validators, text utils, and typed extractors."""
from __future__ import annotations

import pytest

from app.modules.ocr.extractors.base import DocType
from app.modules.ocr.extractors.classifier import classify_document
from app.modules.ocr.extractors.validators import (
    check_totals_consistency,
    extract_bic_from_text,
    extract_iban_from_text,
    mask_iban,
    validate_bic,
    validate_iban,
    validate_siren_luhn,
    validate_siret_luhn,
)
from app.modules.ocr.extractors.utils_text import (
    normalize_text,
    parse_date,
    parse_french_amount,
)
from app.modules.ocr.extractors.invoice_extractor import InvoiceExtractor
from app.modules.ocr.extractors.bank_rib_extractor import BankRibExtractor
from app.modules.ocr.extractors.compliance_extractor import ComplianceExtractor


# ── Validators ───────────────────────────────────────────────────

class TestValidateIban:
    def test_valid_french_iban(self):
        assert validate_iban("FR7630006000011234567890189") is True

    def test_valid_german_iban(self):
        assert validate_iban("DE89370400440532013000") is True

    def test_invalid_iban_bad_checksum(self):
        assert validate_iban("FR7630006000011234567890100") is False

    def test_invalid_iban_too_short(self):
        assert validate_iban("FR76300") is False

    def test_iban_with_spaces(self):
        assert validate_iban("FR76 3000 6000 0112 3456 7890 189") is True


class TestValidateBic:
    def test_valid_bic_8(self):
        assert validate_bic("BNPAFRPP") is True

    def test_valid_bic_11(self):
        assert validate_bic("BNPAFRPPXXX") is True

    def test_invalid_bic_wrong_length(self):
        assert validate_bic("BNPAF") is False

    def test_invalid_bic_numbers_in_wrong_place(self):
        assert validate_bic("1234FRPP") is False


class TestValidateSiren:
    def test_valid_siren(self):
        # Known valid SIREN: 443 061 841 (Société Générale)
        assert validate_siren_luhn("443061841") is True

    def test_invalid_siren(self):
        assert validate_siren_luhn("123456789") is False

    def test_wrong_length(self):
        assert validate_siren_luhn("12345") is False


class TestValidateSiret:
    def test_valid_siret(self):
        # SIRET = SIREN + NIC (443061841 + 00019)
        assert validate_siret_luhn("44306184100019") is True

    def test_invalid_siret(self):
        assert validate_siret_luhn("12345678901234") is False

    def test_wrong_length(self):
        assert validate_siret_luhn("1234567890") is False


class TestTotalsConsistency:
    def test_consistent(self):
        ok, msg = check_totals_consistency(1000.0, 200.0, 1200.0)
        assert ok is True
        assert msg is None

    def test_inconsistent(self):
        ok, msg = check_totals_consistency(1000.0, 200.0, 1500.0)
        assert ok is False
        assert "inconsistent" in msg.lower()

    def test_none_values(self):
        ok, msg = check_totals_consistency(None, 200.0, 1200.0)
        assert ok is True  # Can't check, not an error


class TestExtractIban:
    def test_extract_from_text(self):
        text = "Votre IBAN: FR76 3000 6000 0112 3456 7890 189 BIC: BNPAFRPP"
        iban = extract_iban_from_text(text)
        assert iban == "FR7630006000011234567890189"

    def test_no_iban(self):
        assert extract_iban_from_text("No iban here") is None


class TestExtractBic:
    def test_extract_from_text(self):
        text = "BIC: BNPAFRPP code banque"
        bic = extract_bic_from_text(text)
        assert bic == "BNPAFRPP"


class TestMaskIban:
    def test_mask(self):
        assert mask_iban("FR7630006000011234567890189") == "FR*********************0189"

    def test_mask_none(self):
        assert mask_iban(None) is None

    def test_mask_short(self):
        assert mask_iban("FR76") == "FR76"


# ── Text utilities ───────────────────────────────────────────────

class TestParseFrenchAmount:
    def test_comma_decimal(self):
        assert parse_french_amount("1 234,56") == 1234.56

    def test_dot_thousand_comma_decimal(self):
        assert parse_french_amount("1.234,56") == 1234.56

    def test_pure_dot_decimal(self):
        assert parse_french_amount("1234.56") == 1234.56

    def test_with_euro_sign(self):
        assert parse_french_amount("1 234,56 €") == 1234.56

    def test_none(self):
        assert parse_french_amount(None) is None

    def test_empty(self):
        assert parse_french_amount("") is None


class TestParseDate:
    def test_slash_format(self):
        assert parse_date("15/01/2026") == "2026-01-15"

    def test_dash_format(self):
        assert parse_date("15-01-2026") == "2026-01-15"

    def test_dot_format(self):
        assert parse_date("15.01.2026") == "2026-01-15"

    def test_two_digit_year(self):
        assert parse_date("15/01/26") == "2026-01-15"

    def test_french_month(self):
        assert parse_date("12 janvier 2026") == "2026-01-12"

    def test_french_month_with_le(self):
        assert parse_date("le 12 janvier 2026") == "2026-01-12"

    def test_iso_format(self):
        assert parse_date("2026-01-15") == "2026-01-15"

    def test_none(self):
        assert parse_date(None) is None


class TestNormalizeText:
    def test_collapse_spaces(self):
        assert normalize_text("hello   world") == "hello world"

    def test_remove_zero_width(self):
        assert normalize_text("hello\u200bworld") == "helloworld"

    def test_crlf(self):
        assert normalize_text("line1\r\nline2") == "line1\nline2"


# ── Classifier ───────────────────────────────────────────────────

class TestClassifier:
    def test_classify_invoice(self):
        text = """
        FACTURE N° FA-2026-001
        Date de facture: 15/01/2026
        Total HT: 1 234,56 €
        TVA 20%: 246,91 €
        Total TTC: 1 481,47 €
        Net à payer: 1 481,47 €
        """
        result = classify_document(text)
        assert result.doc_type == DocType.INVOICE
        assert result.confidence > 0.5

    def test_classify_bank_rib(self):
        text = """
        RELEVE D'IDENTITE BANCAIRE
        Titulaire du compte: SARL TRANSPORT EXPRESS
        IBAN: FR76 3000 6000 0112 3456 7890 189
        BIC: BNPAFRPP
        Code banque: 30006 Code guichet: 00001
        Domiciliation: BNP PARIBAS PARIS OPERA
        """
        result = classify_document(text)
        assert result.doc_type == DocType.BANK_RIB
        assert result.confidence > 0.5

    def test_classify_kbis(self):
        text = """
        EXTRAIT KBIS
        Greffe du Tribunal de Commerce de Paris
        RCS PARIS 443 061 841
        Dénomination: SOCIETE GENERALE
        Forme juridique: SA
        Capital social: 1 009 897 173,75 EUR
        Immatriculation: 29/01/1864
        """
        result = classify_document(text)
        assert result.doc_type == DocType.KBIS
        assert result.confidence > 0.5

    def test_classify_urssaf(self):
        text = """
        ATTESTATION DE VIGILANCE
        URSSAF Ile-de-France
        Article L.243-15 du Code de la Sécurité Sociale
        Cotisations sociales à jour
        Obligations sociales respectées
        """
        result = classify_document(text)
        assert result.doc_type == DocType.URSSAF
        assert result.confidence > 0.5

    def test_classify_insurance(self):
        text = """
        ATTESTATION D'ASSURANCE
        Responsabilité Civile Professionnelle
        Police d'assurance n° 123456789
        Assureur: AXA France
        Couverture du 01/01/2026 au 31/12/2026
        """
        result = classify_document(text)
        assert result.doc_type == DocType.INSURANCE
        assert result.confidence > 0.5

    def test_classify_unknown(self):
        text = "Just some random text without any document markers."
        result = classify_document(text)
        assert result.doc_type == DocType.UNKNOWN


# ── Invoice Extractor ────────────────────────────────────────────

class TestInvoiceExtractor:
    def test_extract_basic_invoice(self):
        text = """TRANSPORT EXPRESS SARL
FACTURE N° FA-2026-042
Date: 15/01/2026
Total HT: 1 500,00 €
TVA 20%: 300,00 €
Total TTC: 1 800,00 €"""
        lines = text.strip().split("\n")
        result = InvoiceExtractor().extract(text, lines)

        assert result.extracted_fields["invoice_number"] is not None
        assert result.extracted_fields["total_ht"] == 1500.0
        assert result.extracted_fields["tva"] == 300.0
        assert result.extracted_fields["total_ttc"] == 1800.0
        assert result.global_confidence > 0
        assert len(result.errors) == 0  # totals are consistent

    def test_inconsistent_totals(self):
        text = """FACTURE N° FA-001
Total HT: 1 000,00 €
TVA: 200,00 €
Total TTC: 1 500,00 €"""
        lines = text.strip().split("\n")
        result = InvoiceExtractor().extract(text, lines)
        assert len(result.errors) > 0
        assert "inconsistent" in result.errors[0].lower()


# ── Bank RIB Extractor ───────────────────────────────────────────

class TestBankRibExtractor:
    def test_extract_rib(self):
        text = """RELEVE D'IDENTITE BANCAIRE
Titulaire: SARL TRANSPORT EXPRESS
IBAN: FR76 3000 6000 0112 3456 7890 189
BIC: BNPAFRPP
Domiciliation: BNP PARIBAS PARIS
30006 00001 12345678901 89"""
        lines = text.strip().split("\n")
        result = BankRibExtractor().extract(text, lines)

        assert result.extracted_fields["iban"] == "FR7630006000011234567890189"
        assert result.extracted_fields["bic"] == "BNPAFRPP"
        assert result.field_confidences["iban"] >= 0.9
        assert result.field_confidences["bic"] >= 0.9
        assert result.global_confidence > 0.5


# ── Compliance Extractor ─────────────────────────────────────────

class TestComplianceExtractor:
    def test_extract_kbis(self):
        text = """EXTRAIT KBIS
Dénomination: TRANSPORT EXPRESS SARL
SIREN: 443 061 841
Forme juridique: SARL
Capital social: 50 000 EUR
RCS PARIS 443 061 841"""
        lines = text.strip().split("\n")
        result = ComplianceExtractor().extract(text, lines, DocType.KBIS)

        assert result.extracted_fields["raison_sociale"] is not None
        assert result.extracted_fields["siren"] == "443061841"
        assert result.field_confidences["siren"] >= 0.9  # valid Luhn
        assert result.global_confidence > 0

    def test_extract_urssaf(self):
        text = """ATTESTATION DE VIGILANCE
URSSAF
Employeur: TRANSPORT EXPRESS SARL
SIRET: 44306184100019
Valable jusqu'au 15/06/2026"""
        lines = text.strip().split("\n")
        result = ComplianceExtractor().extract(text, lines, DocType.URSSAF)

        assert result.extracted_fields["siret"] == "44306184100019"
        assert result.global_confidence > 0

    def test_extract_insurance(self):
        text = """ATTESTATION D'ASSURANCE
Responsabilité Civile Professionnelle
Assuré: TRANSPORT EXPRESS SARL
Assureur: AXA France
Contrat n°: POL-2026-001
Du 01/01/2026 au 31/12/2026"""
        lines = text.strip().split("\n")
        result = ComplianceExtractor().extract(text, lines, DocType.INSURANCE)

        assert result.extracted_fields["assure"] is not None
        assert result.global_confidence > 0
