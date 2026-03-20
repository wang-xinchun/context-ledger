"""add read-path performance indexes

Revision ID: 20260320_0002
Revises: 20260320_0001
Create Date: 2026-03-20 11:20:00
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260320_0002"
down_revision = "20260320_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_turns_project_role_created_at",
        "turns",
        ["project_id", "role", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_timeline_project_created_at_id",
        "timeline_events",
        ["project_id", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "idx_timeline_project_memory_id",
        "timeline_events",
        ["project_id", "memory_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_timeline_project_memory_id", table_name="timeline_events")
    op.drop_index("idx_timeline_project_created_at_id", table_name="timeline_events")
    op.drop_index("idx_turns_project_role_created_at", table_name="turns")

