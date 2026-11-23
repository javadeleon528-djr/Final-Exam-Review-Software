"""add sources and scope draft timestamp

Revision ID: b617e7c2a904
Revises: 8a241a626c1e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b617e7c2a904"
down_revision: Union[str, Sequence[str], None] = "8a241a626c1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scope_drafts",
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("course_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("uri", sa.String(length=2000), nullable=True),
        sa.Column("note_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("kind IN ('link', 'note')", name="ck_sources_kind"),
        sa.CheckConstraint("status = 'registered'", name="ck_sources_status"),
        sa.CheckConstraint(
            "(kind = 'link' AND uri IS NOT NULL AND note_text IS NULL) OR "
            "(kind = 'note' AND note_text IS NOT NULL AND uri IS NULL)",
            name="ck_sources_payload",
        ),
    )
    op.create_index("ix_sources_course_created", "sources", ["course_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_sources_course_created", table_name="sources")
    op.drop_table("sources")
    op.drop_column("scope_drafts", "updated_at")
