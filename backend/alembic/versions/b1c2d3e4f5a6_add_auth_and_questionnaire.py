"""add_auth_and_questionnaire

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users, questionnaire_sessions, questionnaire_answers, generated_workbooks tables."""
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'questionnaire_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('current_question_id', sa.String(), nullable=True),
        sa.Column('current_section', sa.Integer(), nullable=False),
        sa.Column('completed_count', sa.Integer(), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_questionnaire_sessions_user_id'), 'questionnaire_sessions', ['user_id'], unique=False)

    op.create_table(
        'questionnaire_answers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('question_id', sa.String(), nullable=False),
        sa.Column('section_number', sa.Integer(), nullable=False),
        sa.Column('answer_json', sa.Text(), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['questionnaire_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'question_id'),
    )

    op.create_table(
        'generated_workbooks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('plan_id', sa.String(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('workbook_json', sa.Text(), nullable=False),
        sa.Column('xlsx_token', sa.String(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['questionnaire_sessions.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('xlsx_token'),
    )


def downgrade() -> None:
    """Drop tables in reverse dependency order."""
    op.drop_table('generated_workbooks')
    op.drop_table('questionnaire_answers')
    op.drop_index(op.f('ix_questionnaire_sessions_user_id'), table_name='questionnaire_sessions')
    op.drop_table('questionnaire_sessions')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
