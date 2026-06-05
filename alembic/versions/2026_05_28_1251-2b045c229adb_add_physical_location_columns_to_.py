"""add_physical_location_columns_to_inventory

Revision ID: 2b045c229adb
Revises: 30daf3151e4c
Create Date: 2026-05-28 12:51:34.354023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b045c229adb'
down_revision: Union[str, Sequence[str], None] = '30daf3151e4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "inventory",
        sa.Column("physical_location_site", sa.String(length=100), nullable=True),
        schema="verity"
    )
    op.add_column(
        "inventory",
        sa.Column("physical_location_room", sa.String(length=100), nullable=True),
        schema="verity"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("inventory", "physical_location_room", schema="verity")
    op.drop_column("inventory", "physical_location_site", schema="verity")

