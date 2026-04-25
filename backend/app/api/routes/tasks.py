from collections.abc import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_one
from app.core.database import get_db
from app.models import Agent, Run, Task
from app.schemas import RunRead, TaskCreate, TaskRead
from app.services.agent_runtime.run_manager import RunManager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    item = Task(
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        agent_id=payload.agent_id,
        title=payload.title or payload.input_message[:80],
        input_message=payload.input_message,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[TaskRead])
def list_tasks(workspace_id: str, project_id: str | None = None, db: Session = Depends(get_db)) -> Sequence[Task]:
    stmt = select(Task).where(Task.workspace_id == workspace_id)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    return db.scalars(stmt.order_by(Task.created_at.desc())).all()


@router.get("/{item_id}", response_model=TaskRead)
def read_task(item_id: str, db: Session = Depends(get_db)) -> Task:
    return get_one(db, Task, item_id)


@router.post("/{item_id}/runs", response_model=RunRead)
def create_run(item_id: str, db: Session = Depends(get_db)) -> Run:
    task = get_one(db, Task, item_id)
    agent = db.get(Agent, task.agent_id) if task.agent_id else None
    run = Run(task_id=task.id)
    db.add(run)
    db.commit()
    db.refresh(run)
    RunManager(db).execute(task, run, agent)
    db.refresh(run)
    return run
