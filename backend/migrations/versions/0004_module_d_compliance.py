"""Module D — Gestion documentaire & Conformité.

Expands documents table for full vault, creates compliance_templates,
compliance_checklists, compliance_alerts tables.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Expand documents table → full Document Vault (D.4.1)
    # ------------------------------------------------------------------
    op.add_column("documents", sa.Column("sous_type", sa.String(50)))
    op.add_column("documents", sa.Column("numero_document", sa.String(100)))
    op.add_column("documents", sa.Column("date_emission", sa.Date()))
    op.add_column("documents", sa.Column("date_expiration", sa.Date()))
    op.add_column("documents", sa.Column("date_prochaine_echeance", sa.Date()))
    op.add_column("documents", sa.Column("organisme_emetteur", sa.String(255)))
    op.add_column("documents", sa.Column("tags", sa.ARRAY(sa.String())))
    op.add_column("documents", sa.Column("version", sa.Integer(), server_default=sa.text("1")))
    op.add_column("documents", sa.Column("remplace_document_id", sa.UUID(),
                                          sa.ForeignKey("documents.id", ondelete="SET NULL")))
    op.add_column("documents", sa.Column("statut", sa.String(30),
                                          server_default=sa.text("'VALIDE'")))
    op.add_column("documents", sa.Column("validation_par", sa.UUID()))
    op.add_column("documents", sa.Column("validation_date", sa.DateTime(timezone=True)))
    op.add_column("documents", sa.Column("motif_rejet", sa.Text()))
    op.add_column("documents", sa.Column("is_critical", sa.Boolean(),
                                          server_default=sa.text("false")))
    op.add_column("documents", sa.Column("alerte_j60_envoyee", sa.Boolean(),
                                          server_default=sa.text("false")))
    op.add_column("documents", sa.Column("alerte_j30_envoyee", sa.Boolean(),
                                          server_default=sa.text("false")))
    op.add_column("documents", sa.Column("alerte_j15_envoyee", sa.Boolean(),
                                          server_default=sa.text("false")))
    op.add_column("documents", sa.Column("alerte_j7_envoyee", sa.Boolean(),
                                          server_default=sa.text("false")))
    op.add_column("documents", sa.Column("alerte_j0_envoyee", sa.Boolean(),
                                          server_default=sa.text("false")))
    op.add_column("documents", sa.Column("uploaded_by", sa.UUID()))
    op.add_column("documents", sa.Column("uploaded_by_role", sa.String(30)))
    op.add_column("documents", sa.Column("fichier_taille_octets", sa.Integer()))
    op.add_column("documents", sa.Column("fichier_mime_type", sa.String(50)))

    # Migrate old columns → new
    op.execute("""
        UPDATE documents SET
            date_emission = issue_date,
            date_expiration = expiry_date
        WHERE issue_date IS NOT NULL OR expiry_date IS NOT NULL
    """)

    # Indexes on documents
    op.create_index("ix_documents_entity", "documents",
                     ["tenant_id", "entity_type", "entity_id"])
    op.create_index("ix_documents_expiration", "documents",
                     ["date_expiration"],
                     postgresql_where=sa.text("date_expiration IS NOT NULL"))

    # ------------------------------------------------------------------
    # Compliance Templates (D.4.4) — replaces/extends document_types
    # ------------------------------------------------------------------
    op.create_table(
        "compliance_templates",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("type_document", sa.String(50), nullable=False),
        sa.Column("libelle", sa.String(255), nullable=False),
        sa.Column("obligatoire", sa.Boolean(), server_default=sa.text("true"),
                  nullable=False),
        sa.Column("bloquant", sa.Boolean(), server_default=sa.text("true"),
                  nullable=False),
        sa.Column("condition_applicabilite", sa.Text()),  # JSON
        sa.Column("duree_validite_defaut_jours", sa.Integer()),
        sa.Column("alertes_jours", sa.ARRAY(sa.Integer()),
                  server_default=sa.text("'{60,30,15,7,0}'")),
        sa.Column("ordre_affichage", sa.Integer(), server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"),
                  nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_compliance_templates_tenant", "compliance_templates",
                     ["tenant_id", "entity_type"])

    # ------------------------------------------------------------------
    # Compliance Checklists (D.4.3)
    # ------------------------------------------------------------------
    op.create_table(
        "compliance_checklists",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("statut_global", sa.String(20),
                  server_default=sa.text("'OK'"), nullable=False),
        sa.Column("nb_documents_requis", sa.Integer(),
                  server_default=sa.text("0")),
        sa.Column("nb_documents_valides", sa.Integer(),
                  server_default=sa.text("0")),
        sa.Column("nb_documents_manquants", sa.Integer(),
                  server_default=sa.text("0")),
        sa.Column("nb_documents_expires", sa.Integer(),
                  server_default=sa.text("0")),
        sa.Column("nb_documents_expirant_bientot", sa.Integer(),
                  server_default=sa.text("0")),
        sa.Column("taux_conformite_pourcent", sa.Numeric(5, 2),
                  server_default=sa.text("100.00")),
        sa.Column("details", sa.Text()),  # JSON
        sa.Column("derniere_mise_a_jour", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_compliance_checklists_entity", "compliance_checklists",
                     ["tenant_id", "entity_type", "entity_id"], unique=True)

    # ------------------------------------------------------------------
    # Compliance Alerts (D.4.5)
    # ------------------------------------------------------------------
    op.create_table(
        "compliance_alerts",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.UUID(),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("type_alerte", sa.String(30), nullable=False),
        sa.Column("date_declenchement", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("date_expiration_document", sa.Date(), nullable=False),
        sa.Column("destinataires_notifies", sa.ARRAY(sa.UUID())),
        sa.Column("canaux_utilises", sa.ARRAY(sa.String())),
        sa.Column("statut", sa.String(20),
                  server_default=sa.text("'ENVOYEE'"), nullable=False),
        sa.Column("date_acquittement", sa.DateTime(timezone=True)),
        sa.Column("acquittee_par", sa.UUID()),
        sa.Column("notes", sa.Text()),
        sa.Column("escalade_niveau", sa.Integer(),
                  server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_compliance_alerts_document", "compliance_alerts",
                     ["document_id"])
    op.create_index("ix_compliance_alerts_entity", "compliance_alerts",
                     ["tenant_id", "entity_type", "entity_id"])
    op.create_index("ix_compliance_alerts_statut", "compliance_alerts",
                     ["statut"])


def downgrade() -> None:
    op.drop_table("compliance_alerts")
    op.drop_table("compliance_checklists")
    op.drop_table("compliance_templates")

    # Remove indexes
    op.drop_index("ix_documents_expiration", "documents")
    op.drop_index("ix_documents_entity", "documents")

    # Remove added columns from documents
    for col in [
        "sous_type", "numero_document", "date_emission", "date_expiration",
        "date_prochaine_echeance", "organisme_emetteur", "tags", "version",
        "remplace_document_id", "statut", "validation_par", "validation_date",
        "motif_rejet", "is_critical",
        "alerte_j60_envoyee", "alerte_j30_envoyee", "alerte_j15_envoyee",
        "alerte_j7_envoyee", "alerte_j0_envoyee",
        "uploaded_by", "uploaded_by_role",
        "fichier_taille_octets", "fichier_mime_type",
    ]:
        op.drop_column("documents", col)
