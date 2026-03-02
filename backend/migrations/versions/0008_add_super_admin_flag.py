"""Add is_super_admin flag to users table.

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_super_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    # Partial index for quick super-admin lookups
    op.create_index(
        "ix_users_super_admin",
        "users",
        ["is_super_admin"],
        postgresql_where=sa.text("is_super_admin = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_super_admin", table_name="users")
    op.drop_column("users", "is_super_admin")
