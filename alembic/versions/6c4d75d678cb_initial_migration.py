"""initial migration

Revision ID: 6c4d75d678cb
Revises: 1a356f1cfc2b
Create Date: 2026-04-24 10:41:45.529315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c4d75d678cb'
down_revision: Union[str, Sequence[str], None] = '1a356f1cfc2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
