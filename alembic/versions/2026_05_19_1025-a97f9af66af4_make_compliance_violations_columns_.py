"""make_compliance_violations_columns_plain_text

Revision ID: a97f9af66af4
Revises: 38fee9f10239
Create Date: 2026-05-19 10:25:40.516097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a97f9af66af4'
down_revision: Union[str, Sequence[str], None] = '38fee9f10239'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("TRUNCATE TABLE verity.compliance_violations CASCADE")
    
    op.drop_constraint('compliance_violations_personnel_id_fkey', 'compliance_violations', schema='verity', type_='foreignkey')
    op.drop_constraint('compliance_violations_project_id_fkey', 'compliance_violations', schema='verity', type_='foreignkey')
    
    op.alter_column('compliance_violations', 'employee_id',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=False,
               schema='verity')
    op.alter_column('compliance_violations', 'project_id',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=False,
               schema='verity')
    op.create_foreign_key(None, 'compliance_violations', 'projects', ['project_id'], ['project_id'], source_schema='verity', referent_schema='verity')
    op.create_foreign_key(None, 'compliance_violations', 'personnel', ['employee_id'], ['employee_id'], source_schema='verity', referent_schema='verity')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("TRUNCATE TABLE verity.compliance_violations CASCADE")
    
    op.drop_constraint(None, 'compliance_violations', schema='verity', type_='foreignkey')
    op.drop_constraint(None, 'compliance_violations', schema='verity', type_='foreignkey')
    op.create_foreign_key('compliance_violations_project_id_fkey', 'compliance_violations', 'projects', ['project_id'], ['id'], source_schema='verity', referent_schema='verity')
    op.create_foreign_key('compliance_violations_personnel_id_fkey', 'compliance_violations', 'personnel', ['employee_id'], ['id'], source_schema='verity', referent_schema='verity')
    op.alter_column('compliance_violations', 'project_id',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=False,
               schema='verity')
    op.alter_column('compliance_violations', 'employee_id',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=False,
               schema='verity')
