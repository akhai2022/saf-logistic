"""Module H — Flotte & Maintenance + Module I — Reporting support tables.

Creates maintenance_schedules, maintenance_records, vehicle_costs, vehicle_claims.

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # maintenance_schedules — Recurring maintenance plans per vehicle
    # ------------------------------------------------------------------
    op.create_table(
        "maintenance_schedules",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.UUID(),
                  sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type_maintenance", sa.String(30), nullable=False),
        sa.Column("libelle", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("frequence_jours", sa.Integer()),
        sa.Column("frequence_km", sa.Integer()),
        sa.Column("derniere_date_realisation", sa.Date()),
        sa.Column("dernier_km_realisation", sa.Integer()),
        sa.Column("prochaine_date_prevue", sa.Date()),
        sa.Column("prochain_km_prevu", sa.Integer()),
        sa.Column("prestataire_par_defaut", sa.String(255)),
        sa.Column("cout_estime", sa.Numeric(10, 2)),
        sa.Column("alerte_jours_avant", sa.Integer(), server_default=sa.text("30")),
        sa.Column("alerte_km_avant", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"),
                  nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_maint_schedules_vehicle", "maintenance_schedules",
                     ["tenant_id", "vehicle_id"])

    # ------------------------------------------------------------------
    # maintenance_records — Actual maintenance events
    # ------------------------------------------------------------------
    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.UUID(),
                  sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schedule_id", sa.UUID(),
                  sa.ForeignKey("maintenance_schedules.id", ondelete="SET NULL")),
        sa.Column("type_maintenance", sa.String(30), nullable=False),
        sa.Column("libelle", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("date_debut", sa.Date(), nullable=False),
        sa.Column("date_fin", sa.Date()),
        sa.Column("km_vehicule", sa.Integer()),
        sa.Column("prestataire", sa.String(255)),
        sa.Column("lieu", sa.String(255)),
        sa.Column("cout_pieces_ht", sa.Numeric(10, 2)),
        sa.Column("cout_main_oeuvre_ht", sa.Numeric(10, 2)),
        sa.Column("cout_total_ht", sa.Numeric(10, 2)),
        sa.Column("cout_tva", sa.Numeric(10, 2)),
        sa.Column("cout_total_ttc", sa.Numeric(10, 2)),
        sa.Column("facture_ref", sa.String(100)),
        sa.Column("facture_s3_key", sa.String(500)),
        sa.Column("is_planifie", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("statut", sa.String(20),
                  server_default=sa.text("'PLANIFIE'"), nullable=False),
        sa.Column("resultat", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.UUID()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_maint_records_vehicle", "maintenance_records",
                     ["tenant_id", "vehicle_id"])
    op.create_index("ix_maint_records_schedule", "maintenance_records",
                     ["schedule_id"])
    op.create_index("ix_maint_records_statut", "maintenance_records",
                     ["statut"])

    # ------------------------------------------------------------------
    # vehicle_costs — Unified cost ledger per vehicle
    # ------------------------------------------------------------------
    op.create_table(
        "vehicle_costs",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.UUID(),
                  sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("maintenance_record_id", sa.UUID(),
                  sa.ForeignKey("maintenance_records.id", ondelete="SET NULL")),
        sa.Column("categorie", sa.String(30), nullable=False),
        sa.Column("sous_categorie", sa.String(50)),
        sa.Column("libelle", sa.String(255), nullable=False),
        sa.Column("date_cout", sa.Date(), nullable=False),
        sa.Column("montant_ht", sa.Numeric(10, 2), nullable=False),
        sa.Column("montant_tva", sa.Numeric(10, 2)),
        sa.Column("montant_ttc", sa.Numeric(10, 2)),
        sa.Column("km_vehicule", sa.Integer()),
        sa.Column("quantite", sa.Numeric(10, 3)),
        sa.Column("unite", sa.String(20)),
        sa.Column("fournisseur", sa.String(255)),
        sa.Column("facture_ref", sa.String(100)),
        sa.Column("facture_s3_key", sa.String(500)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.UUID()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_vehicle_costs_vehicle", "vehicle_costs",
                     ["tenant_id", "vehicle_id"])
    op.create_index("ix_vehicle_costs_categorie", "vehicle_costs",
                     ["categorie"])
    op.create_index("ix_vehicle_costs_date", "vehicle_costs",
                     ["date_cout"])

    # ------------------------------------------------------------------
    # vehicle_claims — Sinistres / accidents
    # ------------------------------------------------------------------
    op.create_table(
        "vehicle_claims",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.UUID(),
                  sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero", sa.String(50), nullable=False),
        sa.Column("date_sinistre", sa.Date(), nullable=False),
        sa.Column("heure_sinistre", sa.Time()),
        sa.Column("lieu", sa.String(255)),
        sa.Column("type_sinistre", sa.String(30), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("driver_id", sa.UUID(),
                  sa.ForeignKey("drivers.id", ondelete="SET NULL")),
        sa.Column("tiers_implique", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("tiers_nom", sa.String(255)),
        sa.Column("tiers_immatriculation", sa.String(20)),
        sa.Column("tiers_assurance", sa.String(255)),
        sa.Column("tiers_police", sa.String(100)),
        sa.Column("constat_s3_key", sa.String(500)),
        sa.Column("assurance_ref", sa.String(100)),
        sa.Column("assurance_declaration_date", sa.Date()),
        sa.Column("responsabilite", sa.String(20),
                  server_default=sa.text("'A_DETERMINER'")),
        sa.Column("cout_reparation_ht", sa.Numeric(10, 2)),
        sa.Column("franchise", sa.Numeric(10, 2)),
        sa.Column("indemnisation_recue", sa.Numeric(10, 2)),
        sa.Column("cout_immobilisation_estime", sa.Numeric(10, 2)),
        sa.Column("jours_immobilisation", sa.Integer()),
        sa.Column("statut", sa.String(20),
                  server_default=sa.text("'DECLARE'"), nullable=False),
        sa.Column("date_cloture", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.UUID()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_vehicle_claims_vehicle", "vehicle_claims",
                     ["tenant_id", "vehicle_id"])
    op.create_index("ix_vehicle_claims_numero", "vehicle_claims",
                     ["tenant_id", "numero"], unique=True)
    op.create_index("ix_vehicle_claims_statut", "vehicle_claims",
                     ["statut"])


def downgrade() -> None:
    op.drop_table("vehicle_claims")
    op.drop_table("vehicle_costs")
    op.drop_table("maintenance_records")
    op.drop_table("maintenance_schedules")
