from sqlalchemy.orm import Session

from app.models import Agent, Run, Task
from app.services.agent_runtime.run_manager import RunManager


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
        task = Task(
            workspace_id=workspace_id,
            project_id=project_id,
            agent_id=agent_id,
            title=content[:80],
            input_message=content,
        )
        self.db.add(task)
        self.db.flush()
        run = Run(task_id=task.id, session_id=session_id)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(task)
        self.db.refresh(run)

        agent = self.db.get(Agent, task.agent_id) if task.agent_id else None
        RunManager(self.db).execute(task, run, agent, session_id=session_id)
        self.db.refresh(task)
        self.db.refresh(run)
        return task, run
