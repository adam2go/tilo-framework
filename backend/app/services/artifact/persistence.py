from typing import Any

from sqlalchemy.orm import Session

from app.models import Artifact, Run, Task
from app.services.artifact.spec import ArtifactValidator


class ArtifactPersistenceService:
    def __init__(self, db: Session):
        self.db = db
        self.validator = ArtifactValidator()

    def create(
        self,
        *,
        task: Task,
        run: Run,
        artifact_type: str,
        schema_json: dict[str, Any],
    ) -> Artifact:
        schema = self.validator.normalize_and_validate(schema_json)
        artifact = Artifact(
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            task_id=task.id,
            run_id=run.id,
            type=artifact_type,
            title=schema["title"],
            schema_json=schema,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def update_schema(self, artifact: Artifact, schema_json: dict[str, Any]) -> Artifact:
        schema = self.validator.normalize_and_validate(schema_json)
        artifact.schema_json = schema
        artifact.type = schema["artifact_type"]
        artifact.title = schema["title"]
        self.db.commit()
        self.db.refresh(artifact)
        return artifact
