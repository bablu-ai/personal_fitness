"""add_exercises_json_to_task_template

Revision ID: a1b2c3d4e5f6
Revises: 930832d8e721
Create Date: 2026-05-16 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '930832d8e721'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('task_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('exercises_json', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('task_templates', schema=None) as batch_op:
        batch_op.drop_column('exercises_json')
