from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b0f9ecf6a41"
down_revision: Union[str, None] = "1e4ee2f02eac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("quests", sa.Column("module_name", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("quests", "module_name")
