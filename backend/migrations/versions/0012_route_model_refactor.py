"""Refactor route model: template / run / mission separation.

Creates route_templates, route_template_stops, route_runs, route_run_missions.
Adds source_type, source_route_template_id, source_route_run_id to jobs.
Migrates data from old routes → route_templates.
Old tables (routes, route_delivery_points) kept for backward compatibility.

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-28 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. route_templates (Tournée modèle) ──────────────────────────
    op.create_table(
        "route_templates",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_id", sa.UUID(), sa.ForeignKey("agencies.id", ondelete="SET NULL")),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("site", sa.String(100)),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("recurrence_rule", sa.String(30), nullable=False, server_default=sa.text("'LUN_VEN'")),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date()),
        sa.Column("default_driver_id", sa.UUID(), sa.ForeignKey("drivers.id", ondelete="SET NULL")),
        sa.Column("default_vehicle_id", sa.UUID(), sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column("is_subcontracted", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("default_subcontractor_id", sa.UUID(), sa.ForeignKey("subcontractors.id", ondelete="SET NULL")),
        sa.Column("default_mission_type", sa.String(30), server_default=sa.text("'LOT_COMPLET'")),
        sa.Column("default_sale_amount_ht", sa.Numeric(12, 2)),
        sa.Column("default_purchase_amount_ht", sa.Numeric(12, 2)),
        sa.Column("default_loading_address", sa.Text()),
        sa.Column("default_estimated_distance_km", sa.Numeric(10, 2)),
        sa.Column("default_constraints_json", sa.JSON()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.UUID()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_route_templates_tenant_code"),
    )
    op.create_index("ix_route_templates_tenant", "route_templates", ["tenant_id"])
    op.create_index("ix_route_templates_customer", "route_templates", ["customer_id"])
    op.create_index("ix_route_templates_driver", "route_templates", ["default_driver_id"])

    # ── 2. route_template_stops (Arrêts par défaut) ──────────────────
    op.create_table(
        "route_template_stops",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_template_id", sa.UUID(), sa.ForeignKey("route_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("stop_type", sa.String(20), server_default=sa.text("'DELIVERY'")),
        sa.Column("name", sa.String(255)),
        sa.Column("address", sa.Text()),
        sa.Column("city", sa.String(100)),
        sa.Column("postal_code", sa.String(10)),
        sa.Column("contact_name", sa.String(100)),
        sa.Column("contact_phone", sa.String(20)),
        sa.Column("instructions", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_route_template_stops_template", "route_template_stops", ["route_template_id"])

    # ── 3. route_runs (Exécution / Tournée du jour) ──────────────────
    op.create_table(
        "route_runs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_template_id", sa.UUID(), sa.ForeignKey("route_templates.id", ondelete="SET NULL")),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'DRAFT'")),
        sa.Column("assigned_driver_id", sa.UUID(), sa.ForeignKey("drivers.id", ondelete="SET NULL")),
        sa.Column("assigned_vehicle_id", sa.UUID(), sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column("planned_start_at", sa.DateTime(timezone=True)),
        sa.Column("planned_end_at", sa.DateTime(timezone=True)),
        sa.Column("actual_start_at", sa.DateTime(timezone=True)),
        sa.Column("actual_end_at", sa.DateTime(timezone=True)),
        sa.Column("aggregated_sale_amount_ht", sa.Numeric(12, 2)),
        sa.Column("aggregated_purchase_amount_ht", sa.Numeric(12, 2)),
        sa.Column("aggregated_margin_ht", sa.Numeric(12, 2)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.UUID()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_route_runs_tenant_code"),
    )
    op.create_index("ix_route_runs_tenant", "route_runs", ["tenant_id"])
    op.create_index("ix_route_runs_template", "route_runs", ["route_template_id"])
    op.create_index("ix_route_runs_service_date", "route_runs", ["tenant_id", "service_date"])
    op.create_index("ix_route_runs_driver", "route_runs", ["assigned_driver_id"])

    # ── 4. route_run_missions (Junction: Run ↔ Mission + sequence) ───
    op.create_table(
        "route_run_missions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_run_id", sa.UUID(), sa.ForeignKey("route_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mission_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("assignment_status", sa.String(20), server_default=sa.text("'ASSIGNED'")),
        sa.Column("planned_eta", sa.DateTime(timezone=True)),
        sa.Column("actual_eta", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("route_run_id", "mission_id", name="uq_run_mission"),
        sa.UniqueConstraint("route_run_id", "sequence", name="uq_run_sequence"),
    )
    op.create_index("ix_route_run_missions_run", "route_run_missions", ["route_run_id"])
    op.create_index("ix_route_run_missions_mission", "route_run_missions", ["mission_id"])

    # ── 5. Add source columns to jobs ────────────────────────────────
    op.add_column("jobs", sa.Column("source_type", sa.String(30), server_default=sa.text("'MANUAL'")))
    op.add_column("jobs", sa.Column("source_route_template_id", sa.UUID(),
                                     sa.ForeignKey("route_templates.id", ondelete="SET NULL")))
    op.add_column("jobs", sa.Column("source_route_run_id", sa.UUID(),
                                     sa.ForeignKey("route_runs.id", ondelete="SET NULL")))
    op.create_index("ix_jobs_source_template", "jobs", ["source_route_template_id"])
    op.create_index("ix_jobs_source_run", "jobs", ["source_route_run_id"])

    # ── 6. Migrate data: routes → route_templates ────────────────────
    op.execute("""
        INSERT INTO route_templates (
            id, tenant_id, agency_id, code, label, customer_id, site,
            status, recurrence_rule, valid_from, valid_to,
            default_driver_id, default_vehicle_id, is_subcontracted, default_subcontractor_id,
            default_mission_type, default_sale_amount_ht, default_purchase_amount_ht,
            default_loading_address, default_estimated_distance_km, default_constraints_json,
            notes, created_at, updated_at, created_by
        )
        SELECT
            id, tenant_id, agency_id, numero, libelle, client_id, site,
            CASE statut
                WHEN 'ACTIF' THEN 'ACTIVE'
                WHEN 'SUSPENDUE' THEN 'SUSPENDED'
                WHEN 'ARCHIVEE' THEN 'ARCHIVED'
                ELSE 'ACTIVE'
            END,
            recurrence, date_debut, date_fin,
            driver_id, vehicle_id, is_subcontracted, subcontractor_id,
            type_mission, montant_vente_ht, montant_achat_ht,
            adresse_chargement, distance_estimee_km, contraintes,
            notes, created_at, updated_at, created_by
        FROM routes
    """)

    # ── 7. Migrate data: route_delivery_points → route_template_stops
    op.execute("""
        INSERT INTO route_template_stops (
            id, tenant_id, route_template_id, sequence, stop_type,
            name, address, city, postal_code,
            contact_name, contact_phone, instructions, created_at
        )
        SELECT
            id, tenant_id, route_id, ordre, 'DELIVERY',
            contact_nom, adresse, ville, code_postal,
            contact_nom, contact_telephone, instructions, created_at
        FROM route_delivery_points
    """)

    # ── 8. Backfill jobs.source_route_template_id from jobs.route_id
    op.execute("""
        UPDATE jobs SET
            source_type = 'GENERATED_FROM_TEMPLATE',
            source_route_template_id = route_id
        WHERE route_id IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_index("ix_jobs_source_run", "jobs")
    op.drop_index("ix_jobs_source_template", "jobs")
    op.drop_column("jobs", "source_route_run_id")
    op.drop_column("jobs", "source_route_template_id")
    op.drop_column("jobs", "source_type")
    op.drop_table("route_run_missions")
    op.drop_table("route_runs")
    op.drop_table("route_template_stops")
    op.drop_table("route_templates")
