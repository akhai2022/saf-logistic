"""Add staff_schedules and vehicle_repairs tables.

Tables: staff_schedules, vehicle_repairs.
These tables store data from the "Planning de travail SAF AT" and
"tableau REPARATION 3 mois format" integration spreadsheets.

Revision ID: 0017
Revises: 0016
Create Date: 2026-03-31 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
    ), {"t": name})
    return result.scalar()


def _index_exists(name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = :n)"
    ), {"n": name})
    return result.scalar()


def _create_index_if_not_exists(name: str, table: str, columns: list, **kwargs):
    if not _index_exists(name):
        op.create_index(name, table, columns, **kwargs)


def upgrade() -> None:
    # ── staff_schedules (Planning de travail SAF AT) ─────────────
    if not _table_exists("staff_schedules"):
        op.create_table(
            "staff_schedules",
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
            sa.Column("tenant_id", sa.UUID(), nullable=False),
            sa.Column("driver_id", sa.UUID(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(20), server_default="SERVICE", nullable=False),
            sa.Column("shift_start", sa.Time(), nullable=True),
            sa.Column("shift_end", sa.Time(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("tenant_id", "driver_id", "date", name="uq_staff_schedules_tenant_driver_date"),
        )
    _create_index_if_not_exists("ix_staff_schedules_tenant_id", "staff_schedules", ["tenant_id"])
    _create_index_if_not_exists("ix_staff_schedules_tenant_date", "staff_schedules", ["tenant_id", "date"])

    # ── vehicle_repairs (tableau REPARATION 3 mois format) ───────
    if not _table_exists("vehicle_repairs"):
        op.create_table(
            "vehicle_repairs",
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
            sa.Column("tenant_id", sa.UUID(), nullable=False),
            sa.Column("vehicle_id", sa.UUID(), nullable=False),
            sa.Column("immatriculation", sa.String(15), nullable=True),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), server_default="A_FAIRE", nullable=False),
            sa.Column("date_signalement", sa.Date(), nullable=True),
            sa.Column("date_realisation", sa.Date(), nullable=True),
            sa.Column("cout", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column("prestataire", sa.String(200), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        )
    _create_index_if_not_exists("ix_vehicle_repairs_tenant_id", "vehicle_repairs", ["tenant_id"])
    _create_index_if_not_exists("ix_vehicle_repairs_tenant_vehicle", "vehicle_repairs", ["tenant_id", "vehicle_id"])
    _create_index_if_not_exists("ix_vehicle_repairs_tenant_status", "vehicle_repairs", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_vehicle_repairs_tenant_status", table_name="vehicle_repairs")
    op.drop_index("ix_vehicle_repairs_tenant_vehicle", table_name="vehicle_repairs")
    op.drop_index("ix_vehicle_repairs_tenant_id", table_name="vehicle_repairs")
    op.drop_table("vehicle_repairs")

    op.drop_index("ix_staff_schedules_tenant_date", table_name="staff_schedules")
    op.drop_index("ix_staff_schedules_tenant_id", table_name="staff_schedules")
    op.drop_table("staff_schedules")
