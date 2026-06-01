"""Initial IAM database schema

Revision ID: 0001_initial_iam_schema
Revises:
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_iam_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.VARCHAR(length=255),
            nullable=False,
        ),
        sa.Column(
            "full_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "last_login",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "role IN ('donor', 'charity_representative', 'admin', 'super_admin')",
            name="check_user_role",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="check_user_status",
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_index(
        "idx_users_role",
        "users",
        ["role"],
        unique=False,
    )

    op.create_index(
        "idx_users_status",
        "users",
        ["status"],
        unique=False,
    )

    op.create_index(
        "idx_users_is_verified",
        "users",
        ["is_verified"],
        unique=False,
    )

    op.create_index(
        "unique_single_super_admin",
        "users",
        ["role"],
        unique=True,
        postgresql_where=sa.text("role = 'super_admin'"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "token",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_refresh_tokens_token"),
    )

    op.create_index(
        "idx_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_refresh_tokens_user_id",
        table_name="refresh_tokens",
    )

    op.drop_table("refresh_tokens")

    op.drop_index(
        "unique_single_super_admin",
        table_name="users",
    )

    op.drop_index(
        "idx_users_is_verified",
        table_name="users",
    )

    op.drop_index(
        "idx_users_status",
        table_name="users",
    )

    op.drop_index(
        "idx_users_role",
        table_name="users",
    )

    op.drop_table("users")