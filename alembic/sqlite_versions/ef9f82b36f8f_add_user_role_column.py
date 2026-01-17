"""add_user_role_column

Revision ID: ef9f82b36f8f
Revises: ed65e845dd8a
Create Date: 2026-01-12 07:08:25.837733

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef9f82b36f8f"
down_revision: str | Sequence[str] | None = "ed65e845dd8a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users", sa.Column("role", sa.String(20), nullable=False, server_default="user")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
