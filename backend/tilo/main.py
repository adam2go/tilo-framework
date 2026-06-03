from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from tilo.api.routes import routers
from tilo.core.config import get_settings
from tilo.core.database import Base, SessionLocal, engine
from tilo.core.migrations import ensure_v02_schema
from tilo.services.bootstrap import seed_defaults


settings = get_settings()

_ALEMBIC_INI = Path(__file__).parent.parent / "alembic.ini"


def _run_db_migrations() -> None:
    """Apply all pending database migrations on startup.

    Strategy:
    - Fresh database (no alembic_version table):
        1. create_all  — creates every table from the current ORM models.
        2. alembic stamp head — marks all migrations as applied so Alembic
           doesn't try to re-apply them on the next start.
    - Pre-Alembic database (has tables, but no alembic_version):
        1. alembic upgrade head — applies migrations 0001 (no-op baseline)
           and 0002 (additive v02 columns + surface_turns), replacing the
           old ensure_v02_schema() manual approach.
    - Alembic-managed database (alembic_version exists):
        1. alembic upgrade head — applies any pending migrations.
    """
    try:
        from alembic.config import Config
        from alembic import command as alembic_command

        insp = inspect(engine)
        has_alembic = "alembic_version" in insp.get_table_names()
        has_tables = bool(insp.get_table_names())

        alembic_cfg = Config(str(_ALEMBIC_INI))

        if not has_tables:
            # Completely fresh database.
            Base.metadata.create_all(bind=engine)
            alembic_command.stamp(alembic_cfg, "head")
        elif not has_alembic:
            # Pre-existing tables, but Alembic was never set up.
            # Run migrations (0001 is a no-op; 0002 adds missing columns).
            alembic_command.upgrade(alembic_cfg, "head")
        else:
            # Normal case: apply any pending migrations.
            alembic_command.upgrade(alembic_cfg, "head")

    except Exception as exc:  # noqa: BLE001
        # Alembic not installed or alembic.ini missing — fall back to the
        # previous approach so existing deployments are not broken.
        _fallback_migrations(exc)


def _fallback_migrations(reason: Exception) -> None:
    """Legacy migration path when Alembic is unavailable."""
    import warnings
    warnings.warn(
        f"Alembic migration skipped ({reason}); falling back to create_all + ensure_v02_schema. "
        "Install alembic (pip install alembic) for tracked schema migrations.",
        stacklevel=2,
    )
    Base.metadata.create_all(bind=engine)
    ensure_v02_schema(engine)


@asynccontextmanager
async def lifespan(_: FastAPI):
    _run_db_migrations()
    with SessionLocal() as db:
        seed_defaults(db)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)
