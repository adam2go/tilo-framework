from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Agent, Artifact, Confirmation, ConversationSession, ConversationTurn, Memory, Project, UIInteractionEvent, Workspace
from app.services.agent_runtime.message_flow import MessageFlowService
from app.services.channels.telegram.renderer import TelegramRenderer
from app.services.channels.types import ChannelRenderResult, TiloChannelEvent
from app.services.interactions.events import UIInteractionEventService
from app.services.memory.writer import MemoryWriter


class TelegramWebhookService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.renderer = TelegramRenderer()

    def handle(self, event: TiloChannelEvent) -> dict[str, Any]:
        if event.event_type == "channel.command.start":
            return self._start_response(event)
        if event.event_type == "channel.callback.clicked":
            return self._handle_callback(event)
        if event.event_type == "channel.message.received" and event.text:
            return self._handle_text_message(event)
        rendered = self.renderer.plain_text(event.external_chat_id, "Tilo received the update, but there is no supported action yet.")
        return self._response(event, rendered, status="ignored")

    def _start_response(self, event: TiloChannelEvent) -> dict[str, Any]:
        rendered = self.renderer.plain_text(
            event.external_chat_id,
            "Welcome to Tilo. Send me a goal, or open the Tilo Console for the full ROAM surface.",
        )
        return self._response(event, rendered)

    def _handle_text_message(self, event: TiloChannelEvent) -> dict[str, Any]:
        context = self._default_context()
        if not context:
            rendered = self.renderer.plain_text(event.external_chat_id, "Tilo is not configured with a workspace yet.")
            return self._response(event, rendered, status="configuration_missing")

        workspace, project, agent = context
        session = self._get_or_create_session(workspace_id=workspace.id, project_id=project.id if project else None, agent_id=agent.id if agent else None, event=event)
        self._append_turn(session.id, turn_type="user_message", role="user", content=event.text or "")
        task, run = MessageFlowService(self.db).create_task_run(
            workspace_id=workspace.id,
            project_id=project.id if project else None,
            agent_id=agent.id if agent else None,
            content=event.text or "",
        )
        artifact = self.db.scalar(select(Artifact).where(Artifact.task_id == task.id).order_by(Artifact.created_at.desc()))
        if artifact:
            self._append_turn(session.id, turn_type="agent_message", role="assistant", content=f"Task created for: {event.text}")
            self._append_turn(
                session.id,
                turn_type="rich_surface_link",
                surface_type="ContractReviewArtifact",
                surface_payload_json={
                    "surface": "ContractReviewArtifact",
                    "title": "Open Artifact",
                    "target": {
                        "type": "page",
                        "artifactId": artifact.id,
                        "title": artifact.title,
                        "source": "channel_fallback",
                    },
                    "channel": "telegram",
                    "metadata": {"external_chat_id": event.external_chat_id},
                },
                artifact_id=artifact.id,
                run_id=run.id,
                task_id=task.id,
            )
            rendered = self.renderer.artifact_link_button(
                event.external_chat_id,
                f"Task created. {artifact.title} is ready as a rich Artifact Surface.",
                artifact.id,
                self.settings.public_app_url,
            )
        else:
            rendered = self.renderer.plain_text(event.external_chat_id, f"Task created. Run status: {run.status}.")
        return {
            **self._response(event, rendered),
            "task_id": task.id,
            "run_id": run.id,
            "artifact_id": artifact.id if artifact else None,
        }

    def _handle_callback(self, event: TiloChannelEvent) -> dict[str, Any]:
        callback = event.callback_data or {}
        action = str(callback.get("action") or "")
        target_id = str(callback.get("target_id") or "")
        if action in {"approve_confirmation", "reject_confirmation"}:
            return self._handle_confirmation_callback(event, action, target_id)
        if action in {"confirm_memory", "reject_memory"}:
            return self._handle_memory_callback(event, action, target_id)
        if action == "open_artifact":
            artifact = self._resolve_by_id_prefix(Artifact, target_id)
            if artifact:
                interaction = self._record_interaction(event, artifact.workspace_id, action, artifact_id=artifact.id)
                self._append_observation_turn_for_interaction(interaction.id, artifact.workspace_id, event, {"action": action, "artifact_id": artifact.id})
                rendered = self.renderer.artifact_link_button(event.external_chat_id, f"Open {artifact.title}.", artifact.id, self.settings.public_app_url)
                return {**self._response(event, rendered), "interaction_id": interaction.id, "artifact_id": artifact.id}
        rendered = self.renderer.plain_text(event.external_chat_id, "Tilo could not resolve that Telegram action.")
        return self._response(event, rendered, status="unresolved")

    def _handle_confirmation_callback(self, event: TiloChannelEvent, action: str, target_id: str) -> dict[str, Any]:
        confirmation = self._resolve_by_id_prefix(Confirmation, target_id)
        if not confirmation:
            rendered = self.renderer.plain_text(event.external_chat_id, "That confirmation is no longer available.")
            return self._response(event, rendered, status="unresolved")
        confirmation.status = "approved" if action == "approve_confirmation" else "rejected"
        confirmation.decision_json = {"decision": {"source": "telegram", "external_user_id": event.external_user_id, "action": action}}
        self.db.commit()
        self.db.refresh(confirmation)
        interaction = self._record_interaction(
            event,
            confirmation.workspace_id,
            action,
            run_id=confirmation.run_id,
            action_id=action,
            payload={"confirmation_id": confirmation.id, "status": confirmation.status},
        )
        rendered = self.renderer.plain_text(event.external_chat_id, f"Confirmation {confirmation.status}.")
        self._append_observation_turn_for_interaction(interaction.id, confirmation.workspace_id, event, {"action": action, "confirmation_id": confirmation.id})
        return {**self._response(event, rendered), "confirmation_id": confirmation.id, "interaction_id": interaction.id}

    def _handle_memory_callback(self, event: TiloChannelEvent, action: str, target_id: str) -> dict[str, Any]:
        memory = self._resolve_by_id_prefix(Memory, target_id)
        if not memory:
            rendered = self.renderer.plain_text(event.external_chat_id, "That memory candidate is no longer available.")
            return self._response(event, rendered, status="unresolved")
        writer = MemoryWriter(self.db)
        if action == "confirm_memory":
            writer.confirm(memory)
        else:
            writer.reject(memory, "Rejected from Telegram")
        self.db.commit()
        self.db.refresh(memory)
        interaction = self._record_interaction(
            event,
            memory.workspace_id,
            action,
            run_id=memory.source_run_id,
            action_id=action,
            payload={"memory_id": memory.id, "status": memory.status},
        )
        rendered = self.renderer.plain_text(event.external_chat_id, f"Memory {memory.status}.")
        self._append_observation_turn_for_interaction(interaction.id, memory.workspace_id, event, {"action": action, "memory_id": memory.id})
        return {**self._response(event, rendered), "memory_id": memory.id, "interaction_id": interaction.id}

    def _get_or_create_session(self, *, workspace_id: str, project_id: str | None, agent_id: str | None, event: TiloChannelEvent) -> ConversationSession:
        thread_id = event.external_chat_id
        existing = self.db.scalar(
            select(ConversationSession).where(
                ConversationSession.workspace_id == workspace_id,
                ConversationSession.channel == "telegram",
                ConversationSession.external_thread_id == thread_id,
            )
        )
        if existing:
            return existing
        session = ConversationSession(
            app_id="contract-review-agent",
            workspace_id=workspace_id,
            project_id=project_id,
            agent_id=agent_id,
            channel="telegram",
            external_thread_id=thread_id,
            external_user_id=event.external_user_id,
            metadata_json={"source": "telegram_webhook"},
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def _append_turn(self, session_id: str, turn_type: str, **kwargs: Any) -> None:
        self.db.add(ConversationTurn(session_id=session_id, turn_type=turn_type, **kwargs))
        self.db.commit()

    def _append_observation_turn_for_interaction(self, interaction_id: str, workspace_id: str, event: TiloChannelEvent, payload: dict[str, Any]) -> None:
        session = self.db.scalar(select(ConversationSession).where(ConversationSession.workspace_id == workspace_id, ConversationSession.channel == "telegram", ConversationSession.external_thread_id == event.external_chat_id))
        if not session:
            return
        self._append_turn(
            session.id,
            turn_type="observation",
            role="system",
            interaction_id=interaction_id,
            observation_payload_json={"channel": "telegram", "external_user_id": event.external_user_id, **payload},
        )

    def _record_interaction(
        self,
        event: TiloChannelEvent,
        workspace_id: str,
        action: str,
        *,
        artifact_id: str | None = None,
        action_id: str | None = None,
        run_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> UIInteractionEvent:
        return UIInteractionEventService(self.db).create(
            workspace_id=workspace_id,
            artifact_id=artifact_id,
            action_id=action_id,
            run_id=run_id,
            event_type=f"channel.telegram.{action}",
            payload_json={
                "channel": "telegram",
                "external_user_id": event.external_user_id,
                "external_chat_id": event.external_chat_id,
                "callback": event.callback_data,
                **(payload or {}),
            },
        )

    def _default_context(self) -> tuple[Workspace, Project | None, Agent | None] | None:
        workspace = self.db.scalar(select(Workspace).order_by(Workspace.created_at.asc()))
        if not workspace:
            return None
        project = self.db.scalar(select(Project).where(Project.workspace_id == workspace.id).order_by(Project.created_at.asc()))
        agent = self.db.scalar(select(Agent).where(Agent.workspace_id == workspace.id).order_by(Agent.created_at.asc()))
        return workspace, project, agent

    def _resolve_by_id_prefix(self, model: type, target_id: str):
        if not target_id:
            return None
        exact = self.db.get(model, target_id)
        if exact:
            return exact
        return self.db.scalar(select(model).where(model.id.startswith(target_id)).order_by(model.created_at.desc()))

    def _response(self, event: TiloChannelEvent, rendered: ChannelRenderResult, status: str = "ok") -> dict[str, Any]:
        return {
            "status": status,
            "event_type": event.event_type,
            "event": event.model_dump(exclude={"raw_payload"}),
            "telegram_response": rendered.payload,
        }
