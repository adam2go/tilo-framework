from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.core.database import get_db
from tilo.models import ConversationSession, ConversationTurn, SurfaceTurn, UIInteractionEvent
from tilo.schemas import (
    ConversationMessageCreate,
    ConversationMessageResponse,
    ConversationObservationCreate,
    ConversationSessionCreate,
    ConversationSessionRead,
    ConversationTurnCreate,
    ConversationTurnRead,
    SurfaceTurnRead,
)
from tilo.services.agent_runtime.message_flow import execute_run_in_background
from tilo.services.conversations.messages import ConversationMessageService
from tilo.services.conversations.service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationSessionRead)
def create_session(payload: ConversationSessionCreate, db: Session = Depends(get_db)) -> ConversationSession:
    return ConversationService(db).create_or_get_session(
        app_id=payload.app_id,
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        agent_id=payload.agent_id,
        channel=payload.channel,
        external_thread_id=payload.external_thread_id,
        external_user_id=payload.external_user_id,
        metadata=payload.metadata,
    )


@router.get("/{session_id}", response_model=ConversationSessionRead)
def get_session(session_id: str, db: Session = Depends(get_db)) -> ConversationSession:
    session = ConversationService(db).get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return session


@router.post("/{session_id}/turns", response_model=ConversationTurnRead)
def create_turn(session_id: str, payload: ConversationTurnCreate, db: Session = Depends(get_db)) -> ConversationTurn:
    service = ConversationService(db)
    if not service.get_session(session_id):
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return service.append_turn(
        session_id,
        turn_type=payload.turn_type,
        role=payload.role,
        content=payload.content,
        surface_type=payload.surface_type,
        surface_payload=payload.surface_payload,
        observation_payload=payload.observation_payload,
        artifact_id=payload.artifact_id,
        run_id=payload.run_id,
        task_id=payload.task_id,
        interaction_id=payload.interaction_id,
        confirmation_id=payload.confirmation_id,
        memory_id=payload.memory_id,
        policy_decision=payload.policy_decision,
    )


@router.post("/{session_id}/messages", response_model=ConversationMessageResponse)
def create_message(session_id: str, payload: ConversationMessageCreate, db: Session = Depends(get_db)) -> dict[str, str | None]:
    try:
        return ConversationMessageService(db).send_message(session_id, content=payload.content, attachments=payload.attachments)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/messages/async", response_model=ConversationMessageResponse)
def create_message_async(
    session_id: str,
    payload: ConversationMessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    """Persist user input and return immediately with a `pending` Run id.

    The actual run executes in a FastAPI BackgroundTask. Frontends are
    expected to poll `/api/runs/{run_id}/trace` and
    `/api/runs/{run_id}/surface-turns` to render the activity stream and
    surfaces as they appear. This is the ACP-style streaming entry point.
    """
    try:
        result = ConversationMessageService(db).start_message(
            session_id, content=payload.content, attachments=payload.attachments
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    background_tasks.add_task(
        execute_run_in_background,
        result["task_id"],
        result["run_id"],
        result["session_id"],
    )
    return result


@router.post("/{session_id}/observations/from-interaction", response_model=ConversationTurnRead)
def create_observation_from_interaction(session_id: str, payload: ConversationObservationCreate, db: Session = Depends(get_db)) -> ConversationTurn:
    service = ConversationService(db)
    if not service.get_session(session_id):
        raise HTTPException(status_code=404, detail="Conversation session not found")
    event = db.get(UIInteractionEvent, payload.interaction_id)
    if not event:
        raise HTTPException(status_code=404, detail="Interaction event not found")
    return service.append_observation_for_interaction(session_id, event)


@router.get("/{session_id}/turns", response_model=list[ConversationTurnRead])
def list_turns(session_id: str, limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)) -> list[ConversationTurn]:
    return list(ConversationService(db).list_turns(session_id, limit))


@router.get("/{session_id}/surface-turns", response_model=list[SurfaceTurnRead])
def list_session_surface_turns(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[SurfaceTurn]:
    """List surface turns emitted within a conversation session, oldest first.

    This is what a streaming-aware frontend pulls after each /messages call
    to render the conversation timeline as a sequence of focused surfaces.
    """
    if not ConversationService(db).get_session(session_id):
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return list(
        db.scalars(
            select(SurfaceTurn)
            .where(SurfaceTurn.session_id == session_id)
            .order_by(SurfaceTurn.created_at.asc())
            .limit(limit)
        ).all()
    )
