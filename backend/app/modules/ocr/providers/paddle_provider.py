"""PaddleOCR provider — PDF to structured invoice data."""
from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path

from app.modules.ocr.providers.base import OcrResult

logger = logging.getLogger(__name__)

# Regex patterns for French invoices
PATTERNS = {
    "invoice_number": [
        r"(?:facture|invoice|n°\s*facture)[:\s]*([A-Z0-9][\w\-/]+)",
        r"(?:N°|No|Num)[:\s]*([A-Z0-9][\w\-/]+)",
    ],
    "invoice_date": [
        r"(?:date)[:\s]*(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})",
        r"(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4})",
    ],
    "total_ht": [
        r"(?:total\s*h\.?t\.?|montant\s*h\.?t\.?)[:\s]*([\d\s]+[,.]?\d*)\s*[€E]?",
    ],
    "total_ttc": [
        r"(?:total\s*t\.?t\.?c\.?|montant\s*t\.?t\.?c\.?|net\s*[àa]\s*payer)[:\s]*([\d\s]+[,.]?\d*)\s*[€E]?",
    ],
    "tva": [
        r"(?:t\.?v\.?a\.?|taxe)[:\s]*([\d\s]+[,.]?\d*)\s*[€E]?",
    ],
    "supplier_name": [
        r"^([A-Z][A-Z\s&\-\.]{2,40})$",
    ],
}


def _parse_french_number(s: str | None) -> float | None:
    if not s:
        return None
    s = s.replace(" ", "").replace("\u00a0", "")
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


class PaddleOcrProvider:
    def __init__(self):
        from paddleocr import PaddleOCR
        from pathlib import Path

        base = Path.home() / ".paddleocr" / "whl"
        det_dir = base / "det" / "en" / "en_PP-OCRv3_det_infer"
        rec_dir = base / "rec" / "french" / "latin_PP-OCRv3_rec_infer"
        cls_dir = base / "cls" / "ch_ppocr_mobile_v2.0_cls_infer"

        kwargs = {"use_angle_cls": True, "lang": "fr", "show_log": False}
        # Use pre-downloaded models if available (avoids runtime downloads)
        if det_dir.exists():
            kwargs["det_model_dir"] = str(det_dir)
        if rec_dir.exists():
            kwargs["rec_model_dir"] = str(rec_dir)
        if cls_dir.exists():
            kwargs["cls_model_dir"] = str(cls_dir)

        self._ocr = PaddleOCR(**kwargs)

    def _pdf_to_images(self, pdf_path: str) -> list[str]:
        import fitz  # pymupdf
        doc = fitz.open(pdf_path)
        image_paths = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=300)
            img_path = tempfile.mktemp(suffix=f"_p{page_num}.png")
            pix.save(img_path)
            image_paths.append(img_path)
        doc.close()
        return image_paths

    def _preprocess(self, image_path: str) -> str:
        import cv2
        import numpy as np
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        out_path = tempfile.mktemp(suffix="_preprocessed.png")
        cv2.imwrite(out_path, binary)
        return out_path

    def extract(self, file_path: str) -> OcrResult:
        ext = Path(file_path).suffix.lower()

        if ext == ".pdf":
            images = self._pdf_to_images(file_path)
        else:
            images = [file_path]

        all_text_lines: list[str] = []

        for img_path in images:
            processed = self._preprocess(img_path)
            result = self._ocr.ocr(processed, cls=True)
            if result and result[0]:
                for line in result[0]:
                    text_content = line[1][0]
                    all_text_lines.append(text_content)

        raw_text = "\n".join(all_text_lines)

        # Extract fields
        extracted = {}
        for field, patterns in PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    extracted[field] = match.group(1).strip()
                    break

        # Calculate confidence
        fields_found = sum(1 for k in ["invoice_number", "total_ht", "total_ttc"] if k in extracted)
        confidence = fields_found / 3.0

        # Line items via pdfplumber if PDF
        line_items = []
        if ext == ".pdf":
            try:
                from app.modules.ocr.line_items import extract_line_items
                line_items = extract_line_items(file_path)
            except Exception as e:
                logger.warning("Line item extraction failed: %s", e)

        return OcrResult(
            supplier_name=extracted.get("supplier_name"),
            invoice_number=extracted.get("invoice_number"),
            invoice_date=extracted.get("invoice_date"),
            total_ht=_parse_french_number(extracted.get("total_ht")),
            total_ttc=_parse_french_number(extracted.get("total_ttc")),
            tva=_parse_french_number(extracted.get("tva")),
            confidence=confidence,
            raw_text=raw_text,
            line_items=line_items,
        )
