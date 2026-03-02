"""Document type classifier using keyword/pattern scoring heuristics."""
from __future__ import annotations

import re

from app.modules.ocr.extractors.base import ClassificationResult, DocType


# ── Keyword sets per doc type ────────────────────────────────────
_KEYWORDS: dict[DocType, list[tuple[str, float]]] = {
    DocType.BANK_RIB: [
        ("iban", 3.0),
        ("bic", 2.5),
        ("swift", 2.5),
        ("rib", 2.0),
        ("releve d'identite bancaire", 4.0),
        ("relevé d'identité bancaire", 4.0),
        ("domiciliation", 1.5),
        ("titulaire du compte", 2.0),
        ("code banque", 2.0),
        ("code guichet", 2.0),
        ("n° de compte", 1.5),
        ("clé rib", 2.0),
        ("clé r.i.b", 2.0),
    ],
    DocType.INVOICE: [
        ("facture", 3.0),
        ("invoice", 2.0),
        ("total ht", 2.5),
        ("total h.t", 2.5),
        ("total ttc", 2.5),
        ("total t.t.c", 2.5),
        ("montant ht", 2.0),
        ("montant ttc", 2.0),
        ("tva", 1.5),
        ("t.v.a", 1.5),
        ("net à payer", 3.0),
        ("net a payer", 3.0),
        ("date de facture", 2.0),
        ("échéance", 1.0),
        ("echeance", 1.0),
        ("bon de commande", 1.0),
        ("n° facture", 2.5),
        ("numéro de facture", 2.5),
    ],
    DocType.KBIS: [
        ("kbis", 5.0),
        ("k bis", 5.0),
        ("extrait kbis", 5.0),
        ("extrait k bis", 5.0),
        ("registre du commerce", 3.0),
        ("rcs", 2.0),
        ("greffe", 2.0),
        ("tribunal de commerce", 2.5),
        ("immatriculation", 1.5),
        ("forme juridique", 2.0),
        ("capital social", 1.5),
        ("objet social", 1.5),
        ("dirigeant", 1.0),
        ("gérant", 1.0),
        ("président", 0.5),
    ],
    DocType.URSSAF: [
        ("urssaf", 5.0),
        ("attestation de vigilance", 5.0),
        ("vigilance", 2.0),
        ("sécurité sociale", 1.5),
        ("securite sociale", 1.5),
        ("cotisations sociales", 2.0),
        ("obligations sociales", 2.0),
        ("l.243-15", 3.0),
        ("l243-15", 3.0),
        ("code de la sécurité sociale", 2.0),
        ("code du travail", 1.0),
    ],
    DocType.INSURANCE: [
        ("attestation d'assurance", 5.0),
        ("attestation d assurance", 5.0),
        ("responsabilité civile", 3.0),
        ("responsabilite civile", 3.0),
        ("rc professionnelle", 3.0),
        ("police d'assurance", 2.5),
        ("police d assurance", 2.5),
        ("compagnie d'assurance", 2.0),
        ("assureur", 1.5),
        ("garantie", 1.0),
        ("sinistre", 1.0),
        ("prime d'assurance", 2.0),
        ("couverture", 1.0),
        ("franchise", 0.5),
    ],
}

# Regex patterns that boost confidence per doc type
_REGEX_BOOSTS: dict[DocType, list[tuple[str, float]]] = {
    DocType.BANK_RIB: [
        # IBAN pattern (FR76 XXXX ...)
        (r"\b[A-Z]{2}\s?\d{2}[\s]?(?:[A-Z0-9]{4}[\s]?){3,8}[A-Z0-9]{0,4}\b", 3.0),
        # BIC pattern
        (r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b", 2.0),
        # Code banque / guichet / compte / clé pattern
        (r"\b\d{5}\s+\d{5}\s+\d{11}\s+\d{2}\b", 4.0),
    ],
    DocType.INVOICE: [
        # Amount patterns like "1 234,56 €"
        (r"\d[\d\s]*[,\.]\d{2}\s*[€E]", 1.5),
        # TVA rate "20%" or "20,00%"
        (r"\b(?:5[,.]50|10[,.]00|20[,.]00)\s*%", 1.5),
        # Invoice number pattern
        (r"(?:FA|INV|FCT)[\-/]?\d{4,}", 2.0),
    ],
    DocType.KBIS: [
        # RCS number
        (r"\bRCS\s+[A-Z\s]+\d{3}\s?\d{3}\s?\d{3}\b", 3.0),
        # SIREN / SIRET
        (r"\b\d{3}\s?\d{3}\s?\d{3}(?:\s?\d{5})?\b", 1.0),
    ],
    DocType.URSSAF: [
        # Attestation reference number
        (r"N°\s*[A-Z0-9]{10,}", 1.0),
        # Date validity pattern
        (r"valid[ée]?\s+(?:jusqu|du)", 1.0),
    ],
    DocType.INSURANCE: [
        # Policy number
        (r"(?:police|contrat)\s*n°?\s*[A-Z0-9\-]+", 2.0),
        # Coverage period
        (r"du\s+\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4}\s+au\s+\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4}", 1.5),
    ],
}

# Minimum score to accept a classification (otherwise UNKNOWN)
_MIN_SCORE = 3.0


def classify_document(text: str) -> ClassificationResult:
    """Classify a document by scoring keywords and regex patterns against the text.

    Returns ClassificationResult with the best matching DocType, confidence, and per-type scores.
    """
    text_upper = text.upper()
    text_lower = text.lower()
    scores: dict[str, float] = {}

    for doc_type in DocType:
        if doc_type == DocType.UNKNOWN:
            continue

        score = 0.0

        # Keyword scoring
        keywords = _KEYWORDS.get(doc_type, [])
        for keyword, weight in keywords:
            # Count occurrences (case-insensitive)
            count = text_lower.count(keyword.lower())
            if count > 0:
                # Diminishing returns for repeated keywords
                score += weight * min(count, 3)

        # Regex pattern scoring
        regex_boosts = _REGEX_BOOSTS.get(doc_type, [])
        for pattern, weight in regex_boosts:
            matches = re.findall(pattern, text_upper)
            if matches:
                score += weight * min(len(matches), 3)

        scores[doc_type.value] = round(score, 2)

    # Find the winner
    if not scores:
        return ClassificationResult(
            doc_type=DocType.UNKNOWN,
            confidence=0.0,
            scores={},
        )

    best_type_str = max(scores, key=scores.get)  # type: ignore[arg-type]
    best_score = scores[best_type_str]

    if best_score < _MIN_SCORE:
        return ClassificationResult(
            doc_type=DocType.UNKNOWN,
            confidence=0.0,
            scores=scores,
        )

    # Calculate confidence: normalize against the theoretical max and spread
    # Use a sigmoid-like mapping: score → confidence
    # At score 10 → ~0.7, at score 20 → ~0.9, at score 30+ → ~0.95
    raw_confidence = min(best_score / (best_score + 10), 0.99)

    # Penalize if second-best is close (ambiguous)
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) > 1 and sorted_scores[1] > 0:
        ratio = sorted_scores[1] / sorted_scores[0]
        if ratio > 0.7:
            raw_confidence *= 0.7  # Very ambiguous
        elif ratio > 0.4:
            raw_confidence *= 0.85  # Somewhat ambiguous

    confidence = round(raw_confidence, 4)

    return ClassificationResult(
        doc_type=DocType(best_type_str),
        confidence=confidence,
        scores=scores,
    )
