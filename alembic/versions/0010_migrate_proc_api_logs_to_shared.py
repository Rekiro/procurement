"""Migrate proc_api_logs rows into the shared api_logs table, then drop proc_api_logs.

Prerequisite: Account Master must have run its 0001 migration first, which
creates the shared `api_logs` table. Procurement and accountMaster can be
applied in either order normally — but this specific revision depends on
api_logs existing.

Column mapping (proc_api_logs → api_logs):
  - id (uuid)        → (auto-assigned BigInt; old UUIDs discarded)
  - (n/a)            → module = 'PROCUREMENT'
  - response_id      → request_id   (renamed)
  - timestamp        → timestamp
  - method           → method
  - path             → path
  - status_code      → status_code
  - duration_ms      → duration_ms
  - user_email       → user_id      (procurement historically stored an email
                                     here; preserved as-is until procurement
                                     migrates to the shared users table)
  - user_role        → user_role
  - client_ip        → ip_address   (renamed)
  - request_body     → request_body
  - response_body    → response_body
  - (n/a)            → user_agent = NULL
  - (n/a)            → error = NULL

Revision ID: 0010
Revises: 0009
Create Date: 2026-04-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Hard precondition — api_logs must already exist (created by accountMaster's
    # 0001 migration). Fail loudly with a clear message rather than silently
    # losing 700+ historical log rows.
    exists = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='api_logs'"
        )
    ).scalar()
    if not exists:
        raise RuntimeError(
            "Cannot migrate proc_api_logs: shared `api_logs` table is missing. "
            "Run accountMaster's alembic upgrade first "
            "(cd accountMaster && alembic upgrade head)."
        )

    op.execute(
        """
        INSERT INTO api_logs (
            module, request_id, timestamp, method, path, status_code,
            duration_ms, user_id, user_role, ip_address, user_agent,
            request_body, response_body, error
        )
        SELECT
            'PROCUREMENT'         AS module,
            response_id           AS request_id,
            timestamp,
            method,
            path,
            status_code,
            duration_ms,
            user_email            AS user_id,
            user_role,
            client_ip             AS ip_address,
            NULL                  AS user_agent,
            request_body,
            response_body,
            NULL                  AS error
        FROM proc_api_logs
        ORDER BY timestamp
        """
    )

    op.drop_index("ix_proc_api_logs_response_id", table_name="proc_api_logs")
    op.drop_index("ix_proc_api_logs_user_email", table_name="proc_api_logs")
    op.drop_index("ix_proc_api_logs_timestamp", table_name="proc_api_logs")
    op.drop_table("proc_api_logs")


def downgrade() -> None:
    """Recreate proc_api_logs and copy PROCUREMENT-tagged rows back.

    Caveat: original UUID `id` and `response_id` values are not recovered
    (they were discarded on upgrade). New UUIDs are generated for both.
    """
    from sqlalchemy.dialects import postgresql

    op.create_table(
        "proc_api_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(2048), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("user_role", sa.String(50), nullable=True),
        sa.Column("request_body", postgresql.JSONB, nullable=True),
        sa.Column("response_body", postgresql.JSONB, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=False),
        sa.Column("client_ip", sa.String(45), nullable=True),
        sa.Column("response_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_proc_api_logs_timestamp", "proc_api_logs", ["timestamp"])
    op.create_index("ix_proc_api_logs_user_email", "proc_api_logs", ["user_email"])
    op.create_index("ix_proc_api_logs_response_id", "proc_api_logs", ["response_id"])

    op.execute(
        """
        INSERT INTO proc_api_logs (
            id, timestamp, method, path, status_code,
            user_email, user_role, request_body, response_body,
            duration_ms, client_ip, response_id
        )
        SELECT
            gen_random_uuid()  AS id,
            timestamp,
            method,
            path,
            status_code,
            user_id            AS user_email,
            user_role,
            request_body,
            response_body,
            duration_ms,
            ip_address         AS client_ip,
            request_id         AS response_id
        FROM api_logs
        WHERE module = 'PROCUREMENT'
        ORDER BY timestamp
        """
    )
    op.execute("DELETE FROM api_logs WHERE module = 'PROCUREMENT'")
