"""add must_change_password to users

Revision ID: 050259b2eeac
Revises: 0001_initial_iam_schema
Create Date: 2026-06-16 23:27:44.753361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '050259b2eeac'
down_revision: Union[str, None] = '0001_initial_iam_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
