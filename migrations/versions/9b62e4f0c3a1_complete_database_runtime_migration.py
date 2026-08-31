"""Complete the database-backed runtime schema.

Revision ID: 9b62e4f0c3a1
Revises: ce6f8924b21c
Create Date: 2026-08-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b62e4f0c3a1"
down_revision: Union[str, Sequence[str], None] = "ce6f8924b21c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("display_name", sa.String(length=150), nullable=True),
    )
    op.execute(
        """
        UPDATE users
        SET display_name = CASE username
            WHEN 'admin' THEN 'Dashboard Admin'
            WHEN 'coach' THEN 'Coaching Staff'
            WHEN 'player' THEN 'Jack O''Shea'
            WHEN 'viewer' THEN 'Read-only Viewer'
            ELSE username
        END
        """
    )
    op.alter_column(
        "users",
        "display_name",
        existing_type=sa.String(length=150),
        nullable=False,
    )

    op.alter_column(
        "matches",
        "home_score",
        existing_type=sa.String(length=50),
        type_=sa.Integer(),
        postgresql_using="home_score::integer",
    )
    op.alter_column(
        "matches",
        "away_score",
        existing_type=sa.String(length=50),
        type_=sa.Integer(),
        postgresql_using="away_score::integer",
    )


def downgrade() -> None:
    op.alter_column(
        "matches",
        "away_score",
        existing_type=sa.Integer(),
        type_=sa.String(length=50),
        postgresql_using="away_score::text",
    )
    op.alter_column(
        "matches",
        "home_score",
        existing_type=sa.Integer(),
        type_=sa.String(length=50),
        postgresql_using="home_score::text",
    )
    op.drop_column("users", "display_name")
