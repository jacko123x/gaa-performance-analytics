"""Add match lifecycle and audit history.

Revision ID: d4a7c8e1f2b3
Revises: 9b62e4f0c3a1
Create Date: 2026-08-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4a7c8e1f2b3"
down_revision: Union[str, Sequence[str], None] = "9b62e4f0c3a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Published",
        ),
    )
    op.add_column(
        "matches",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "matches",
        sa.Column("published_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column(
            "published_by",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE matches SET published_at = created_at, "
        "published_by = 'migration'"
    )
    op.create_check_constraint(
        "ck_matches_status",
        "matches",
        "status IN ('Draft', 'Review', 'Published')",
    )
    op.alter_column("matches", "status", server_default=None)
    op.alter_column("matches", "updated_at", server_default=None)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("dataset", sa.String(length=50), nullable=True),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["matches.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_events_match_created",
        "audit_events",
        ["match_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_events_match_created",
        table_name="audit_events",
    )
    op.drop_table("audit_events")
    op.drop_constraint("ck_matches_status", "matches", type_="check")
    op.drop_column("matches", "published_by")
    op.drop_column("matches", "published_at")
    op.drop_column("matches", "updated_at")
    op.drop_column("matches", "status")
