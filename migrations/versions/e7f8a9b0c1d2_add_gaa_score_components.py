"""Add GAA score components to matches.

Revision ID: e7f8a9b0c1d2
Revises: d4a7c8e1f2b3
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "d4a7c8e1f2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("home_goals", sa.Integer(), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column("home_points", sa.Integer(), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column("away_goals", sa.Integer(), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column("away_points", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("matches", "away_points")
    op.drop_column("matches", "away_goals")
    op.drop_column("matches", "home_points")
    op.drop_column("matches", "home_goals")
