from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Agent, Run, Task
from app.schemas import MessageCreate, MessageResponse
from app.services.agent_runtime.run_manager import RunManager

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("", response_model=MessageResponse)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    task = Task(
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        agent_id=payload.agent_id,
        title=payload.content[:80],
        input_message=payload.content,
    )
    db.add(task)
    db.flush()
    run = Run(task_id=task.id)
    db.add(run)
    db.commit()
    db.refresh(task)
    db.refresh(run)

    agent = db.get(Agent, task.agent_id) if task.agent_id else None
    RunManager(db).execute(task, run, agent)
    db.refresh(task)
    db.refresh(run)
    return {"task_id": task.id, "run_id": run.id, "status": run.status}
