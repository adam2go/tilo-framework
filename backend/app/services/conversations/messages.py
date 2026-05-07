from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Artifact
from app.services.agent_runtime.message_flow import MessageFlowService
from app.services.conversations.service import ConversationService
from app.services.surfaces.constants import RichSurfaceSource, RichSurfaceTargetType
from app.services.surfaces.rich_links import create_rich_surface_link


class ConversationMessageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversation = ConversationService(db)

    def send_message(self, session_id: str, *, content: str, attachments: list[dict[str, Any]] | None = None) -> dict[str, str | None]:
        session = self.conversation.get_session(session_id)
        if not session:
            raise ValueError("Conversation session not found")

        self.conversation.append_user_message(session.id, content)
        for attachment in attachments or []:
            self.conversation.append_attachment(
                session.id,
                content=str(attachment.get("name") or attachment.get("filename") or attachment.get("type") or "attachment"),
                payload=attachment,
            )

        task, run = MessageFlowService(self.db).create_task_run(
            workspace_id=session.workspace_id,
            project_id=session.project_id,
            agent_id=session.agent_id,
            content=content,
            session_id=session.id,
        )
        artifact = self.db.scalar(select(Artifact).where(Artifact.task_id == task.id).order_by(Artifact.created_at.desc()))

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

    @staticmethod
    def _surface_for_app(app_id: str) -> str:
        if app_id == "sales-followup-agent":
            return "FollowupDraftArtifact"
        return "ContractReviewArtifact"
