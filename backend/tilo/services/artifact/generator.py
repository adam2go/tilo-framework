"""Artifact generation — the bridge between agent reasoning and structured output.

Every artifact_type (contract_review, dashboard, table, document) follows
the same flow:

    1. Detect artifact_type from the user message.
    2. If LLM is enabled → call the model with a type-specific prompt to
       generate structured data.  Streaming thinking is visible in trace.
    3. Fall back to deterministic fixture data when LLM is disabled or
       the model call fails.
    4. Pass the structured data (LLM or fixture) to ArtifactSpecBuilder
       which assembles the full ArtifactSpecV1 with blocks + views.
    5. Persist and return the Artifact.
"""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from tilo.core.config import Settings, get_settings
from tilo.models import Artifact, Memory, Run, Task
from tilo.services.artifact.contract_llm import ContractReviewLLMGenerator
from tilo.services.artifact.persistence import ArtifactPersistenceService
from tilo.services.artifact.spec import ArtifactSpecBuilder, ArtifactTypeDetector
from tilo.services.models.client import ModelClient
from tilo.services.models.errors import ModelClientError
from tilo.services.models.prompts import (
    COMPETITIVE_ANALYSIS_SYSTEM_PROMPT,
    SALES_FOLLOWUP_SYSTEM_PROMPT,
    competitive_analysis_user_prompt,
    sales_followup_user_prompt,
)
from tilo.services.models.schemas import (
    CompetitiveAnalysisLLMData,
    SalesFollowUpLLMData,
)
from tilo.services.trace.recorder import TraceRecorder


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
        settings = get_settings()
        memory_snippets = [m.content for m in memories[:5]]

        # --- LLM generation (all artifact types) ---
        llm_data: dict[str, Any] | None = None
        generation_mode = "deterministic"

        if settings.llm_enabled and settings.llm_api_key:
            on_thinking, on_content, running_step = self._setup_streaming(run, settings)
            try:
                llm_data, generation_mode = self._call_llm(
                    artifact_type, task, memories, tool_outputs,
                    memory_snippets, settings, on_thinking, on_content,
                )
            finally:
                self._finish_streaming(running_step, generation_mode, artifact_type, settings)
        else:
            self.trace.record(
                run.id, "llm_generation",
                "Skipping LLM (deterministic mode)",
                "No API key configured; composing artifact from fixtures.",
                output_json={"runtime_mode": "deterministic"},
            )

        # --- Build spec + persist ---
        schema = self.builder.build(
            artifact_type, task, run, memories, tool_outputs,
            contract_llm_data=llm_data.get("contract") if llm_data else None,
            sales_llm_data=llm_data.get("sales") if llm_data else None,
            competitive_llm_data=llm_data.get("competitive") if llm_data else None,
            generation_mode=generation_mode,
        )
        artifact = self.persistence.create(task=task, run=run, artifact_type=artifact_type, schema_json=schema)
        self.trace.record(
            run.id, "generate_artifact", "Generate artifact",
            f"Created {artifact_type} artifact.",
            output_json={
                "artifact_id": artifact.id,
                "title": artifact.title,
                "schema_version": artifact.schema_json.get("version"),
                "action_count": len(artifact.schema_json.get("actions", [])),
            },
        )
        return artifact

    # ------------------------------------------------------------------ #
    # LLM call dispatch                                                   #
    # ------------------------------------------------------------------ #

    def _call_llm(
        self,
        artifact_type: str,
        task: Task,
        memories: list[Memory],
        tool_outputs: list[dict[str, Any]],
        memory_snippets: list[str],
        settings: Settings,
        on_thinking: Any,
        on_content: Any,
    ) -> tuple[dict[str, Any], str]:
        """Dispatch to the right LLM generator per artifact_type.

        Returns (data_dict, mode) where data_dict maps a key like
        "contract"/"sales"/"competitive" to the parsed pydantic model.
        """
        if artifact_type == "contract_review":
            result = ContractReviewLLMGenerator(settings).generate(
                task, memories, tool_outputs,
                on_thinking=on_thinking, on_content=on_content,
            )
            return {"contract": result.data}, result.mode

        if artifact_type == "dashboard":
            return self._call_generic_llm(
                settings=settings,
                system=SALES_FOLLOWUP_SYSTEM_PROMPT,
                user=sales_followup_user_prompt(task.input_message, memory_snippets),
                schema_cls=SalesFollowUpLLMData,
                key="sales",
                on_thinking=on_thinking,
                on_content=on_content,
            )

        if artifact_type == "table":
            return self._call_generic_llm(
                settings=settings,
                system=COMPETITIVE_ANALYSIS_SYSTEM_PROMPT,
                user=competitive_analysis_user_prompt(task.input_message, memory_snippets),
                schema_cls=CompetitiveAnalysisLLMData,
                key="competitive",
                on_thinking=on_thinking,
                on_content=on_content,
            )

        # document or unknown — no specialised LLM yet
        return None, "deterministic"

    def _call_generic_llm(
        self,
        *,
        settings: Settings,
        system: str,
        user: str,
        schema_cls: type,
        key: str,
        on_thinking: Any,
        on_content: Any,
    ) -> tuple[dict[str, Any], str]:
        client = ModelClient(settings)
        if not client.enabled:
            return None, "deterministic"
        try:
            if hasattr(client, "chat_json_streaming_sync"):
                raw = client.chat_json_streaming_sync(
                    system=system, user=user,
                    schema_name=key,
                    temperature=0.3,
                    on_thinking=on_thinking, on_content=on_content,
                )
            else:
                raw = client.chat_json_sync(
                    system=system, user=user,
                    schema_name=key, temperature=0.3,
                )
            data = schema_cls.model_validate(raw)
            return {key: data}, "llm"
        except (ModelClientError, ValidationError, ValueError):
            return None, "deterministic"

    # ------------------------------------------------------------------ #
    # Streaming trace helpers                                             #
    # ------------------------------------------------------------------ #

    def _setup_streaming(self, run: Run, settings: Settings):
        running_step = self.trace.record_started(
            run.id, "llm_generation",
            f"Calling {settings.llm_provider} · {settings.default_model}",
            "",
            input_json={"model": settings.default_model, "provider": settings.llm_provider},
        )
        step_id = running_step.id

        def on_thinking(chunk: str) -> None:
            fresh = self.db.get(type(running_step), step_id)
            if fresh is not None:
                self.trace.append_streaming_chunk(fresh, chunk)

        def on_content(chunk: str) -> None:
            fresh = self.db.get(type(running_step), step_id)
            if fresh is not None:
                self.trace.append_streaming_chunk(fresh, "·", max_chars=200)

        return on_thinking, on_content, running_step

    def _finish_streaming(self, running_step, generation_mode: str, artifact_type: str, settings: Settings):
        if running_step is not None:
            self.trace.record_completed(
                self.db.get(type(running_step), running_step.id) or running_step,
                summary=f"Mode={generation_mode}; type={artifact_type}.",
                output_json={
                    "model": settings.default_model,
                    "runtime_mode": generation_mode,
                    "artifact_type": artifact_type,
                },
            )
