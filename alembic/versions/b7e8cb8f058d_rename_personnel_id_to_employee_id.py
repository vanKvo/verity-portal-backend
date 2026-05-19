"""rename_personnel_id_to_employee_id

Revision ID: b7e8cb8f058d
Revises: 5122b545ca31
Create Date: 2026-05-19 10:00:01.702194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e8cb8f058d'
down_revision: Union[str, Sequence[str], None] = '5122b545ca31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('compliance_violations', 'personnel_id', new_column_name='employee_id', schema='verity')
    op.alter_column('project_assignments', 'personnel_id', new_column_name='employee_id', schema='verity')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('compliance_violations', 'employee_id', new_column_name='personnel_id', schema='verity')
    op.alter_column('project_assignments', 'employee_id', new_column_name='personnel_id', schema='verity')
