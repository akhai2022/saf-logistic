from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class OcrResult:
    supplier_name: str | None
    invoice_number: str | None
    invoice_date: str | None
    total_ht: float | None
    total_ttc: float | None
    tva: float | None
    confidence: float
    raw_text: str
    line_items: list[dict] = field(default_factory=list)


class OcrProvider(Protocol):
    def extract(self, file_path: str) -> OcrResult: ...
