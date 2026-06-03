"""Initial schema baseline.

Revision ID: 0001
Revises:
Create Date: 2026-06-04

This migration is a **no-op baseline marker**.

On fresh databases, `Base.metadata.create_all()` creates all tables
before Alembic runs. The startup code then stamps this revision as
applied so subsequent migrations are tracked correctly.

On pre-Alembic databases (v0.1 installs), this migration records that
the initial schema is already in place, and migration 0002 handles the
additive v02 column changes.
"""
from alembic import op  # noqa: F401

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables exist on all databases (either via create_all or pre-existing).
    pass


def downgrade() -> None:
    pass
