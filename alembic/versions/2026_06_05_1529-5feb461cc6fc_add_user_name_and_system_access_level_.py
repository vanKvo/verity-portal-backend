"""add user_name and system_access_level to it_activity

Revision ID: 5feb461cc6fc
Revises: b699913a0e4b
Create Date: 2026-06-05 15:29:09.735760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5feb461cc6fc'
down_revision: Union[str, Sequence[str], None] = 'b699913a0e4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('it_activity', sa.Column('user_name', sa.String(length=100), nullable=True), schema='verity')
    op.add_column('it_activity', sa.Column('system_access_level', sa.String(length=50), nullable=True), schema='verity')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('it_activity', 'system_access_level', schema='verity')
    op.drop_column('it_activity', 'user_name', schema='verity')
