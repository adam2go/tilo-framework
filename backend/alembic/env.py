"""Alembic environment configuration for Tilo Framework.

The database URL is read from tilo.core.config (DATABASE_URL env var).
All ORM models are imported here so Alembic can detect schema changes
for `alembic revision --autogenerate`.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config provides access to alembic.ini values.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Base and register all models so target_metadata is complete.
from tilo.core.database import Base  # noqa: E402
import tilo.models.domain  # noqa: F401, E402 — registers all ORM tables

target_metadata = Base.metadata


def _get_url() -> str:
    from tilo.core.config import get_settings
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    cfg = dict(config.get_section(config.config_ini_section) or {})
    cfg["sqlalchemy.url"] = _get_url()
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
