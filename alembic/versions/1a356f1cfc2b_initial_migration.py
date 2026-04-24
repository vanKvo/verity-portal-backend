"""initial migration

Revision ID: 1a356f1cfc2b
Revises: 642c029ec550
Create Date: 2026-04-24 10:41:19.890972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a356f1cfc2b'
down_revision: Union[str, Sequence[str], None] = '642c029ec550'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
