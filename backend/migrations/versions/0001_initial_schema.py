"""Initial schema — consolidated.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Tenants
    # ------------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("siren", sa.String(9)),
        sa.Column("address", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ------------------------------------------------------------------
    # Agencies
    # ------------------------------------------------------------------
    op.create_table(
        "agencies",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20)),
        sa.Column("address", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_agencies_tenant", "agencies", ["tenant_id"])

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("permissions", sa.JSON(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_id", sa.UUID(), sa.ForeignKey("agencies.id", ondelete="SET NULL")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role_id", sa.UUID(), sa.ForeignKey("roles.id", ondelete="SET NULL")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )
    op.create_index("ix_users_tenant", "users", ["tenant_id"])

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("siren", sa.String(9)),
        sa.Column("address", sa.Text()),
        sa.Column("contact_name", sa.String(255)),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("contact_phone", sa.String(30)),
        sa.Column("payment_terms_days", sa.Integer(), server_default=sa.text("30")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_customers_tenant", "customers", ["tenant_id"])

    # ------------------------------------------------------------------
    # Suppliers
    # ------------------------------------------------------------------
    op.create_table(
        "suppliers",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("siren", sa.String(9)),
        sa.Column("address", sa.Text()),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("contact_phone", sa.String(30)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_suppliers_tenant", "suppliers", ["tenant_id"])

    # ------------------------------------------------------------------
    # Drivers
    # ------------------------------------------------------------------
    op.create_table(
        "drivers",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_id", sa.UUID(), sa.ForeignKey("agencies.id", ondelete="SET NULL")),
        sa.Column("matricule", sa.String(20)),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("license_number", sa.String(50)),
        sa.Column("license_categories", sa.String(50)),
        sa.Column("phone", sa.String(30)),
        sa.Column("email", sa.String(255)),
        sa.Column("hire_date", sa.Date()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "matricule", name="uq_drivers_tenant_matricule"),
    )
    op.create_index("ix_drivers_tenant", "drivers", ["tenant_id"])

    # ------------------------------------------------------------------
    # Vehicles
    # ------------------------------------------------------------------
    op.create_table(
        "vehicles",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_id", sa.UUID(), sa.ForeignKey("agencies.id", ondelete="SET NULL")),
        sa.Column("plate_number", sa.String(20), nullable=False),
        sa.Column("vin", sa.String(17)),
        sa.Column("brand", sa.String(100)),
        sa.Column("model", sa.String(100)),
        sa.Column("vehicle_type", sa.String(50)),
        sa.Column("payload_kg", sa.Numeric(10, 2)),
        sa.Column("first_registration", sa.Date()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "plate_number", name="uq_vehicles_tenant_plate"),
    )
    op.create_index("ix_vehicles_tenant", "vehicles", ["tenant_id"])

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_id", sa.UUID(), sa.ForeignKey("agencies.id", ondelete="SET NULL")),
        sa.Column("reference", sa.String(50)),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("driver_id", sa.UUID(), sa.ForeignKey("drivers.id", ondelete="SET NULL")),
        sa.Column("vehicle_id", sa.UUID(), sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(30), server_default=sa.text("'draft'")),
        sa.Column("pickup_address", sa.Text()),
        sa.Column("delivery_address", sa.Text()),
        sa.Column("pickup_date", sa.DateTime(timezone=True)),
        sa.Column("delivery_date", sa.DateTime(timezone=True)),
        sa.Column("distance_km", sa.Numeric(10, 2)),
        sa.Column("weight_kg", sa.Numeric(10, 2)),
        sa.Column("goods_description", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("pod_s3_key", sa.Text()),
        sa.Column("pod_uploaded_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_jobs_tenant", "jobs", ["tenant_id"])
    op.create_index("ix_jobs_status", "jobs", ["tenant_id", "status"])
    op.create_index("ix_jobs_driver", "jobs", ["driver_id"])

    # ------------------------------------------------------------------
    # Documents (driver/vehicle compliance docs)
    # ------------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),  # driver | vehicle
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("doc_type", sa.String(100), nullable=False),
        sa.Column("s3_key", sa.Text()),
        sa.Column("file_name", sa.String(255)),
        sa.Column("issue_date", sa.Date()),
        sa.Column("expiry_date", sa.Date()),
        sa.Column("compliance_status", sa.String(30), server_default=sa.text("'valid'")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_documents_tenant", "documents", ["tenant_id"])
    op.create_index("ix_documents_entity", "documents", ["entity_type", "entity_id"])
    op.create_index("ix_documents_expiry", "documents", ["expiry_date"])

    # ------------------------------------------------------------------
    # Document types (per-tenant config)
    # ------------------------------------------------------------------
    op.create_table(
        "document_types",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("validity_months", sa.Integer()),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.text("false")),
        sa.UniqueConstraint("tenant_id", "entity_type", "code", name="uq_doctypes_tenant_entity_code"),
    )

    # ------------------------------------------------------------------
    # Pricing rules
    # ------------------------------------------------------------------
    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="CASCADE")),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("rule_type", sa.String(30), nullable=False),  # km | flat | surcharge
        sa.Column("rate", sa.Numeric(12, 4), nullable=False),
        sa.Column("min_km", sa.Numeric(10, 2)),
        sa.Column("max_km", sa.Numeric(10, 2)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_pricing_rules_tenant", "pricing_rules", ["tenant_id"])

    # ------------------------------------------------------------------
    # Number sequences (for invoices)
    # ------------------------------------------------------------------
    op.create_table(
        "number_sequences",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prefix", sa.String(20), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("last_number", sa.Integer(), server_default=sa.text("0")),
        sa.UniqueConstraint("tenant_id", "prefix", "year", "month", name="uq_numseq_tenant_prefix_ym"),
    )

    # ------------------------------------------------------------------
    # Invoices
    # ------------------------------------------------------------------
    op.create_table(
        "invoices",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("invoice_number", sa.String(30)),
        sa.Column("status", sa.String(30), server_default=sa.text("'draft'")),
        sa.Column("issue_date", sa.Date()),
        sa.Column("due_date", sa.Date()),
        sa.Column("total_ht", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("tva_rate", sa.Numeric(5, 2), server_default=sa.text("20.00")),
        sa.Column("total_tva", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("total_ttc", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("pdf_s3_key", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("validated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "invoice_number", name="uq_invoices_tenant_number"),
    )
    op.create_index("ix_invoices_tenant", "invoices", ["tenant_id"])
    op.create_index("ix_invoices_status", "invoices", ["tenant_id", "status"])

    # ------------------------------------------------------------------
    # Invoice lines
    # ------------------------------------------------------------------
    op.create_table(
        "invoice_lines",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_id", sa.UUID(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="SET NULL")),
        sa.Column("description", sa.Text()),
        sa.Column("quantity", sa.Numeric(10, 2), server_default=sa.text("1")),
        sa.Column("unit_price", sa.Numeric(12, 4), server_default=sa.text("0")),
        sa.Column("amount_ht", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("line_order", sa.Integer(), server_default=sa.text("0")),
    )
    op.create_index("ix_invoice_lines_invoice", "invoice_lines", ["invoice_id"])

    # ------------------------------------------------------------------
    # Payroll periods
    # ------------------------------------------------------------------
    op.create_table(
        "payroll_periods",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), server_default=sa.text("'draft'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "year", "month", name="uq_payroll_period_tenant_ym"),
    )

    # ------------------------------------------------------------------
    # Payroll variable types
    # ------------------------------------------------------------------
    op.create_table(
        "payroll_variable_types",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(20)),
        sa.Column("category", sa.String(50)),
        sa.UniqueConstraint("tenant_id", "code", name="uq_payvar_types_tenant_code"),
    )

    # ------------------------------------------------------------------
    # Payroll variables
    # ------------------------------------------------------------------
    op.create_table(
        "payroll_variables",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_id", sa.UUID(), sa.ForeignKey("payroll_periods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", sa.UUID(), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variable_type_id", sa.UUID(), sa.ForeignKey("payroll_variable_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("period_id", "driver_id", "variable_type_id", name="uq_payvar_period_driver_type"),
    )
    op.create_index("ix_payroll_variables_period", "payroll_variables", ["period_id"])

    # ------------------------------------------------------------------
    # Payroll mappings (SILAE export mapping)
    # ------------------------------------------------------------------
    op.create_table(
        "payroll_mappings",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variable_type_code", sa.String(50), nullable=False),
        sa.Column("target_code", sa.String(50), nullable=False),
        sa.Column("target_label", sa.String(255)),
        sa.UniqueConstraint("tenant_id", "variable_type_code", name="uq_paymap_tenant_varcode"),
    )

    # ------------------------------------------------------------------
    # Supplier invoices
    # ------------------------------------------------------------------
    op.create_table(
        "supplier_invoices",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", sa.UUID(), sa.ForeignKey("suppliers.id", ondelete="SET NULL")),
        sa.Column("invoice_number", sa.String(50)),
        sa.Column("invoice_date", sa.Date()),
        sa.Column("total_ht", sa.Numeric(12, 2)),
        sa.Column("total_tva", sa.Numeric(12, 2)),
        sa.Column("total_ttc", sa.Numeric(12, 2)),
        sa.Column("s3_key", sa.Text()),
        sa.Column("status", sa.String(30), server_default=sa.text("'pending'")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_supplier_invoices_tenant", "supplier_invoices", ["tenant_id"])

    # ------------------------------------------------------------------
    # OCR jobs
    # ------------------------------------------------------------------
    op.create_table(
        "ocr_jobs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("s3_key", sa.Text(), nullable=False),
        sa.Column("file_name", sa.String(255)),
        sa.Column("status", sa.String(30), server_default=sa.text("'pending'")),
        sa.Column("provider", sa.String(30)),
        sa.Column("extracted_data", sa.JSON()),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("supplier_invoice_id", sa.UUID(), sa.ForeignKey("supplier_invoices.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_ocr_jobs_tenant", "ocr_jobs", ["tenant_id"])

    # ------------------------------------------------------------------
    # Tasks (task center)
    # ------------------------------------------------------------------
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", sa.String(36)),
        sa.Column("assigned_to", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("due_date", sa.Date()),
        sa.Column("status", sa.String(30), server_default=sa.text("'open'")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_tasks_tenant", "tasks", ["tenant_id"])
    op.create_index("ix_tasks_status", "tasks", ["tenant_id", "status"])


def downgrade() -> None:
    tables = [
        "tasks", "ocr_jobs", "supplier_invoices",
        "payroll_mappings", "payroll_variables", "payroll_variable_types", "payroll_periods",
        "invoice_lines", "invoices", "number_sequences", "pricing_rules",
        "document_types", "documents",
        "jobs", "vehicles", "drivers", "suppliers", "customers",
        "users", "roles", "agencies", "tenants",
    ]
    for t in tables:
        op.drop_table(t)
