"""Fix compliance_templates duplicates and add unique constraint.

The compliance_templates table lacked a unique constraint on
(tenant_id, entity_type, type_document), causing seed re-runs to
create duplicate entries. This migration:
1. Removes duplicate rows (keeps the earliest per group)
2. Adds a unique constraint to prevent future duplicates

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Delete duplicate compliance_templates, keep earliest per group ──
    op.execute("""
        DELETE FROM compliance_templates
        WHERE id NOT IN (
            SELECT DISTINCT ON (tenant_id, entity_type, type_document) id
            FROM compliance_templates
            ORDER BY tenant_id, entity_type, type_document, created_at ASC
        )
    """)

    # ── 2. Add unique constraint ──
    op.create_unique_constraint(
        "uq_compliance_templates_tenant_entity_doctype",
        "compliance_templates",
        ["tenant_id", "entity_type", "type_document"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_compliance_templates_tenant_entity_doctype", "compliance_templates")
