from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_v02_schema(engine: Engine) -> None:
    """Small compatibility bridge until the project has real migrations."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "runs" in table_names:
        run_columns = {column["name"] for column in inspector.get_columns("runs")}
        if "session_id" not in run_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE runs ADD COLUMN session_id VARCHAR"))

    if "memories" in table_names:
        datetime_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"
        memory_columns: dict[str, str] = {
            "scope_type": "VARCHAR DEFAULT 'workspace'",
            "scope_id": "VARCHAR",
            "source_run_id": "VARCHAR",
            "salience": "FLOAT DEFAULT 0.5",
            "status": "VARCHAR DEFAULT 'candidate'",
            "structured_payload": "JSON",
            "supersedes_id": "VARCHAR",
            "last_recalled_at": datetime_type,
            "recall_count": "INTEGER DEFAULT 0",
        }

        existing_columns = {column["name"] for column in inspector.get_columns("memories")}
        with engine.begin() as connection:
            for column_name, column_type in memory_columns.items():
                if column_name not in existing_columns:
                    connection.execute(text(f"ALTER TABLE memories ADD COLUMN {column_name} {column_type}"))

            connection.execute(
                text(
                    """
                    UPDATE memories
                    SET status = CASE WHEN is_confirmed THEN 'confirmed' ELSE 'candidate' END
                    WHERE status IS NULL OR status = ''
                    """
                )
            )
            connection.execute(text("UPDATE memories SET salience = 0.5 WHERE salience IS NULL"))
            connection.execute(text("UPDATE memories SET recall_count = 0 WHERE recall_count IS NULL"))
            connection.execute(text("UPDATE memories SET scope_type = 'workspace' WHERE scope_type IS NULL OR scope_type = ''"))

    # Phase 2: surface_turns table.
    # `Base.metadata.create_all` already creates the table on fresh databases.
    # The explicit creation below is defensive: it ensures the table exists
    # even on legacy Postgres instances that pre-date `Base.metadata.create_all`
    # being invoked at startup. We re-run create_all for SurfaceTurn only by
    # importing the model; SQLAlchemy will skip if the table already exists.
    # No per-column ALTERs are needed yet because this is the table's first
    # appearance.
    _ensure_surface_turns_table(engine)


def _ensure_surface_turns_table(engine: Engine) -> None:
    inspector = inspect(engine)
    if "surface_turns" in inspector.get_table_names():
        return
    # Re-import models lazily and use create_all for this table only.
    from tilo.core.database import Base  # noqa: WPS433 — circular-safe at runtime
    from tilo.models.domain import SurfaceTurn  # noqa: F401 — registers the table

    SurfaceTurn.__table__.create(bind=engine, checkfirst=True)
