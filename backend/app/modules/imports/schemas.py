"""Pydantic schemas for the bulk import module."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ImportError(BaseModel):
    """A single validation error tied to a specific row/column."""
    row: int
    column: str | None = None
    message: str
    value: str | None = None


class ImportJobOut(BaseModel):
    """Full representation of an import job."""
    id: str
    tenant_id: str
    entity_type: str
    status: str
    file_name: str
    file_s3_key: str
    content_type: str | None = None
    total_rows: int | None = None
    valid_rows: int | None = None
    error_rows: int | None = None
    inserted_rows: int | None = None
    updated_rows: int | None = None
    skipped_rows: int | None = None
    column_mapping: dict[str, str] | None = None
    preview_data: dict[str, Any] | None = None
    errors_json: list[dict[str, Any]] | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PreviewResult(BaseModel):
    """Response returned by the preview endpoint."""
    job_id: str
    entity_type: str
    total_rows: int
    valid_rows: int
    error_rows: int
    detected_mapping: dict[str, str]
    sample_rows: list[dict[str, Any]]
    errors: list[ImportError]


class ApplyResult(BaseModel):
    """Response returned by the apply endpoint."""
    job_id: str
    entity_type: str
    total_rows: int
    inserted_rows: int
    updated_rows: int
    skipped_rows: int
    error_rows: int
    errors: list[ImportError]
