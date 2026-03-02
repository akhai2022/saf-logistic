"""Add OCR document type classification, per-field confidence, and extraction metadata.

Adds columns to ocr_jobs: doc_type, doc_type_confidence, extracted_fields,
field_confidences, global_confidence, normalized_text, extraction_errors.
Backfills existing rows with doc_type='UNKNOWN'.

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"


def upgrade() -> None:
    op.add_column("ocr_jobs", sa.Column("doc_type", sa.String(30), server_default=sa.text("'UNKNOWN'")))
    op.add_column("ocr_jobs", sa.Column("doc_type_confidence", sa.Numeric(5, 4)))
    op.add_column("ocr_jobs", sa.Column("extracted_fields", sa.JSON()))
    op.add_column("ocr_jobs", sa.Column("field_confidences", sa.JSON()))
    op.add_column("ocr_jobs", sa.Column("global_confidence", sa.Numeric(5, 4)))
    op.add_column("ocr_jobs", sa.Column("normalized_text", sa.Text()))
    op.add_column("ocr_jobs", sa.Column("extraction_errors", sa.JSON()))

    op.create_index("ix_ocr_jobs_doc_type", "ocr_jobs", ["doc_type"])

    # Backfill existing rows
    op.execute("UPDATE ocr_jobs SET doc_type = 'UNKNOWN' WHERE doc_type IS NULL")


def downgrade() -> None:
    op.drop_index("ix_ocr_jobs_doc_type", table_name="ocr_jobs")
    op.drop_column("ocr_jobs", "extraction_errors")
    op.drop_column("ocr_jobs", "normalized_text")
    op.drop_column("ocr_jobs", "global_confidence")
    op.drop_column("ocr_jobs", "field_confidences")
    op.drop_column("ocr_jobs", "extracted_fields")
    op.drop_column("ocr_jobs", "doc_type_confidence")
    op.drop_column("ocr_jobs", "doc_type")
