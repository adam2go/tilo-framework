from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ConversationSession, ConversationTurn, UIInteractionEvent
from app.schemas import RichSurfaceLink
from app.services.conversations.constants import ConversationChannel, ConversationRole, ConversationTurnType
from app.services.trace.recorder import TraceSanitizer


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.sanitizer = TraceSanitizer()

    def create_or_get_session(
        self,
        *,
        app_id: str,
        workspace_id: str,
        project_id: str | None = None,
        agent_id: str | None = None,
        channel: ConversationChannel | str = ConversationChannel.web,
        external_thread_id: str | None = None,
        external_user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationSession:
        if external_thread_id:
            existing = self.find_by_external_thread(channel=channel, external_thread_id=external_thread_id, workspace_id=workspace_id)
            if existing:
                return existing
        session = ConversationSession(
            app_id=app_id,
            workspace_id=workspace_id,
            project_id=project_id,
            agent_id=agent_id,
            channel=ConversationChannel(channel).value,
            external_thread_id=external_thread_id,
            external_user_id=external_user_id,
            metadata_json=metadata or {},
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> ConversationSession | None:
        return self.db.get(ConversationSession, session_id)

    def find_by_external_thread(
        self,
        *,
        channel: ConversationChannel | str,
        external_thread_id: str,
        workspace_id: str,
    ) -> ConversationSession | None:
        return self.db.scalar(
            select(ConversationSession).where(
                ConversationSession.workspace_id == workspace_id,
                ConversationSession.channel == ConversationChannel(channel).value,
                ConversationSession.external_thread_id == external_thread_id,
            )
        )

    def append_turn(
        self,
        session_id: str,
        *,
        turn_type: ConversationTurnType | str,
        role: ConversationRole | str | None = None,
        content: str | None = None,
        surface_type: str | None = None,
        surface_payload: dict[str, Any] | None = None,
        observation_payload: dict[str, Any] | None = None,
        artifact_id: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
        interaction_id: str | None = None,
        confirmation_id: str | None = None,
        memory_id: str | None = None,
        policy_decision: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        if not self.get_session(session_id):
            raise ValueError("Conversation session not found")
        turn = ConversationTurn(
            session_id=session_id,
            turn_type=ConversationTurnType(turn_type).value,
            role=ConversationRole(role).value if role else None,
            content=content,
            surface_type=surface_type,
            surface_payload_json=self.sanitizer.sanitize(surface_payload) if surface_payload is not None else None,
            observation_payload_json=self.sanitizer.sanitize(observation_payload) if observation_payload is not None else None,
            artifact_id=artifact_id,
            run_id=run_id,
            task_id=task_id,
            interaction_id=interaction_id,
            confirmation_id=confirmation_id,
            memory_id=memory_id,
            policy_decision_json=self.sanitizer.sanitize(policy_decision) if policy_decision is not None else None,
        )
        self.db.add(turn)
        self.db.commit()
        self.db.refresh(turn)
        return turn

    def list_turns(self, session_id: str, limit: int = 50) -> Sequence[ConversationTurn]:
        stmt = select(ConversationTurn).where(ConversationTurn.session_id == session_id).order_by(ConversationTurn.created_at.desc()).limit(limit)
        return list(reversed(self.db.scalars(stmt).all()))

    def append_user_message(self, session_id: str, content: str, **kwargs: Any) -> ConversationTurn:
        return self.append_turn(session_id, turn_type=ConversationTurnType.user_message, role=ConversationRole.user, content=content, **kwargs)

    def append_agent_message(self, session_id: str, content: str, **kwargs: Any) -> ConversationTurn:
        return self.append_turn(session_id, turn_type=ConversationTurnType.agent_message, role=ConversationRole.assistant, content=content, **kwargs)

    def append_attachment(self, session_id: str, *, content: str | None = None, payload: dict[str, Any] | None = None, **kwargs: Any) -> ConversationTurn:
        return self.append_turn(session_id, turn_type=ConversationTurnType.attachment, content=content, surface_payload=payload, **kwargs)

    def append_mini_surface(self, session_id: str, *, surface_type: str, payload: dict[str, Any] | None = None, **kwargs: Any) -> ConversationTurn:
        return self.append_turn(
            session_id,
            turn_type=ConversationTurnType.mini_surface,
            role=ConversationRole.assistant,
            surface_type=surface_type,
            surface_payload=payload,
            **kwargs,
        )

    def append_observation(
        self,
        session_id: str,
        *,
        interaction_id: str | None = None,
        content: str | None = None,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ConversationTurn:
        return self.append_turn(
            session_id,
            turn_type=ConversationTurnType.observation,
            role=ConversationRole.system,
            content=content,
            interaction_id=interaction_id,
            observation_payload=payload,
            **kwargs,
        )

    def append_rich_surface_link(
        self,
        session_id: str,
        *,
        link: RichSurfaceLink,
        artifact_id: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
        interaction_id: str | None = None,
        policy_decision: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        return self.append_turn(
            session_id,
            turn_type=ConversationTurnType.rich_surface_link,
            role=ConversationRole.assistant,
            content=link.title,
            surface_type=link.surface,
            surface_payload=link.model_dump(mode="json"),
            artifact_id=artifact_id or link.target.artifactId,
            run_id=run_id,
            task_id=task_id,
            interaction_id=interaction_id,
            policy_decision=policy_decision,
        )

    def append_observation_for_interaction(self, session_id: str, event: UIInteractionEvent) -> ConversationTurn:
        return self.append_observation(
            session_id,
            interaction_id=event.id,
            content=event.event_type,
            artifact_id=event.artifact_id,
            run_id=event.run_id,
            payload={
                "event_type": event.event_type,
                "payload": event.payload_json,
                "artifact_id": event.artifact_id,
                "run_id": event.run_id,
                "action_id": event.action_id,
                "block_id": event.block_id,
            },
        )
