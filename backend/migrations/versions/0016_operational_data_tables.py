"""Add operational data tables for spreadsheet integration.

Tables: customer_complaints, driver_infractions, traffic_violations, driver_leaves.
These tables store data from the RECLAMATIONS, INFRACTIONS CHAUFFEURS,
CONTRAVENTIONS, and Tableau des congés integration spreadsheets.

Revision ID: 0016
Revises: 0015
Create Date: 2026-03-31 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0016"
down_revision: Union[str, None] = "0015"
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
    # Drop any partially-created tables from failed previous attempts
    # These are new tables with no production data yet
    for tbl in ["driver_leaves", "traffic_violations", "driver_infractions", "customer_complaints"]:
        if _table_exists(tbl):
            op.execute(sa.text(f"DROP TABLE {tbl} CASCADE"))

    # ── customer_complaints (RECLAMATIONS) ────────────────────────
    if not _table_exists("customer_complaints"):
        op.create_table(
            "customer_complaints",
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
            sa.Column("tenant_id", sa.UUID(), nullable=False),
            sa.Column("date_incident", sa.Date(), nullable=True),
            sa.Column("client_name", sa.String(200), nullable=True),
            sa.Column("client_id", sa.UUID(), nullable=True),
            sa.Column("contact_name", sa.String(200), nullable=True),
            sa.Column("subject", sa.Text(), nullable=False),
            sa.Column("driver_id", sa.UUID(), nullable=True),
            sa.Column("severity", sa.String(20), server_default="NORMAL", nullable=False),
            sa.Column("status", sa.String(20), server_default="OUVERTE", nullable=False),
            sa.Column("resolution", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["client_id"], ["customers.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="SET NULL"),
        )
    _create_index_if_not_exists("ix_customer_complaints_tenant_id", "customer_complaints", ["tenant_id"])
    _create_index_if_not_exists("ix_customer_complaints_tenant_status", "customer_complaints", ["tenant_id", "status"])
    _create_index_if_not_exists("ix_customer_complaints_tenant_client", "customer_complaints", ["tenant_id", "client_id"])

    # ── driver_infractions (INFRACTIONS CHAUFFEURS) ───────────────
    if not _table_exists("driver_infractions"):
        op.create_table(
            "driver_infractions",
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
            sa.Column("tenant_id", sa.UUID(), nullable=False),
            sa.Column("driver_id", sa.UUID(), nullable=False),
            sa.Column("year", sa.Integer(), nullable=False),
            sa.Column("month", sa.Integer(), nullable=False),
            sa.Column("infraction_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("anomaly_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        )
    _create_index_if_not_exists("ix_driver_infractions_tenant_id", "driver_infractions", ["tenant_id"])
    _create_index_if_not_exists("ix_driver_infractions_unique", "driver_infractions", ["tenant_id", "driver_id", "year", "month"], unique=True)

    # ── traffic_violations (CONTRAVENTIONS) ───────────────────────
    if not _table_exists("traffic_violations"):
        op.create_table(
            "traffic_violations",
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
            sa.Column("tenant_id", sa.UUID(), nullable=False),
            sa.Column("date_infraction", sa.Date(), nullable=True),
            sa.Column("lieu", sa.String(200), nullable=True),
            sa.Column("vehicle_id", sa.UUID(), nullable=True),
            sa.Column("immatriculation", sa.String(15), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("numero_avis", sa.String(50), nullable=True),
            sa.Column("montant", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column("statut_paiement", sa.String(20), server_default="A_PAYER", nullable=False),
            sa.Column("statut_dossier", sa.String(30), nullable=True),
            sa.Column("driver_id", sa.UUID(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="SET NULL"),
        )
    _create_index_if_not_exists("ix_traffic_violations_tenant_id", "traffic_violations", ["tenant_id"])
    _create_index_if_not_exists("ix_traffic_violations_tenant_vehicle", "traffic_violations", ["tenant_id", "vehicle_id"])

    # ── driver_leaves (Tableau des congés) ────────────────────────
    if not _table_exists("driver_leaves"):
        op.create_table(
            "driver_leaves",
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
            sa.Column("tenant_id", sa.UUID(), nullable=False),
            sa.Column("driver_id", sa.UUID(), nullable=False),
            sa.Column("date_debut", sa.Date(), nullable=False),
            sa.Column("date_fin", sa.Date(), nullable=False),
            sa.Column("type_conge", sa.String(30), server_default="CONGES_PAYES", nullable=False),
            sa.Column("statut", sa.String(20), server_default="APPROUVE", nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        )
    _create_index_if_not_exists("ix_driver_leaves_tenant_id", "driver_leaves", ["tenant_id"])
    _create_index_if_not_exists("ix_driver_leaves_tenant_driver", "driver_leaves", ["tenant_id", "driver_id"])
    _create_index_if_not_exists("ix_driver_leaves_tenant_dates", "driver_leaves", ["tenant_id", "date_debut", "date_fin"])


def downgrade() -> None:
    op.drop_index("ix_driver_leaves_tenant_dates", table_name="driver_leaves")
    op.drop_index("ix_driver_leaves_tenant_driver", table_name="driver_leaves")
    op.drop_index("ix_driver_leaves_tenant_id", table_name="driver_leaves")
    op.drop_table("driver_leaves")

    op.drop_index("ix_traffic_violations_tenant_vehicle", table_name="traffic_violations")
    op.drop_index("ix_traffic_violations_tenant_id", table_name="traffic_violations")
    op.drop_table("traffic_violations")

    op.drop_index("ix_driver_infractions_unique", table_name="driver_infractions")
    op.drop_index("ix_driver_infractions_tenant_id", table_name="driver_infractions")
    op.drop_table("driver_infractions")

    op.drop_index("ix_customer_complaints_tenant_client", table_name="customer_complaints")
    op.drop_index("ix_customer_complaints_tenant_status", table_name="customer_complaints")
    op.drop_index("ix_customer_complaints_tenant_id", table_name="customer_complaints")
    op.drop_table("customer_complaints")
