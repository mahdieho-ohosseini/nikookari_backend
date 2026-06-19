"""add must_change_password to users

Revision ID: 050259b2eeac
Revises: 0001_initial_iam_schema
Create Date: 2026-06-16 23:27:44.753361
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "050259b2eeac"
down_revision: Union[str, None] = "0001_initial_iam_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )

    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=20),
        type_=sa.String(length=30),
        existing_nullable=False,
    )

    op.drop_constraint(
        "check_user_role",
        "users",
        type_="check",
    )

    op.create_check_constraint(
        "check_user_role",
        "users",
        "role IN ('donor', 'charity', 'verifier', 'admin')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "check_user_role",
        "users",
        type_="check",
    )

    op.create_check_constraint(
        "check_user_role",
        "users",
        "role IN ('donor', 'charity_representative', 'admin', 'super_admin')",
    )

    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=30),
        type_=sa.String(length=20),
        existing_nullable=False,
    )

    op.drop_column("users", "must_change_password")