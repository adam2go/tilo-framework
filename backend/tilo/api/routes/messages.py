from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from tilo.core.database import get_db
from tilo.schemas import MessageCreate, MessageResponse
from tilo.services.agent_runtime.message_flow import (
    MessageFlowService,
    execute_run_in_background,
)

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("", response_model=MessageResponse)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    """Synchronous message endpoint — blocks until the run completes.

    Kept for tests and callers that want inline results. New UIs should use
    /api/messages/async + trace polling for ACP-style streaming UX.
    """
    task, run = MessageFlowService(db).create_task_run(
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        agent_id=payload.agent_id,
        content=payload.content,
    )
    return {"task_id": task.id, "run_id": run.id, "status": run.status}


@router.post("/async", response_model=MessageResponse)
def create_message_async(
    payload: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Asynchronous message endpoint — returns instantly with run_id.

    The frontend polls /api/runs/{run_id}/trace and /api/artifacts to render
    the live activity stream (skill_match → memory_recall → llm_generation →
    artifact_render). This is what the 3D Canvas demo and any stream-first
    surface should use.
    """
    task, run = MessageFlowService(db).start_task_run_async(
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        agent_id=payload.agent_id,
        content=payload.content,
    )
    background_tasks.add_task(
        execute_run_in_background, task.id, run.id, None,
    )
    return {"task_id": task.id, "run_id": run.id, "status": run.status}
