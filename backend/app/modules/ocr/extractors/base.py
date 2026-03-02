"""Base types for the OCR extraction pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class DocType(str, Enum):
    INVOICE = "INVOICE"
    BANK_RIB = "BANK_RIB"
    KBIS = "KBIS"
    URSSAF = "URSSAF"
    INSURANCE = "INSURANCE"
    UNKNOWN = "UNKNOWN"


@dataclass
class ClassificationResult:
    doc_type: DocType
    confidence: float  # 0..1
    scores: dict[str, float] = field(default_factory=dict)  # per-type scores


@dataclass
class ExtractionResult:
    extracted_fields: dict  # schema depends on doc_type
    field_confidences: dict[str, float]  # per-field 0..1
    global_confidence: float  # 0..1
    errors: list[str] = field(default_factory=list)


class Extractor(Protocol):
    """Protocol for typed extractors."""

    def extract(self, text: str, lines: list[str]) -> ExtractionResult: ...
