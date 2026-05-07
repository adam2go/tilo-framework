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

    if "memories" not in table_names:
        return

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
