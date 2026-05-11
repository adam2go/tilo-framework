from typing import Any

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models import TraceStep


SENSITIVE_KEYS = {"api_key", "apikey", "authorization", "cookie", "password", "secret", "token"}
SENSITIVE_TEXT_MARKERS = ("api_key=", "apikey=", "authorization:", "bearer ", "password=", "secret=", "token=")
MAX_TRACE_STRING_LENGTH = 600
MAX_TRACE_LIST_LENGTH = 20


class TraceSanitizer:
    def sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): "[REDACTED]" if self._is_sensitive_key(str(key)) else self.sanitize(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            sanitized = [self.sanitize(item) for item in value[:MAX_TRACE_LIST_LENGTH]]
            if len(value) > MAX_TRACE_LIST_LENGTH:
                sanitized.append({"truncated": len(value) - MAX_TRACE_LIST_LENGTH})
            return sanitized
        if isinstance(value, tuple):
            return self.sanitize(list(value))
        if isinstance(value, str):
            return self._sanitize_text(value)
        return value

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        return key.lower().replace("-", "_") in SENSITIVE_KEYS

    @staticmethod
    def _sanitize_text(value: str) -> str:
        lowered = value.lower()
        if "chain-of-thought" in lowered or "hidden reasoning" in lowered:
            return "[REDACTED]"
        if any(marker in lowered for marker in SENSITIVE_TEXT_MARKERS):
            return "[REDACTED]"
        if len(value) > MAX_TRACE_STRING_LENGTH:
            return f"{value[:MAX_TRACE_STRING_LENGTH]}... [truncated {len(value) - MAX_TRACE_STRING_LENGTH} chars]"
        return value


class TraceRecorder:
    def __init__(self, db: Session):
        self.db = db
        self.sanitizer = TraceSanitizer()

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
        now = utcnow()
        step = TraceStep(
            run_id=run_id,
            step_type=step_type,
            title=title,
            summary=summary,
            input_json=self.sanitizer.sanitize(input_json) if input_json is not None else None,
            output_json=self.sanitizer.sanitize(output_json) if output_json is not None else None,
            status=status,
            started_at=now,
            completed_at=now,
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def record_started(
        self,
        run_id: str,
        step_type: str,
        title: str,
        summary: str,
        input_json: dict[str, Any] | None = None,
    ) -> TraceStep:
        now = utcnow()
        step = TraceStep(
            run_id=run_id,
            step_type=step_type,
            title=title,
            summary=summary,
            input_json=self.sanitizer.sanitize(input_json) if input_json is not None else None,
            status="running",
            started_at=now,
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def record_completed(
        self,
        step: TraceStep,
        summary: str | None = None,
        output_json: dict[str, Any] | None = None,
    ) -> TraceStep:
        step.status = "completed"
        if summary is not None:
            step.summary = summary
        step.output_json = self.sanitizer.sanitize(output_json) if output_json is not None else step.output_json
        step.completed_at = utcnow()
        self.db.commit()
        self.db.refresh(step)
        return step

    def record_failed(
        self,
        run_id: str,
        step_type: str,
        title: str,
        summary: str,
        input_json: dict[str, Any] | None = None,
        output_json: dict[str, Any] | None = None,
    ) -> TraceStep:
        return self.record(
            run_id,
            step_type,
            title,
            summary,
            input_json=input_json,
            output_json=output_json,
            status="failed",
        )
