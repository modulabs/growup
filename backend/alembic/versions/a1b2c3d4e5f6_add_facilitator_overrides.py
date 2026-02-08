"""add facilitator_overrides table

Revision ID: a1b2c3d4e5f6
Revises: 5c8d676613a9
Create Date: 2026-02-08 22:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "5c8d676613a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facilitator_overrides",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("legacy_user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("legacy_user_id"),
    )
    op.create_index(
        op.f("ix_facilitator_overrides_legacy_user_id"),
        "facilitator_overrides",
        ["legacy_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_facilitator_overrides_legacy_user_id"),
        table_name="facilitator_overrides",
    )
    op.drop_table("facilitator_overrides")
