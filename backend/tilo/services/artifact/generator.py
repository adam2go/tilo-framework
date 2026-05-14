"""Artifact generation — the bridge between agent reasoning and structured output.

AIP v1 flow:
    1. AIPSpecGenerator calls the LLM with primitive block types + skill hints.
    2. LLM generates a complete spec with views + blocks.
    3. Falls back to deterministic spec when LLM is unavailable.
    4. Persist and return the Artifact.

Legacy v0.x flow (kept for backward compat when AIP generator fails):
    Uses ArtifactSpecBuilder from spec.py with type-specific LLM schemas.
"""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from tilo.core.config import Settings, get_settings
from tilo.models import Artifact, Memory, Run, Task
from tilo.services.artifact.aip_generator import AIPSpecGenerator, ArtifactTypeDetector
from tilo.services.artifact.contract_llm import ContractReviewLLMGenerator
from tilo.services.artifact.persistence import ArtifactPersistenceService
from tilo.services.artifact.spec import ArtifactSpecBuilder
from tilo.services.demo import load_problematic_ai_service_agreement
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

        # --- AIP v1 path: unified LLM spec generation ---
        schema: dict[str, Any] | None = None
        generation_mode = "deterministic"

        if settings.llm_enabled and settings.llm_api_key:
            on_thinking, on_content, running_step = self._setup_streaming(run, settings)
            try:
                client = ModelClient(settings)
                # Resolve contract text for contract-review scenarios
                contract_text = self._resolve_contract_text(task.input_message) if artifact_type == "contract_review" else None
                aip_gen = AIPSpecGenerator(client=client)
                schema = aip_gen.generate(
                    task, run, memories, tool_outputs,
                    contract_text=contract_text,
                    on_thinking=on_thinking,
                    on_content=on_content,
                )
                generation_mode = schema.pop("_generation_mode", "llm")
                memory_candidate_data = schema.pop("_memory_candidate", None)
            except Exception:
                schema = None
            finally:
                self._finish_streaming(running_step, generation_mode, artifact_type, settings)
        else:
            self.trace.record(
                run.id, "llm_generation",
                "Skipping LLM (deterministic mode)",
                "No API key configured; using AIP deterministic fallback.",
                output_json={"runtime_mode": "deterministic"},
            )

        # --- Fallback to legacy v0.x spec builder if AIP path failed ---
        if schema is None:
            schema = self._legacy_generate(
                artifact_type, task, run, memories, tool_outputs, settings,
            )
            generation_mode = schema.pop("_generation_mode", "deterministic")

        artifact = self.persistence.create(task=task, run=run, artifact_type=artifact_type, schema_json=schema)
        self.trace.record(
            run.id, "generate_artifact", "Generate artifact",
            f"Created {artifact_type} artifact via {generation_mode}.",
            output_json={
                "artifact_id": artifact.id,
                "title": artifact.title,
                "schema_version": artifact.schema_json.get("version"),
                "action_count": len(artifact.schema_json.get("actions", [])),
                "generation_mode": generation_mode,
            },
        )
        return artifact

    # ------------------------------------------------------------------ #
    # Legacy v0.x path (backward compat)                                  #
    # ------------------------------------------------------------------ #

    def _legacy_generate(
        self,
        artifact_type: str,
        task: Task,
        run: Run,
        memories: list[Memory],
        tool_outputs: list[dict[str, Any]],
        settings: Settings,
    ) -> dict[str, Any]:
        """Fall back to the v0.x ArtifactSpecBuilder."""
        memory_snippets = [m.content for m in memories[:5]]
        llm_data: dict[str, Any] | None = None
        gen_mode = "deterministic"

        if settings.llm_enabled and settings.llm_api_key:
            try:
                llm_data, gen_mode = self._call_legacy_llm(
                    artifact_type, task, memories, tool_outputs,
                    memory_snippets, settings, None, None,
                )
            except Exception:
                pass

        schema = self.builder.build(
            artifact_type, task, run, memories, tool_outputs,
            contract_llm_data=llm_data.get("contract") if llm_data else None,
            sales_llm_data=llm_data.get("sales") if llm_data else None,
            competitive_llm_data=llm_data.get("competitive") if llm_data else None,
            generation_mode=gen_mode,
        )
        follow_ups = self._extract_follow_ups(llm_data)
        if follow_ups:
            schema["follow_ups"] = follow_ups
        schema["_generation_mode"] = gen_mode
        return schema

    def _call_legacy_llm(
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
    # Contract text resolution                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _resolve_contract_text(message: str) -> str | None:
        """Resolve the contract text to inject into the LLM prompt."""
        if len(message) > 500:
            return None
        fixture_signals = [
            "AI 客服", "ai service agreement", "service agreement",
            "liability", "indemnity", "8.1", "8.2",
            "合同", "条款", "责任上限", "赔偿",
            "risky clauses", "flag risky",
        ]
        text_lower = message.lower()
        if any(sig.lower() in text_lower for sig in fixture_signals):
            try:
                fixture = load_problematic_ai_service_agreement()
                return fixture.content
            except FileNotFoundError:
                return None
        return None

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

    @staticmethod
    def _extract_follow_ups(llm_data: dict[str, Any] | None) -> list[str]:
        """Pull follow_ups from whichever LLM data object was produced."""
        if not llm_data:
            return []
        for value in llm_data.values():
            if value is None:
                continue
            fups = getattr(value, "follow_ups", None)
            if fups and isinstance(fups, list):
                return [str(f) for f in fups[:3]]
        return []
