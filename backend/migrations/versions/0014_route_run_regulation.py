"""Add regulation metadata columns to route_runs.

Supports the regulation mechanism for closing overdue/past route runs
that remain stuck in DISPATCHED or IN_PROGRESS status.

Adds three nullable columns:
- regulated_at: timestamp of regulation
- regulated_by: user who triggered regulation (null for automatic)
- regulation_source: 'manual' or 'automatic'

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-31 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "route_runs",
        sa.Column("regulated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "route_runs",
        sa.Column("regulated_by", sa.UUID(), nullable=True),
    )
    op.add_column(
        "route_runs",
        sa.Column(
            "regulation_source",
            sa.String(20),
            nullable=True,
            comment="manual | automatic",
        ),
    )


def downgrade() -> None:
    op.drop_column("route_runs", "regulation_source")
    op.drop_column("route_runs", "regulated_by")
    op.drop_column("route_runs", "regulated_at")
