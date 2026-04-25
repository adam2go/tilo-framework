from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import TraceStep


class TraceRecorder:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        run_id: str,
        step_type: str,
        title: str,
        summary: str,
        input_json: dict[str, Any] | None = None,
        output_json: dict[str, Any] | None = None,
        status: str = "completed",
    ) -> TraceStep:
        now = datetime.utcnow()
        step = TraceStep(
            run_id=run_id,
            step_type=step_type,
            title=title,
            summary=summary,
            input_json=input_json,
            output_json=output_json,
            status=status,
            started_at=now,
            completed_at=now,
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step
