from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tilo.core.database import get_db
from tilo.schemas import MessageCreate, MessageResponse
from tilo.services.agent_runtime.message_flow import MessageFlowService

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("", response_model=MessageResponse)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    task, run = MessageFlowService(db).create_task_run(
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        agent_id=payload.agent_id,
        content=payload.content,
    )
    return {"task_id": task.id, "run_id": run.id, "status": run.status}
