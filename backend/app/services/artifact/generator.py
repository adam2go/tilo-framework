from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Artifact, Memory, Run, Task
from app.services.artifact.contract_llm import ContractReviewLLMGenerator
from app.services.artifact.persistence import ArtifactPersistenceService
from app.services.artifact.spec import ArtifactSpecBuilder, ArtifactTypeDetector
from app.services.trace.recorder import TraceRecorder


class ArtifactGenerator:
    def __init__(self, db: Session, trace: TraceRecorder):
        self.db = db
        self.trace = trace
        self.detector = ArtifactTypeDetector()
        self.builder = ArtifactSpecBuilder()
        self.persistence = ArtifactPersistenceService(db)

    def generate(
        self,
        task: Task,
        run: Run,
        memories: list[Memory],
        tool_outputs: list[dict[str, Any]],
    ) -> Artifact:
        artifact_type = self.detector.detect(task.input_message)
        contract_llm_data = None
        generation_mode = "deterministic"
        if artifact_type == "contract_review":
            llm_result = ContractReviewLLMGenerator(get_settings()).generate(task, memories, tool_outputs)
            contract_llm_data = llm_result.data
            generation_mode = llm_result.mode
            self.trace.record(
                run.id,
                "llm_generation",
                "LLM generation requested",
                "Prepared contract review generation with fallback-safe model mode.",
                output_json={
                    "model": llm_result.model,
                    "mode": "json",
                    "status": llm_result.status,
                    "runtime_mode": llm_result.mode,
                    "fallback_reason": llm_result.fallback_reason,
                },
            )
        schema = self.builder.build(artifact_type, task, run, memories, tool_outputs, contract_llm_data=contract_llm_data, generation_mode=generation_mode)
        artifact = self.persistence.create(task=task, run=run, artifact_type=artifact_type, schema_json=schema)
        self.trace.record(
            run.id,
            "generate_artifact",
            "Generate artifact",
            f"Created {artifact_type} artifact.",
            output_json={
                "artifact_id": artifact.id,
                "title": artifact.title,
                "schema_version": artifact.schema_json.get("version"),
                "action_count": len(artifact.schema_json.get("actions", [])),
            },
        )
        return artifact
