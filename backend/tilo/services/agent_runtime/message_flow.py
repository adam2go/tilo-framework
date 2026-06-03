from sqlalchemy.orm import Session

from tilo.core.database import SessionLocal
from tilo.models import Agent, Run, Task
from tilo.services.agent_runtime.run_manager import RunManager


class MessageFlowService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task_run(
        self,
        *,
        workspace_id: str,
        content: str,
        project_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
    ) -> tuple[Task, Run]:
        """Synchronous: create + execute the run on the calling thread.

        Used by tests and any caller that wants the artifact/turn results
        in-line. Production callers prefer `start_task_run_async` so the
        HTTP request returns instantly and the frontend polls trace +
        surface-turns to render an ACP-style activity stream.
        """
        task, run = self._create_pending(
            workspace_id=workspace_id,
            content=content,
            project_id=project_id,
            agent_id=agent_id,
            session_id=session_id,
        )
        agent = self.db.get(Agent, task.agent_id) if task.agent_id else None
        RunManager(self.db).execute(task, run, agent, session_id=session_id)
        self.db.refresh(task)
        self.db.refresh(run)
        return task, run

    def start_task_run_async(
        self,
        *,
        workspace_id: str,
        content: str,
        project_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
    ) -> tuple[Task, Run]:
        """Persist the Task + Run in `pending` state and return immediately.

        The caller is expected to schedule `_run_in_background(run.id, ...)`
        via FastAPI's BackgroundTasks (or a real queue later). The caller's
        DB session is NOT shared with the background task — we open a fresh
        SessionLocal there to keep transaction boundaries clean.
        """
        task, run = self._create_pending(
            workspace_id=workspace_id,
            content=content,
            project_id=project_id,
            agent_id=agent_id,
            session_id=session_id,
        )
        return task, run

    def _create_pending(
        self,
        *,
        workspace_id: str,
        content: str,
        project_id: str | None,
        agent_id: str | None,
        session_id: str | None,
    ) -> tuple[Task, Run]:
        task = Task(
            workspace_id=workspace_id,
            project_id=project_id,
            agent_id=agent_id,
            title=content[:80],
            input_message=content,
        )
        self.db.add(task)
        self.db.flush()
        run = Run(task_id=task.id, session_id=session_id, status="queued")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(task)
        self.db.refresh(run)
        return task, run


def execute_run_in_background(task_id: str, run_id: str, session_id: str | None) -> None:
    """Run `RunManager.execute` in a fresh DB session.

    Designed to be passed to FastAPI's BackgroundTasks. Errors are logged
    to the run row (`status=failed`, `result_summary` carries the message)
    instead of crashing the worker silently.
    """
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        run = db.get(Run, run_id)
        if not task or not run:
            return
        agent = db.get(Agent, task.agent_id) if task.agent_id else None
        try:
            RunManager(db).execute(task, run, agent, session_id=session_id)
        except Exception as exc:  # noqa: BLE001 — convert to durable run state
            db.rollback()
            run = db.get(Run, run_id)
            if run is not None:
                run.status = "failed"
                run.result_summary = f"Run failed: {exc.__class__.__name__}: {str(exc)[:200]}"
                db.commit()
    finally:
        db.close()
