"""Settings, notifications, audit trail, credit notes, password reset tokens.

Creates company_settings, bank_accounts, vat_configs, cost_centers,
notification_configs, audit_logs, notifications, credit_notes,
credit_note_lines, password_reset_tokens.
Adds invoices.format column.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # company_settings — single row per tenant
    # ------------------------------------------------------------------
    op.create_table(
        "company_settings",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("siren", sa.String(9)),
        sa.Column("siret", sa.String(14)),
        sa.Column("tva_intracom", sa.String(20)),
        sa.Column("raison_sociale", sa.String(255)),
        sa.Column("adresse_ligne1", sa.String(255)),
        sa.Column("adresse_ligne2", sa.String(255)),
        sa.Column("code_postal", sa.String(10)),
        sa.Column("ville", sa.String(100)),
        sa.Column("pays", sa.String(2), server_default=sa.text("'FR'")),
        sa.Column("telephone", sa.String(30)),
        sa.Column("email", sa.String(255)),
        sa.Column("site_web", sa.String(255)),
        sa.Column("licence_transport", sa.String(100)),
        sa.Column("logo_s3_key", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", name="uq_company_settings_tenant"),
    )

    # ------------------------------------------------------------------
    # bank_accounts — multi-row per tenant
    # ------------------------------------------------------------------
    op.create_table(
        "bank_accounts",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("iban", sa.String(34), nullable=False),
        sa.Column("bic", sa.String(11)),
        sa.Column("bank_name", sa.String(255)),
        sa.Column("is_default", sa.Boolean(),
                  server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_bank_accounts_tenant", "bank_accounts", ["tenant_id"])

    # ------------------------------------------------------------------
    # vat_configs — rate, label, mention_legale
    # ------------------------------------------------------------------
    op.create_table(
        "vat_configs",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("mention_legale", sa.Text()),
        sa.Column("is_default", sa.Boolean(),
                  server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(),
                  server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_vat_configs_tenant", "vat_configs", ["tenant_id"])

    # ------------------------------------------------------------------
    # cost_centers — code + label, unique per (tenant_id, code)
    # ------------------------------------------------------------------
    op.create_table(
        "cost_centers",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(),
                  server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_cost_centers_tenant_code"),
    )

    # ------------------------------------------------------------------
    # notification_configs — event_type, channels, recipients
    # ------------------------------------------------------------------
    op.create_table(
        "notification_configs",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("channels", sa.ARRAY(sa.String(20)), nullable=False,
                  server_default=sa.text("'{IN_APP}'")),
        sa.Column("recipients", sa.ARRAY(sa.String(50)),
                  server_default=sa.text("'{}'::varchar[]")),
        sa.Column("delay_hours", sa.Integer(), server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(),
                  server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_notification_configs_tenant", "notification_configs",
                     ["tenant_id"])

    # ------------------------------------------------------------------
    # audit_logs — immutable (no updated_at)
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID()),
        sa.Column("user_email", sa.String(255)),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(255)),
        sa.Column("old_value", sa.JSON()),
        sa.Column("new_value", sa.JSON()),
        sa.Column("metadata", sa.JSON()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs",
                     ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_user", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_created", "audit_logs", ["created_at"])

    # ------------------------------------------------------------------
    # notifications — user notifications
    # ------------------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("link", sa.String(500)),
        sa.Column("event_type", sa.String(50)),
        sa.Column("read", sa.Boolean(),
                  server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_user_read", "notifications",
                     ["user_id", "read"])

    # ------------------------------------------------------------------
    # credit_notes — avoir
    # ------------------------------------------------------------------
    op.create_table(
        "credit_notes",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credit_note_number", sa.String(30)),
        sa.Column("invoice_id", sa.UUID(),
                  sa.ForeignKey("invoices.id", ondelete="SET NULL")),
        sa.Column("customer_id", sa.UUID(),
                  sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(20),
                  server_default=sa.text("'draft'"), nullable=False),
        sa.Column("issue_date", sa.Date()),
        sa.Column("total_ht", sa.Numeric(12, 2), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("tva_rate", sa.Numeric(5, 2),
                  server_default=sa.text("20")),
        sa.Column("total_tva", sa.Numeric(12, 2), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("total_ttc", sa.Numeric(12, 2), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("pdf_s3_key", sa.String(500)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.UUID()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "credit_note_number",
                            name="uq_credit_notes_tenant_number"),
    )

    # ------------------------------------------------------------------
    # credit_note_lines
    # ------------------------------------------------------------------
    op.create_table(
        "credit_note_lines",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("credit_note_id", sa.UUID(),
                  sa.ForeignKey("credit_notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False,
                  server_default=sa.text("1")),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("amount_ht", sa.Numeric(12, 2), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("line_order", sa.Integer(), server_default=sa.text("0")),
    )
    op.create_index("ix_credit_note_lines_cn", "credit_note_lines",
                     ["credit_note_id"])

    # ------------------------------------------------------------------
    # password_reset_tokens
    # ------------------------------------------------------------------
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.UUID(), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )

    # ------------------------------------------------------------------
    # Add format column to invoices
    # ------------------------------------------------------------------
    op.add_column(
        "invoices",
        sa.Column("format", sa.String(30), server_default=sa.text("'pdf'")),
    )


def downgrade() -> None:
    op.drop_column("invoices", "format")
    op.drop_table("password_reset_tokens")
    op.drop_table("credit_note_lines")
    op.drop_table("credit_notes")
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("notification_configs")
    op.drop_table("cost_centers")
    op.drop_table("vat_configs")
    op.drop_table("bank_accounts")
    op.drop_table("company_settings")
