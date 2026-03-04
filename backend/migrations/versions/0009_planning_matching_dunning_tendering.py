"""Planning, matching, dunning & tendering.

Creates driver_events, dunning_levels, dunning_actions,
supplier_invoice_matchings, subcontractor_offers.
Adds CMR columns to jobs, rapprochement columns to supplier_invoices,
achat/vente columns to pricing_rules.

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # driver_events — Timeline events for driver mobile workflow
    # ------------------------------------------------------------------
    op.create_table(
        "driver_events",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.UUID(),
                  sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", sa.UUID(),
                  sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(10, 7)),
        sa.Column("notes", sa.Text()),
        sa.Column("photo_s3_key", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_driver_events_job", "driver_events", ["job_id"])
    op.create_index("ix_driver_events_driver", "driver_events", ["driver_id"])

    # ------------------------------------------------------------------
    # dunning_levels — Configurable dunning escalation levels
    # ------------------------------------------------------------------
    op.create_table(
        "dunning_levels",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("niveau", sa.Integer(), nullable=False),
        sa.Column("libelle", sa.String(100), nullable=False),
        sa.Column("jours_apres_echeance", sa.Integer(), nullable=False),
        sa.Column("template_objet", sa.String(255)),
        sa.Column("template_texte", sa.Text()),
        sa.Column("is_active", sa.Boolean(),
                  server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_dunning_levels_tenant", "dunning_levels", ["tenant_id"])

    # ------------------------------------------------------------------
    # dunning_actions — History of dunning actions taken
    # ------------------------------------------------------------------
    op.create_table(
        "dunning_actions",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", sa.UUID(),
                  sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("customer_id", sa.UUID(),
                  sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("dunning_level_id", sa.UUID(),
                  sa.ForeignKey("dunning_levels.id")),
        sa.Column("date_relance", sa.Date(), nullable=False),
        sa.Column("mode", sa.String(20)),
        sa.Column("notes", sa.Text()),
        sa.Column("pdf_s3_key", sa.String(500)),
        sa.Column("created_by", sa.UUID(),
                  sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_dunning_actions_invoice", "dunning_actions", ["invoice_id"])
    op.create_index("ix_dunning_actions_customer", "dunning_actions", ["customer_id"])

    # ------------------------------------------------------------------
    # supplier_invoice_matchings — Link supplier invoices to missions
    # ------------------------------------------------------------------
    op.create_table(
        "supplier_invoice_matchings",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_invoice_id", sa.UUID(),
                  sa.ForeignKey("supplier_invoices.id"), nullable=False),
        sa.Column("job_id", sa.UUID(),
                  sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("montant_attendu", sa.Numeric(12, 2)),
        sa.Column("montant_facture", sa.Numeric(12, 2), nullable=False),
        sa.Column("ecart", sa.Numeric(12, 2)),
        sa.Column("ecart_pourcent", sa.Numeric(5, 2)),
        sa.Column("statut", sa.String(30),
                  server_default=sa.text("'A_VERIFIER'")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.UUID(),
                  sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_supplier_invoice_matchings_invoice",
                     "supplier_invoice_matchings", ["supplier_invoice_id"])
    op.create_index("ix_supplier_invoice_matchings_job",
                     "supplier_invoice_matchings", ["job_id"])

    # ------------------------------------------------------------------
    # subcontractor_offers — Tendering / acceptance workflow
    # ------------------------------------------------------------------
    op.create_table(
        "subcontractor_offers",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.UUID(),
                  sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("subcontractor_id", sa.UUID(),
                  sa.ForeignKey("subcontractors.id"), nullable=False),
        sa.Column("montant_propose", sa.Numeric(12, 2), nullable=False),
        sa.Column("montant_contre_offre", sa.Numeric(12, 2)),
        sa.Column("date_envoi", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("date_limite_reponse", sa.DateTime(timezone=True)),
        sa.Column("date_reponse", sa.DateTime(timezone=True)),
        sa.Column("statut", sa.String(30), nullable=False,
                  server_default=sa.text("'ENVOYEE'")),
        sa.Column("motif_refus", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.UUID(),
                  sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_subcontractor_offers_job", "subcontractor_offers",
                     ["job_id"])
    op.create_index("ix_subcontractor_offers_sub", "subcontractor_offers",
                     ["subcontractor_id"])

    # ------------------------------------------------------------------
    # ALTER jobs — CMR columns
    # ------------------------------------------------------------------
    op.add_column("jobs",
                  sa.Column("cmr_s3_key", sa.String(500)))
    op.add_column("jobs",
                  sa.Column("cmr_numero", sa.String(50)))

    # ------------------------------------------------------------------
    # ALTER supplier_invoices — rapprochement columns
    # ------------------------------------------------------------------
    op.add_column("supplier_invoices",
                  sa.Column("subcontractor_id", sa.UUID(),
                            sa.ForeignKey("subcontractors.id")))
    op.add_column("supplier_invoices",
                  sa.Column("statut_rapprochement", sa.String(30),
                            server_default=sa.text("'EN_ATTENTE'")))
    op.add_column("supplier_invoices",
                  sa.Column("montant_attendu_total", sa.Numeric(12, 2)))
    op.add_column("supplier_invoices",
                  sa.Column("ecart_total", sa.Numeric(12, 2)))

    # ------------------------------------------------------------------
    # ALTER pricing_rules — achat / vente direction
    # ------------------------------------------------------------------
    op.add_column("pricing_rules",
                  sa.Column("subcontractor_id", sa.UUID(),
                            sa.ForeignKey("subcontractors.id")))
    op.add_column("pricing_rules",
                  sa.Column("direction", sa.String(10),
                            server_default=sa.text("'VENTE'")))


def downgrade() -> None:
    # -- pricing_rules columns -------------------------------------------
    op.drop_column("pricing_rules", "direction")
    op.drop_column("pricing_rules", "subcontractor_id")

    # -- supplier_invoices columns ---------------------------------------
    op.drop_column("supplier_invoices", "ecart_total")
    op.drop_column("supplier_invoices", "montant_attendu_total")
    op.drop_column("supplier_invoices", "statut_rapprochement")
    op.drop_column("supplier_invoices", "subcontractor_id")

    # -- jobs columns ----------------------------------------------------
    op.drop_column("jobs", "cmr_numero")
    op.drop_column("jobs", "cmr_s3_key")

    # -- tables (reverse creation order) ---------------------------------
    op.drop_table("subcontractor_offers")
    op.drop_table("supplier_invoice_matchings")
    op.drop_table("dunning_actions")
    op.drop_table("dunning_levels")
    op.drop_table("driver_events")
