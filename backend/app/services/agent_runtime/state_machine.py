from app.core.time import utcnow
from app.models import Run, Task


RUN_STATUSES = {"queued", "running", "waiting_for_confirmation", "completed", "failed", "cancelled"}
TASK_STATUSES = {"created", "running", "waiting_for_confirmation", "completed", "failed", "cancelled"}

RUN_TRANSITIONS = {
    "queued": {"running", "cancelled"},
    "running": {"waiting_for_confirmation", "completed", "failed", "cancelled"},
    "waiting_for_confirmation": {"running", "completed", "failed", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}

TASK_TRANSITIONS = {
    "created": {"running", "cancelled"},
    "running": {"waiting_for_confirmation", "completed", "failed", "cancelled"},
    "waiting_for_confirmation": {"running", "completed", "failed", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}

SENSITIVE_REASON_MARKERS = ("api_key=", "apikey=", "authorization:", "bearer ", "password=", "secret=", "token=")


class InvalidStateTransition(ValueError):
    pass


class RunStateMachine:
    def transition_run(self, run: Run, new_status: str, reason: str | None = None) -> None:
        self._transition(
            current=run.status,
            new_status=new_status,
            allowed_statuses=RUN_STATUSES,
            allowed_transitions=RUN_TRANSITIONS,
            entity="run",
        )
        run.status = new_status
        if new_status == "running" and not run.started_at:
            run.started_at = utcnow()
        if new_status in {"completed", "failed", "cancelled"}:
            run.completed_at = utcnow()
        if new_status == "failed" and reason:
            run.error_message = self.safe_reason(reason)

    def transition_task(self, task: Task, new_status: str) -> None:
        self._transition(
            current=task.status,
            new_status=new_status,
            allowed_statuses=TASK_STATUSES,
            allowed_transitions=TASK_TRANSITIONS,
            entity="task",
        )
        task.status = new_status

    def transition(self, task: Task, run: Run, new_status: str, reason: str | None = None) -> None:
        self.transition_run(run, new_status, reason)
        task_status = "created" if new_status == "queued" else new_status
        self.transition_task(task, task_status)

    @staticmethod
    def safe_reason(reason: str) -> str:
        if any(marker in reason.lower() for marker in SENSITIVE_REASON_MARKERS):
            return "[REDACTED]"
        return reason[:500]

    @staticmethod
    def _transition(
        *,
        current: str,
        new_status: str,
        allowed_statuses: set[str],
        allowed_transitions: dict[str, set[str]],
        entity: str,
    ) -> None:
        if new_status not in allowed_statuses:
            raise InvalidStateTransition(f"Invalid {entity} status: {new_status}")
        if current == new_status:
            return
        if current not in allowed_statuses:
            raise InvalidStateTransition(f"Invalid current {entity} status: {current}")
        if new_status not in allowed_transitions[current]:
            raise InvalidStateTransition(f"Invalid {entity} transition: {current} -> {new_status}")
