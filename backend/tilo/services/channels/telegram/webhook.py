from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.core.config import Settings
from tilo.models import Agent, Artifact, Confirmation, Memory, Project, UIInteractionEvent, Workspace
from tilo.services.artifact.actions import ArtifactActionRuntime, ArtifactActionRuntimeError
from tilo.services.channels.telegram.renderer import TelegramRenderer
from tilo.services.channels.types import ChannelRenderResult, TiloChannelEvent
from tilo.services.context_reflection import ContextReflectionService
from tilo.services.conversations.constants import ConversationChannel
from tilo.services.conversations.messages import ConversationMessageService
from tilo.services.conversations.service import ConversationService
from tilo.services.interactions.events import UIInteractionEventService
from tilo.services.memory.writer import MemoryWriter


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
        message = ConversationMessageService(self.db).send_message(
            session.id,
            content=event.text or "",
        )
        artifact = self.db.get(Artifact, message["artifact_id"]) if message["artifact_id"] else None
        if artifact:
            rendered = self.renderer.artifact_link_button(
                event.external_chat_id,
                f"Task created. {artifact.title} is ready as a rich Artifact Surface.",
                artifact.id,
                self.settings.public_app_url,
            )
        else:
            rendered = self.renderer.plain_text(event.external_chat_id, f"Task created. Run status: {message['status']}.")
        return {
            **self._response(event, rendered),
            "task_id": message["task_id"],
            "run_id": message["run_id"],
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
        if action == "artifact_action":
            action_response = self._handle_artifact_action_callback(event, target_id)
            if action_response:
                return action_response
        if action == "open_artifact":
            artifact = self._resolve_by_id_prefix(Artifact, target_id)
            if artifact:
                interaction = self._record_interaction(event, artifact.workspace_id, action, artifact_id=artifact.id)
                self._append_observation_turn_for_interaction(interaction, artifact.workspace_id, event)
                rendered = self.renderer.artifact_link_button(event.external_chat_id, f"Open {artifact.title}.", artifact.id, self.settings.public_app_url)
                return {**self._response(event, rendered), "interaction_id": interaction.id, "artifact_id": artifact.id}
        rendered = self.renderer.plain_text(event.external_chat_id, "Tilo could not resolve that Telegram action.")
        return self._response(event, rendered, status="unresolved")

    def _handle_artifact_action_callback(self, event: TiloChannelEvent, target_id: str) -> dict[str, Any] | None:
        ref = self._parse_artifact_action_ref(target_id)
        if not ref:
            return None
        artifact_id, action_id, block_id = ref
        artifact = self._resolve_by_id_prefix(Artifact, artifact_id)
        if not artifact:
            rendered = self.renderer.plain_text(event.external_chat_id, "That artifact action is no longer available.")
            return self._response(event, rendered, status="unresolved")
        session = ConversationService(self.db).find_by_external_thread(
            channel=ConversationChannel.telegram,
            external_thread_id=event.external_chat_id,
            workspace_id=artifact.workspace_id,
        )
        try:
            result = ArtifactActionRuntime(self.db).execute(
                artifact_id=artifact.id,
                action_id=action_id,
                block_id=block_id,
                session_id=session.id if session else None,
                run_id=artifact.run_id,
                source="telegram",
                payload={
                    "external_user_id": event.external_user_id,
                    "external_chat_id": event.external_chat_id,
                    "callback": event.callback_data,
                },
            )
        except ArtifactActionRuntimeError as exc:
            rendered = self.renderer.plain_text(event.external_chat_id, str(exc))
            return self._response(event, rendered, status="failed")
        rendered = self.renderer.plain_text(event.external_chat_id, result.message)
        return {
            **self._response(event, rendered, status=result.status),
            "artifact_id": artifact.id,
            "action_id": action_id,
            "action_result": result.model_dump(mode="json"),
        }

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
        self._append_observation_turn_for_interaction(interaction, confirmation.workspace_id, event)
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
        self._append_observation_turn_for_interaction(interaction, memory.workspace_id, event)
        return {**self._response(event, rendered), "memory_id": memory.id, "interaction_id": interaction.id}

    def _get_or_create_session(self, *, workspace_id: str, project_id: str | None, agent_id: str | None, event: TiloChannelEvent):
        return ConversationService(self.db).create_or_get_session(
            app_id="contract-review-agent",
            workspace_id=workspace_id,
            project_id=project_id,
            agent_id=agent_id,
            channel=ConversationChannel.telegram,
            external_thread_id=event.external_chat_id,
            external_user_id=event.external_user_id,
            metadata={"source": "telegram_webhook"},
        )

    def _append_observation_turn_for_interaction(self, interaction: UIInteractionEvent, workspace_id: str, event: TiloChannelEvent) -> None:
        conversation = ConversationService(self.db)
        session = conversation.find_by_external_thread(channel=ConversationChannel.telegram, external_thread_id=event.external_chat_id, workspace_id=workspace_id)
        if not session:
            return
        conversation.append_observation_for_interaction(session.id, interaction)
        ContextReflectionService(self.db).reflect_and_persist(
            session_id=session.id,
            trigger_event_id=interaction.id,
            artifact_id=interaction.artifact_id,
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

    @staticmethod
    def _parse_artifact_action_ref(target_id: str) -> tuple[str, str, str | None] | None:
        if not target_id:
            return None
        separator = "|" if "|" in target_id else ":"
        parts = [part for part in target_id.split(separator) if part]
        if len(parts) < 2:
            return None
        return parts[0], parts[1], parts[2] if len(parts) > 2 else None

    def _response(self, event: TiloChannelEvent, rendered: ChannelRenderResult, status: str = "ok") -> dict[str, Any]:
        return {
            "status": status,
            "event_type": event.event_type,
            "event": event.model_dump(exclude={"raw_payload"}),
            "telegram_response": rendered.payload,
        }
