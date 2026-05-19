"""make_project_assignments_columns_plain_text

Revision ID: 38fee9f10239
Revises: b7e8cb8f058d
Create Date: 2026-05-19 10:06:58.070170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38fee9f10239'
down_revision: Union[str, Sequence[str], None] = 'b7e8cb8f058d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("TRUNCATE TABLE verity.project_assignments CASCADE")
    
    op.drop_constraint('project_assignments_personnel_id_fkey', 'project_assignments', schema='verity', type_='foreignkey')
    op.drop_constraint('project_assignments_project_id_fkey', 'project_assignments', schema='verity', type_='foreignkey')
    
    op.alter_column('project_assignments', 'project_id',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=False,
               schema='verity')
    op.alter_column('project_assignments', 'employee_id',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=False,
               schema='verity')
    op.create_foreign_key(None, 'project_assignments', 'personnel', ['employee_id'], ['employee_id'], source_schema='verity', referent_schema='verity')
    op.create_foreign_key(None, 'project_assignments', 'projects', ['project_id'], ['project_id'], source_schema='verity', referent_schema='verity')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("TRUNCATE TABLE verity.project_assignments CASCADE")
    
    op.drop_constraint(None, 'project_assignments', schema='verity', type_='foreignkey')
    op.drop_constraint(None, 'project_assignments', schema='verity', type_='foreignkey')
    op.create_foreign_key('project_assignments_project_id_fkey', 'project_assignments', 'projects', ['project_id'], ['id'], source_schema='verity', referent_schema='verity')
    op.create_foreign_key('project_assignments_personnel_id_fkey', 'project_assignments', 'personnel', ['employee_id'], ['id'], source_schema='verity', referent_schema='verity')
    op.alter_column('project_assignments', 'employee_id',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=False,
               schema='verity')
    op.alter_column('project_assignments', 'project_id',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=False,
               schema='verity')
