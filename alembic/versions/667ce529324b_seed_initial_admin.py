"""seed_initial_admin

Revision ID: 667ce529324b
Revises: a8f30d9d343d
Create Date: 2026-05-14 14:23:29.432144

"""

import os
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from pwdlib import PasswordHash

from alembic import op

revision: str = "<auto>"
down_revision: str | Sequence[str] | None = "a8f30d9d343d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()

    admin_username = os.environ["ADMIN_USERNAME"]
    admin_email = os.environ["ADMIN_EMAIL"]
    admin_password = os.environ["ADMIN_PASSWORD"]

    existing = bind.execute(sa.text("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1")).scalar()
    if existing:
        return

    hashed = PasswordHash.recommended().hash(admin_password)

    bind.execute(
        sa.text("""
            INSERT INTO users (user_id, username, email, nickname,
                                disabled, hashed_password, role)
            VALUES (:uid, :username, :email, :nickname,
                    false, :hashed, 'admin')
            ON CONFLICT (username) DO UPDATE SET role = 'admin'
        """),
        {
            "uid": str(uuid.uuid4()),
            "username": admin_username,
            "email": admin_email,
            "nickname": "Administrator",
            "hashed": hashed,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    admin_username = os.environ.get("ADMIN_USERNAME")
    if admin_username:
        bind.execute(
            sa.text("DELETE FROM users WHERE username = :u AND role = 'admin'"),
            {"u": admin_username},
        )
