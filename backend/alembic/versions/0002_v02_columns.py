"""Add v02 schema columns and surface_turns table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-04

Converts the manual `ensure_v02_schema()` patches into tracked Alembic
migrations. Each change is idempotent (checks before altering) so it is
safe to run against databases that already applied `ensure_v02_schema`.

Changes:
  runs        → add session_id (VARCHAR, nullable)
  memories    → add scope_type, scope_id, source_run_id, salience,
                    status, structured_payload, supersedes_id,
                    last_recalled_at, recall_count
  surface_turns → create table if not present
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return column in {col["name"] for col in insp.get_columns(table)}


def _add_if_missing(table: str, column: str, col_type: sa.types.TypeEngine, server_default: str | None = None) -> None:
    if not _column_exists(table, column):
        op.add_column(table, sa.Column(column, col_type, server_default=server_default, nullable=True))


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    datetime_type: sa.types.TypeEngine = sa.TIMESTAMP() if is_pg else sa.DateTime()

    # -- runs ----------------------------------------------------------------
    _add_if_missing("runs", "session_id", sa.String())

    # -- memories ------------------------------------------------------------
    _add_if_missing("memories", "scope_type", sa.String(), server_default="workspace")
    _add_if_missing("memories", "scope_id", sa.String())
    _add_if_missing("memories", "source_run_id", sa.String())
    _add_if_missing("memories", "salience", sa.Float(), server_default="0.5")
    _add_if_missing("memories", "status", sa.String(), server_default="candidate")
    _add_if_missing("memories", "structured_payload", sa.JSON())
    _add_if_missing("memories", "supersedes_id", sa.String())
    _add_if_missing("memories", "last_recalled_at", datetime_type)
    _add_if_missing("memories", "recall_count", sa.Integer(), server_default="0")

    # Backfill status for rows that pre-date the column.
    op.execute(
        sa.text(
            "UPDATE memories "
            "SET status = CASE WHEN is_confirmed THEN 'confirmed' ELSE 'candidate' END "
            "WHERE status IS NULL OR status = ''"
        )
    )
    op.execute(sa.text("UPDATE memories SET salience = 0.5 WHERE salience IS NULL"))
    op.execute(sa.text("UPDATE memories SET recall_count = 0 WHERE recall_count IS NULL"))
    op.execute(
        sa.text("UPDATE memories SET scope_type = 'workspace' WHERE scope_type IS NULL OR scope_type = ''")
    )

    # -- surface_turns -------------------------------------------------------
    insp = inspect(bind)
    if "surface_turns" not in insp.get_table_names():
        op.create_table(
            "surface_turns",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id"), nullable=True, index=True),
            sa.Column("session_id", sa.String(), sa.ForeignKey("conversation_sessions.id"), nullable=True, index=True),
            sa.Column("workspace_id", sa.String(), nullable=True),
            sa.Column("step_index", sa.Integer(), nullable=True),
            sa.Column("intent", sa.String(), nullable=True),
            sa.Column("spec_json", sa.JSON(), nullable=True),
            sa.Column("budget_hint", sa.String(), nullable=True),
            sa.Column("created_at", datetime_type, nullable=True),
            sa.Column("updated_at", datetime_type, nullable=True),
        )


def downgrade() -> None:
    # Additive column migrations are not reversible in production.
    # Drop surface_turns only (safe — it is the newest table).
    bind = op.get_bind()
    insp = inspect(bind)
    if "surface_turns" in insp.get_table_names():
        op.drop_table("surface_turns")
