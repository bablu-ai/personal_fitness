"""add_questionnaire_snapshots

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-05-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "questionnaire_questions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("section_number", sa.Integer(), nullable=False),
        sa.Column("question_number", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(), nullable=False),
        sa.Column("options_json", sa.Text(), nullable=True),
        sa.Column("required", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("placeholder", sa.Text(), nullable=True),
        sa.Column("conditional_json", sa.Text(), nullable=True),
        sa.Column("validation_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "version"),
    )
    op.create_index(
        op.f("ix_questionnaire_questions_question_id"),
        "questionnaire_questions",
        ["question_id"],
        unique=False,
    )

    with op.batch_alter_table("questionnaire_sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("questionnaire_version", sa.Integer(), server_default="1", nullable=False)
        )

    with op.batch_alter_table("questionnaire_answers", schema=None) as batch_op:
        batch_op.add_column(sa.Column("question_snapshot_id", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_questionnaire_answers_question_snapshot_id",
            "questionnaire_questions",
            ["question_snapshot_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("questionnaire_answers", schema=None) as batch_op:
        batch_op.drop_constraint("fk_questionnaire_answers_question_snapshot_id", type_="foreignkey")
        batch_op.drop_column("question_snapshot_id")

    with op.batch_alter_table("questionnaire_sessions", schema=None) as batch_op:
        batch_op.drop_column("questionnaire_version")

    op.drop_index(op.f("ix_questionnaire_questions_question_id"), table_name="questionnaire_questions")
    op.drop_table("questionnaire_questions")
