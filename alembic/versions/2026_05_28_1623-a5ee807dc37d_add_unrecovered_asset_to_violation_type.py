"""add_unrecovered_asset_to_violation_type

Revision ID: a5ee807dc37d
Revises: 0418630e8999
Create Date: 2026-05-28 16:23:38.182008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5ee807dc37d'
down_revision: Union[str, Sequence[str], None] = '0418630e8999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE public.assetviolationtype ADD VALUE 'UNRECOVERED_ASSET'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL does not support dropping enum values; downgrade is a no-op.
    pass
