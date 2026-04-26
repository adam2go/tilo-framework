from sqlalchemy.orm import Session

from app.models import UIInteractionEvent
from app.services.trace.recorder import TraceSanitizer


class UIInteractionEventService:
    def __init__(self, db: Session):
        self.db = db
        self.sanitizer = TraceSanitizer()

    def create(
        self,
        *,
        workspace_id: str,
        event_type: str,
        payload_json: dict,
        project_id: str | None = None,
        user_id: str | None = None,
        artifact_id: str | None = None,
        block_id: str | None = None,
        action_id: str | None = None,
        run_id: str | None = None,
    ) -> UIInteractionEvent:
        event = UIInteractionEvent(
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            artifact_id=artifact_id,
            block_id=block_id,
            action_id=action_id,
            run_id=run_id,
            event_type=event_type,
            payload_json=self.sanitizer.sanitize(payload_json or {}),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
