from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ConversationSession, ConversationTurn, UIInteractionEvent
from app.schemas import ConversationObservationCreate, ConversationSessionCreate, ConversationSessionRead, ConversationTurnCreate, ConversationTurnRead
from app.services.conversations.service import ConversationService

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
