"""add_phase_8_models

Revision ID: b699913a0e4b
Revises: a5ee807dc37d
Create Date: 2026-06-05 14:48:06.297900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b699913a0e4b'
down_revision: Union[str, Sequence[str], None] = 'a5ee807dc37d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('it_activity',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('last_system_login', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('system_name', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='verity'
    )
    op.create_index(op.f('ix_verity_it_activity_employee_id'), 'it_activity', ['employee_id'], unique=True, schema='verity')

    op.create_table('leaver_violations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('hr_termination_date', sa.Date(), nullable=False),
        sa.Column('last_system_login', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'RESOLVED', name='leaverviolationstatus'), nullable=False),
        sa.Column('resolution_reason', sa.String(length=500), nullable=True),
        sa.Column('resolved_by', sa.String(length=255), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['verity.personnel.employee_id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='verity'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('leaver_violations', schema='verity')
    op.drop_index(op.f('ix_verity_it_activity_employee_id'), table_name='it_activity', schema='verity')
    op.drop_table('it_activity', schema='verity')
    # Note: postgres automatically drops the ENUM type if not referenced, or we can drop it if needed.
    # But Alembic handles Postgres Enum drop cleanly if bound.
    # To be safe and clean, we can drop the enum type if needed, but standard is fine.

