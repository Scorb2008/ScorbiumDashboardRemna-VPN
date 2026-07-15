"""rename pasarguard_key_id to remnawave_key_id

Revision ID: a0b1c2d3e4f5
Revises: f9a0b1c2d3e4
Create Date: 2026-07-15 19:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "f9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
        ),
        {"t": table, "c": column},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "vpn_keys", "pasarguard_key_id") and not _column_exists(
        conn, "vpn_keys", "remnawave_key_id"
    ):
        op.alter_column(
            "vpn_keys", "pasarguard_key_id", new_column_name="remnawave_key_id"
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "vpn_keys", "remnawave_key_id") and not _column_exists(
        conn, "vpn_keys", "pasarguard_key_id"
    ):
        op.alter_column(
            "vpn_keys", "remnawave_key_id", new_column_name="pasarguard_key_id"
        )
