"""add columns for auditing and leaver details

Revision ID: b963922487bc
Revises: 5feb461cc6fc
Create Date: 2026-06-05 16:23:11.200439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b963922487bc'
down_revision: Union[str, Sequence[str], None] = '5feb461cc6fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('asset_violations', sa.Column('resolved_by', sa.String(length=255), nullable=True), schema='verity')
    op.add_column('asset_violations', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True), schema='verity')
    op.add_column('compliance_violations', sa.Column('resolved_by', sa.String(length=255), nullable=True), schema='verity')
    op.add_column('leaver_violations', sa.Column('system_name', sa.String(length=100), nullable=True), schema='verity')
    op.add_column('leaver_violations', sa.Column('ip_address', sa.String(length=45), nullable=True), schema='verity')
    op.create_table(
        'ingestion_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('schema_type', sa.String(length=50), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('uploaded_by', sa.String(length=255), nullable=False),
        sa.Column('records_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='verity'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ingestion_logs', schema='verity')
    op.drop_column('leaver_violations', 'ip_address', schema='verity')
    op.drop_column('leaver_violations', 'system_name', schema='verity')
    op.drop_column('compliance_violations', 'resolved_by', schema='verity')
    op.drop_column('asset_violations', 'resolved_at', schema='verity')
    op.drop_column('asset_violations', 'resolved_by', schema='verity')
