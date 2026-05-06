from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ConversationSession, ConversationTurn
from app.schemas import ConversationSessionCreate, ConversationSessionRead, ConversationTurnCreate, ConversationTurnRead

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationSessionRead)
def create_session(payload: ConversationSessionCreate, db: Session = Depends(get_db)) -> ConversationSession:
    if payload.external_thread_id:
        existing = db.scalar(
            select(ConversationSession).where(
                ConversationSession.channel == payload.channel,
                ConversationSession.external_thread_id == payload.external_thread_id,
                ConversationSession.workspace_id == payload.workspace_id,
            )
        )
        if existing:
            return existing
    session = ConversationSession(
        app_id=payload.app_id,
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        agent_id=payload.agent_id,
        channel=payload.channel,
        external_thread_id=payload.external_thread_id,
        external_user_id=payload.external_user_id,
        metadata_json=payload.metadata,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=ConversationSessionRead)
def get_session(session_id: str, db: Session = Depends(get_db)) -> ConversationSession:
    session = db.get(ConversationSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return session


@router.post("/{session_id}/turns", response_model=ConversationTurnRead)
def create_turn(session_id: str, payload: ConversationTurnCreate, db: Session = Depends(get_db)) -> ConversationTurn:
    if not db.get(ConversationSession, session_id):
        raise HTTPException(status_code=404, detail="Conversation session not found")
    turn = ConversationTurn(
        session_id=session_id,
        turn_type=payload.turn_type,
        role=payload.role,
        content=payload.content,
        surface_type=payload.surface_type,
        surface_payload_json=payload.surface_payload,
        observation_payload_json=payload.observation_payload,
        artifact_id=payload.artifact_id,
        run_id=payload.run_id,
        task_id=payload.task_id,
        interaction_id=payload.interaction_id,
        confirmation_id=payload.confirmation_id,
        memory_id=payload.memory_id,
        policy_decision_json=payload.policy_decision,
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


@router.get("/{session_id}/turns", response_model=list[ConversationTurnRead])
def list_turns(session_id: str, limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)) -> Sequence[ConversationTurn]:
    stmt = select(ConversationTurn).where(ConversationTurn.session_id == session_id).order_by(ConversationTurn.created_at.desc()).limit(limit)
    return list(reversed(db.scalars(stmt).all()))
