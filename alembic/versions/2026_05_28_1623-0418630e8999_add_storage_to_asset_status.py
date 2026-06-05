"""add_storage_to_asset_status

Revision ID: 0418630e8999
Revises: 2b045c229adb
Create Date: 2026-05-28 16:23:13.026728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0418630e8999'
down_revision: Union[str, Sequence[str], None] = '2b045c229adb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE public.assetstatus ADD VALUE 'STORAGE'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres does not support removing values from an ENUM type via ALTER TYPE.
    # Therefore, downgrade is a no-op.
    pass
