"""add_plan_status_task_origin_todo_override

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-05-17 12:00:00.000000

Adds review-lifecycle / concurrency-guard columns (MODIFY_WORKSHEET_PLAN_FINAL §5):
- plans.status            review lifecycle: draft|active|archived
- plans.json_version      bumped on every plan_json write (stale-base 409 guard)
- task_templates.origin   ingest|user_added|user_edited|agent_fixed
- daily_todos.override_json  per-day overlay JSON (nullable)

SQLite cannot ALTER TABLE in place, so every change uses batch_alter_table.
server_default is set on the NOT NULL columns so existing rows backfill safely.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('status', sa.String(), nullable=False, server_default='active')
        )
        batch_op.add_column(
            sa.Column('json_version', sa.Integer(), nullable=False, server_default='1')
        )

    with op.batch_alter_table('task_templates', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('origin', sa.String(), nullable=False, server_default='ingest')
        )

    with op.batch_alter_table('daily_todos', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('override_json', sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table('daily_todos', schema=None) as batch_op:
        batch_op.drop_column('override_json')

    with op.batch_alter_table('task_templates', schema=None) as batch_op:
        batch_op.drop_column('origin')

    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.drop_column('json_version')
        batch_op.drop_column('status')
