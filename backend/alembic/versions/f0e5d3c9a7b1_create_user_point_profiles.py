"""create user_point_profiles

Revision ID: f0e5d3c9a7b1
Revises: ecbab1f997dc
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f0e5d3c9a7b1"
down_revision: Union[str, Sequence[str], None] = "ecbab1f997dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_point_profiles",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("point_id", sa.String(length=64), nullable=False),
        sa.Column("self_status", sa.String(length=20), nullable=False),
        sa.Column("ai_status", sa.String(length=20), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("self_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ai_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("user_id", "point_id"),
        sa.ForeignKeyConstraint(["point_id"], ["knowledge_points.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "self_status IN ('not_started', 'not_mastered', 'basic', 'mastered')",
            name="ck_profile_self_status",
        ),
        sa.CheckConstraint(
            "ai_status IS NULL OR ai_status IN ('not_started', 'not_mastered', 'basic', 'mastered')",
            name="ck_profile_ai_status",
        ),
        sa.CheckConstraint("version >= 1", name="ck_profile_version"),
    )


def downgrade() -> None:
    op.drop_table("user_point_profiles")
