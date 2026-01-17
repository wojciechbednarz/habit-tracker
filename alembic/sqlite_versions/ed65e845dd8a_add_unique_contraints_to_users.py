"""add_unique_contraints_to_users

Revision ID: ed65e845dd8a
Revises: 71e059a1ab6b
Create Date: 2026-01-07 14:04:58.290832

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ed65e845dd8a"
down_revision: str | Sequence[str] | None = "71e059a1ab6b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "email", existing_type=sa.VARCHAR(length=60), nullable=False
        )
        batch_op.create_unique_constraint("uq_users_email", ["email"])
        batch_op.create_unique_constraint("uq_users_username", ["username"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("uq_users_username", type_="unique")
        batch_op.drop_constraint("uq_users_email", type_="unique")
        batch_op.alter_column(
            "email", existing_type=sa.VARCHAR(length=60), nullable=True
        )
