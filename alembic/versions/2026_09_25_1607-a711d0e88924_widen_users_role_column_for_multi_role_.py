"""widen users role column for multi-role guest support

Revision ID: a711d0e88924
Revises: b963922487bc
Create Date: 2026-09-25 16:07:43.075062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a711d0e88924'
down_revision: Union[str, Sequence[str], None] = 'b963922487bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'users', 'role',
        existing_type=sa.String(length=50),
        type_=sa.String(length=255),
        existing_nullable=False,
        schema='verity',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'users', 'role',
        existing_type=sa.String(length=255),
        type_=sa.String(length=50),
        existing_nullable=False,
        schema='verity',
    )
