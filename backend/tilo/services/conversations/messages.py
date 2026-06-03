from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.models import Artifact
from tilo.services.agent_runtime.message_flow import MessageFlowService
from tilo.services.conversations.service import ConversationService
from tilo.services.surfaces.constants import RichSurfaceSource, RichSurfaceTargetType
from tilo.services.surfaces.rich_links import create_rich_surface_link


class ConversationMessageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversation = ConversationService(db)

    def send_message(self, session_id: str, *, content: str, attachments: list[dict[str, Any]] | None = None) -> dict[str, str | None]:
        """Synchronous: create + execute the run inline. Tests rely on this."""
        session = self.conversation.get_session(session_id)
        if not session:
            raise ValueError("Conversation session not found")

        self._persist_user_input(session, content, attachments)
        task, run = MessageFlowService(self.db).create_task_run(
            workspace_id=session.workspace_id,
            project_id=session.project_id,
            agent_id=session.agent_id,
            content=content,
            session_id=session.id,
        )
        artifact = self.db.scalar(
            select(Artifact).where(Artifact.task_id == task.id).order_by(Artifact.created_at.desc())
        )

        self.conversation.append_agent_message(
            session.id,
            run.result_summary or f"Run status: {run.status}.",
            task_id=task.id,
            run_id=run.id,
            artifact_id=artifact.id if artifact else None,
        )
        if artifact:
            self.conversation.append_rich_surface_link(
                session.id,
                link=create_rich_surface_link(
                    surface=self._surface_for_app(session.app_id),
                    title="Open Full Review",
                    target_type=RichSurfaceTargetType.drawer,
                    source=RichSurfaceSource.policy,
                    artifact_id=artifact.id,
                    target_title=artifact.title,
                    channel=session.channel,
                    metadata={"task_id": task.id, "run_id": run.id},
                ),
                artifact_id=artifact.id,
                run_id=run.id,
                task_id=task.id,
            )

        return {
            "session_id": session.id,
            "task_id": task.id,
            "run_id": run.id,
            "status": run.status,
            "artifact_id": artifact.id if artifact else None,
        }

    def start_message(
        self,
        session_id: str,
        *,
        content: str,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, str | None]:
        """Async-friendly: persist user input + a `pending` Run and return.

        The caller is expected to schedule `execute_run_in_background` via
        FastAPI's BackgroundTasks. The frontend polls
        `/api/runs/{run_id}/trace` and `/api/runs/{run_id}/surface-turns`
        to render the ACP-style activity stream.
        """
        session = self.conversation.get_session(session_id)
        if not session:
            raise ValueError("Conversation session not found")

        self._persist_user_input(session, content, attachments)
        task, run = MessageFlowService(self.db).start_task_run_async(
            workspace_id=session.workspace_id,
            project_id=session.project_id,
            agent_id=session.agent_id,
            content=content,
            session_id=session.id,
        )
        return {
            "session_id": session.id,
            "task_id": task.id,
            "run_id": run.id,
            "status": run.status,  # "pending"
            "artifact_id": None,
        }

    def _persist_user_input(self, session, content: str, attachments: list[dict[str, Any]] | None) -> None:
        self.conversation.append_user_message(session.id, content)
        for attachment in attachments or []:
            self.conversation.append_attachment(
                session.id,
                content=str(
                    attachment.get("name")
                    or attachment.get("filename")
                    or attachment.get("type")
                    or "attachment"
                ),
                payload=attachment,
            )

    @staticmethod
    def _surface_for_app(app_id: str) -> str:
        if app_id == "sales-followup-agent":
            return "FollowupDraftArtifact"
        return "ContractReviewArtifact"
