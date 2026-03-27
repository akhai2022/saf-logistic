"""Add routes (tournées) — recurring delivery route definitions.

Creates routes, route_delivery_points tables and adds route_id to jobs.
A route is a recurring delivery pattern (same client, same site, regular schedule).
A job/mission is a single execution of a route on a specific date.

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-28 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Routes (tournées) ────────────────────────────────────────────
    op.create_table(
        "routes",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_id", sa.UUID(), sa.ForeignKey("agencies.id", ondelete="SET NULL")),
        sa.Column("numero", sa.String(30), nullable=False),
        sa.Column("libelle", sa.String(255), nullable=False),
        sa.Column("client_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("type_mission", sa.String(30), server_default=sa.text("'LOT_COMPLET'")),
        # Recurrence
        sa.Column("recurrence", sa.String(30), nullable=False, server_default=sa.text("'LUN_VEN'")),
        sa.Column("date_debut", sa.Date(), nullable=False),
        sa.Column("date_fin", sa.Date()),
        # Default assignment
        sa.Column("driver_id", sa.UUID(), sa.ForeignKey("drivers.id", ondelete="SET NULL")),
        sa.Column("vehicle_id", sa.UUID(), sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column("is_subcontracted", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("subcontractor_id", sa.UUID(), sa.ForeignKey("subcontractors.id", ondelete="SET NULL")),
        # Financials (standard per execution)
        sa.Column("montant_vente_ht", sa.Numeric(12, 2)),
        sa.Column("montant_achat_ht", sa.Numeric(12, 2)),
        # Pickup
        sa.Column("adresse_chargement", sa.Text()),
        sa.Column("site", sa.String(100)),
        sa.Column("distance_estimee_km", sa.Numeric(10, 2)),
        sa.Column("contraintes", sa.JSON()),
        sa.Column("notes", sa.Text()),
        # Status
        sa.Column("statut", sa.String(20), server_default=sa.text("'ACTIF'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.UUID()),
        sa.UniqueConstraint("tenant_id", "numero", name="uq_routes_tenant_numero"),
    )
    op.create_index("ix_routes_tenant", "routes", ["tenant_id"])
    op.create_index("ix_routes_client", "routes", ["client_id"])
    op.create_index("ix_routes_driver", "routes", ["driver_id"])

    # ── Route delivery points (template) ─────────────────────────────
    op.create_table(
        "route_delivery_points",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_id", sa.UUID(), sa.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False),
        sa.Column("adresse", sa.Text()),
        sa.Column("code_postal", sa.String(10)),
        sa.Column("ville", sa.String(100)),
        sa.Column("contact_nom", sa.String(100)),
        sa.Column("contact_telephone", sa.String(20)),
        sa.Column("instructions", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_route_dp_route", "route_delivery_points", ["route_id"])

    # ── Link jobs to routes ──────────────────────────────────────────
    op.add_column("jobs", sa.Column("route_id", sa.UUID(), sa.ForeignKey("routes.id", ondelete="SET NULL")))
    op.create_index("ix_jobs_route", "jobs", ["route_id"])


def downgrade() -> None:
    op.drop_index("ix_jobs_route", "jobs")
    op.drop_column("jobs", "route_id")
    op.drop_table("route_delivery_points")
    op.drop_table("routes")
