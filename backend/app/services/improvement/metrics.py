from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Run, RunMetrics, Task


class RunMetricsService:
    def __init__(self, db: Session):
        self.db = db

    def record_completed(
        self,
        *,
        task: Task,
        run: Run,
        artifact_count: int,
        confirmation_count: int,
        memory_candidate_count: int,
        tool_call_count: int,
        error_count: int = 0,
    ) -> RunMetrics:
        existing = self.db.scalar(select(RunMetrics).where(RunMetrics.run_id == run.id))
        latency_ms = self._latency_ms(run)
        metrics = existing or RunMetrics(run_id=run.id, workspace_id=task.workspace_id)
        metrics.success = run.status == "completed" and error_count == 0
        metrics.latency_ms = latency_ms
        metrics.artifact_count = artifact_count
        metrics.confirmation_count = confirmation_count
        metrics.memory_candidate_count = memory_candidate_count
        metrics.tool_call_count = tool_call_count
        metrics.error_count = error_count
        if not existing:
            self.db.add(metrics)
        self.db.flush()
        return metrics

    def apply_feedback_score(self, run_id: str, rating: int | None) -> None:
        if rating is None:
            return
        metrics = self.db.scalar(select(RunMetrics).where(RunMetrics.run_id == run_id))
        if metrics:
            metrics.user_feedback_score = rating

    @staticmethod
    def _latency_ms(run: Run) -> int:
        if not run.started_at:
            return 0
        end = run.completed_at or datetime.utcnow()
        return max(int((end - run.started_at).total_seconds() * 1000), 0)
