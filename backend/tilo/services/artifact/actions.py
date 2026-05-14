from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from tilo.models import Artifact, Confirmation, Memory, Run, SkillCandidate, Tool, UIInteractionEvent
from tilo.schemas import ArtifactActionResult
from tilo.schemas.artifact import ArtifactAction, ArtifactBlock, ArtifactSpecV1, StateBinding, SUPPORTED_ACTION_TYPES
from tilo.services.context_reflection import ContextReflectionService
from tilo.services.conversations.messages import ConversationMessageService
from tilo.services.conversations.service import ConversationService
from tilo.services.improvement.candidates import SkillCandidateService
from tilo.services.interactions.events import UIInteractionEventService
from tilo.services.memory.writer import MemoryWriter
from tilo.services.tools.invocation import ToolInvocationService
from tilo.services.trace.recorder import TraceSanitizer


class ArtifactActionRuntimeError(ValueError):
    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ResolvedAction:
    action: ArtifactAction
    block: ArtifactBlock | None
    binding: StateBinding | None


class ArtifactActionRuntime:
    """Server-side ROAM action semantics for artifact action buttons."""

    REFLECTION_ACTION_TYPES = {"approve", "confirm", "reject", "select", "edit"}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.sanitizer = TraceSanitizer()

    def execute(
        self,
        *,
        artifact_id: str,
        action_id: str,
        block_id: str | None = None,
        session_id: str | None = None,
        run_id: str | None = None,
        source: str = "web",
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> ArtifactActionResult:
        artifact = self.db.get(Artifact, artifact_id)
        if not artifact:
            raise ArtifactActionRuntimeError("Artifact not found", status_code=404)

        request_payload = self._safe_payload(payload or {})
        resolved = self._resolve(artifact, action_id, block_id)
        effective_run_id = run_id or artifact.run_id or self._artifact_spec_run_id(artifact.schema_json)
        if session_id and not ConversationService(self.db).get_session(session_id):
            raise ArtifactActionRuntimeError("Conversation session not found", status_code=404)

        event = self._create_interaction_event(
            artifact=artifact,
            resolved=resolved,
            run_id=effective_run_id,
            source=source,
            request_payload=request_payload,
            idempotency_key=idempotency_key,
        )
        turn_id, warnings = self._append_observation(session_id=session_id, event=event)

        result = self._execute_handler(
            artifact=artifact,
            resolved=resolved,
            session_id=session_id,
            run_id=effective_run_id,
            request_payload=request_payload,
            warnings=warnings,
        )
        result.interaction_event_id = event.id
        result.conversation_turn_id = turn_id
        result.warnings = warnings + result.warnings

        if session_id and resolved.action.action_type in self.REFLECTION_ACTION_TYPES:
            try:
                ContextReflectionService(self.db).reflect_and_persist(
                    session_id=session_id,
                    trigger_event_id=event.id,
                    artifact_id=artifact.id,
                )
            except Exception as exc:  # pragma: no cover - defensive safety hook
                result.warnings.append(f"Context reflection skipped: {exc}")
        return result

    def _resolve(self, artifact: Artifact, action_id: str, block_id: str | None) -> ResolvedAction:
        schema = artifact.schema_json or {}
        try:
            spec = ArtifactSpecV1.model_validate(schema)
        except ValidationError as exc:
            return self._resolve_invalid_spec(schema, artifact.id, action_id, block_id, exc)

        if block_id:
            block = next((item for item in spec.blocks if item.id == block_id), None)
            if block is not None:
                action = next((item for item in block.actions if item.id == action_id), None)
                if action:
                    return ResolvedAction(action=action, block=block, binding=action.state_binding or block.state_binding)
            # block_id was supplied but doesn't match this artifact's schema
            # (common when a surface composed on top of an artifact carries
            # its own block ids — the surface protocol's block ids don't
            # have to equal the artifact schema's). Fall through to
            # action_id-based resolution rather than failing the request.

        block_matches = [(block, action) for block in spec.blocks for action in block.actions if action.id == action_id]
        artifact_action = next((item for item in spec.actions if item.id == action_id), None)
        if artifact_action:
            return ResolvedAction(action=artifact_action, block=None, binding=artifact_action.state_binding)
        if len(block_matches) > 1 and not block_id:
            raise ArtifactActionRuntimeError(f"Action '{action_id}' exists in multiple blocks; block_id is required")
        if len(block_matches) == 1:
            block, action = block_matches[0]
            return ResolvedAction(action=action, block=block, binding=action.state_binding or block.state_binding)

        raise ArtifactActionRuntimeError(f"Artifact action '{action_id}' was not found", status_code=404)

    def _resolve_invalid_spec(
        self,
        schema: dict[str, Any],
        artifact_id: str,
        action_id: str,
        block_id: str | None,
        error: ValidationError,
    ) -> ResolvedAction:
        raw_action, raw_block = self._find_raw_action(schema, action_id, block_id)
        if not raw_action:
            raise ArtifactActionRuntimeError(f"Artifact action '{action_id}' was not found", status_code=404)
        action_type = str(raw_action.get("action_type") or "")
        if action_type and action_type not in SUPPORTED_ACTION_TYPES:
            action = ArtifactAction.model_construct(
                id=action_id,
                label=str(raw_action.get("label") or action_id),
                action_type=action_type,
                confirmation_required=bool(raw_action.get("confirmation_required")),
                confirmation_id=raw_action.get("confirmation_id"),
                payload=raw_action.get("payload") or {},
                state_binding=None,
            )
            block = None
            if raw_block:
                block = ArtifactBlock.model_construct(
                    id=str(raw_block.get("id") or block_id or "block"),
                    type=str(raw_block.get("type") or "card"),
                    title=raw_block.get("title"),
                    data=raw_block.get("data") or {},
                    actions=[],
                    state_binding=None,
                )
            return ResolvedAction(action=action, block=block, binding=None)
        raise ArtifactActionRuntimeError(f"Artifact '{artifact_id}' has invalid artifact_spec.v1: {error}", status_code=422)

    def _find_raw_action(self, schema: dict[str, Any], action_id: str, block_id: str | None) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if block_id:
            for block in schema.get("blocks") or []:
                if block.get("id") == block_id:
                    for action in block.get("actions") or []:
                        if action.get("id") == action_id:
                            return action, block
        for action in schema.get("actions") or []:
            if action.get("id") == action_id:
                return action, None
        for block in schema.get("blocks") or []:
            for action in block.get("actions") or []:
                if action.get("id") == action_id:
                    return action, block
        return None, None

    def _create_interaction_event(
        self,
        *,
        artifact: Artifact,
        resolved: ResolvedAction,
        run_id: str | None,
        source: str,
        request_payload: dict[str, Any],
        idempotency_key: str | None,
    ) -> UIInteractionEvent:
        return UIInteractionEventService(self.db).create(
            workspace_id=artifact.workspace_id,
            project_id=artifact.project_id,
            artifact_id=artifact.id,
            block_id=resolved.block.id if resolved.block else None,
            action_id=resolved.action.id,
            run_id=run_id,
            event_type=self._event_type_for_action(resolved.action.action_type),
            payload_json={
                "source": source,
                "action_type": resolved.action.action_type,
                "confirmation_id": resolved.action.confirmation_id,
                "state_binding": resolved.binding.model_dump(mode="json") if resolved.binding else None,
                "action_payload": resolved.action.payload,
                "request_payload": request_payload,
                "idempotency_key": idempotency_key,
            },
        )

    def _append_observation(self, *, session_id: str | None, event: UIInteractionEvent) -> tuple[str | None, list[str]]:
        if not session_id:
            return None, []
        conversation = ConversationService(self.db)
        if not conversation.get_session(session_id):
            raise ArtifactActionRuntimeError("Conversation session not found", status_code=404)
        turn = conversation.append_observation_for_interaction(session_id, event)
        return turn.id, []

    def _execute_handler(
        self,
        *,
        artifact: Artifact,
        resolved: ResolvedAction,
        session_id: str | None,
        run_id: str | None,
        request_payload: dict[str, Any],
        warnings: list[str],
    ) -> ArtifactActionResult:
        action_type = resolved.action.action_type
        if action_type not in SUPPORTED_ACTION_TYPES:
            return self._result(artifact, resolved, "failed", f"Unsupported artifact action type: {action_type}", run_id=run_id)
        if action_type in {"approve", "confirm", "reject"}:
            return self._handle_confirmation_or_memory(artifact, resolved, run_id, request_payload)
        if action_type == "create_memory":
            return self._handle_create_memory(artifact, resolved, run_id, request_payload)
        if action_type == "continue_task":
            return self._handle_continue_task(artifact, resolved, session_id, request_payload, warnings)
        if action_type == "invoke_tool":
            return self._handle_invoke_tool(artifact, resolved, run_id, request_payload)
        if action_type == "promote_skill":
            return self._handle_promote_skill(artifact, resolved, run_id)
        if action_type == "regenerate":
            return self._result(artifact, resolved, "noop", "Artifact regeneration is not implemented in v0.9.", run_id=run_id)
        if action_type == "export":
            return self._result(artifact, resolved, "noop", "Structured JSON export is available by reading the artifact; file export is not implemented yet.", run_id=run_id)
        if action_type in {"select", "edit"}:
            return self._result(artifact, resolved, "completed", f"Recorded {action_type} action.", run_id=run_id)
        return self._result(artifact, resolved, "noop", f"No handler is available for action type {action_type}.", run_id=run_id)

    def _handle_confirmation_or_memory(
        self,
        artifact: Artifact,
        resolved: ResolvedAction,
        run_id: str | None,
        request_payload: dict[str, Any],
    ) -> ArtifactActionResult:
        is_reject = resolved.action.action_type == "reject"
        confirmation_id = self._confirmation_id(resolved)
        memory_id = self._bound_entity_id(resolved, "memory")

        if confirmation_id:
            confirmation = self.db.get(Confirmation, confirmation_id)
            if not confirmation:
                return self._result(artifact, resolved, "failed", "Linked confirmation was not found.", confirmation_id=confirmation_id, run_id=run_id)
            if confirmation.status != "pending":
                return self._result(artifact, resolved, "noop", f"Confirmation is already {confirmation.status}.", confirmation_id=confirmation.id, run_id=run_id)
            confirmation.status = "rejected" if is_reject else "approved"
            confirmation.decision_json = (
                {"reason": request_payload.get("reason") or "Rejected from artifact action runtime"}
                if is_reject
                else {"decision": {"source": "artifact_action_runtime", "action_id": resolved.action.id, **self._dict_value(request_payload.get("decision"))}}
            )
            self.db.commit()
            return self._result(
                artifact,
                resolved,
                "rejected" if is_reject else "completed",
                f"Confirmation {confirmation.status}.",
                confirmation_id=confirmation.id,
                run_id=confirmation.run_id or run_id,
            )

        if memory_id:
            memory = self.db.get(Memory, memory_id)
            if not memory:
                return self._result(artifact, resolved, "failed", "Linked memory was not found.", memory_id=memory_id, run_id=run_id)
            writer = MemoryWriter(self.db)
            if is_reject:
                writer.reject(memory, str(request_payload.get("reason") or "Rejected from artifact action runtime"))
            else:
                writer.confirm(memory)
            self.db.commit()
            return self._result(
                artifact,
                resolved,
                "rejected" if is_reject else "completed",
                f"Memory {memory.status}.",
                memory_id=memory.id,
                run_id=memory.source_run_id or run_id,
            )

        return self._result(artifact, resolved, "completed", f"Recorded {resolved.action.action_type} action.", run_id=run_id)

    def _handle_create_memory(
        self,
        artifact: Artifact,
        resolved: ResolvedAction,
        run_id: str | None,
        request_payload: dict[str, Any],
    ) -> ArtifactActionResult:
        merged_payload = {**resolved.action.payload, **request_payload}
        content = str(merged_payload.get("content") or (resolved.block.data.get("content") if resolved.block else "") or "").strip()
        if not content:
            return self._result(artifact, resolved, "failed", "create_memory requires memory content.", run_id=run_id)
        memory = MemoryWriter(self.db).create_candidate(
            workspace_id=artifact.workspace_id,
            project_id=artifact.project_id,
            run_id=run_id,
            content=content,
            memory_type=str(merged_payload.get("type") or merged_payload.get("memory_type") or "task_experience"),
            confidence=float(merged_payload.get("confidence") or (resolved.block.data.get("confidence") if resolved.block else 0.72) or 0.72),
            source_artifact_id=artifact.id,
            reason="Created from artifact action runtime.",
            structured_payload={
                "source": "artifact_action_runtime",
                "artifact_id": artifact.id,
                "block_id": resolved.block.id if resolved.block else None,
                "action_id": resolved.action.id,
            },
        )
        self.db.commit()
        return self._result(artifact, resolved, "completed", "Memory candidate created.", memory_id=memory.id, run_id=run_id)

    def _handle_continue_task(
        self,
        artifact: Artifact,
        resolved: ResolvedAction,
        session_id: str | None,
        request_payload: dict[str, Any],
        warnings: list[str],
    ) -> ArtifactActionResult:
        if not session_id:
            return self._result(artifact, resolved, "noop", "continue_task requires session_id.")
        content = str(request_payload.get("content") or resolved.action.payload.get("content") or "").strip()
        if not content:
            return self._result(artifact, resolved, "noop", "continue_task requires payload.content.")
        try:
            message = ConversationMessageService(self.db).send_message(session_id, content=content, attachments=[])
        except Exception as exc:
            warnings.append(f"Conversation continuation failed: {exc}")
            return self._result(artifact, resolved, "failed", "Conversation continuation failed.")
        return self._result(
            artifact,
            resolved,
            "completed",
            "Conversation task continued.",
            task_id=message.get("task_id"),
            run_id=message.get("run_id"),
        )

    def _handle_invoke_tool(
        self,
        artifact: Artifact,
        resolved: ResolvedAction,
        run_id: str | None,
        request_payload: dict[str, Any],
    ) -> ArtifactActionResult:
        action_payload = {**resolved.action.payload, **request_payload}
        tool_id = str(action_payload.get("tool_id") or self._bound_entity_id(resolved, "tool_invocation") or "")
        tool = self.db.get(Tool, tool_id) if tool_id else None
        confirmation_required = bool(resolved.action.confirmation_required or action_payload.get("confirmation_required"))

        if confirmation_required and (not tool or not run_id):
            confirmation = Confirmation(
                workspace_id=artifact.workspace_id,
                task_id=artifact.task_id,
                run_id=run_id,
                type="tool_permission",
                title=str(action_payload.get("title") or "Approve tool invocation"),
                description="Tool invocation requires approval before execution.",
                payload_json={
                    "artifact_id": artifact.id,
                    "artifact_action_id": resolved.action.id,
                    "input": self._safe_payload(self._dict_value(action_payload.get("input"))),
                },
            )
            self.db.add(confirmation)
            self.db.commit()
            return self._result(
                artifact,
                resolved,
                "pending_confirmation",
                "Tool invocation is waiting for confirmation.",
                confirmation_id=confirmation.id,
                run_id=run_id,
            )

        if not tool:
            return self._result(artifact, resolved, "noop", "invoke_tool requires a valid payload.tool_id.", run_id=run_id)

        input_payload = self._dict_value(action_payload.get("input"))
        if tool.permission_level == "high" or confirmation_required:
            run = self.db.get(Run, run_id) if run_id else None
            if not run:
                return self._handle_invoke_tool(artifact, resolved, None, {**request_payload, "confirmation_required": True})
            invocation, output = ToolInvocationService(self.db).invoke_registered(tool, input_payload, task_id=run.task_id, run_id=run.id)
            if invocation.status == "pending_confirmation":
                return self._result(
                    artifact,
                    resolved,
                    "pending_confirmation",
                    "Tool invocation is waiting for confirmation.",
                    confirmation_id=output.get("confirmation_id"),
                    tool_invocation_id=invocation.id,
                    run_id=run.id,
                )

        if run_id:
            run = self.db.get(Run, run_id)
            if run:
                invocation, _ = ToolInvocationService(self.db).invoke_registered(tool, input_payload, task_id=run.task_id, run_id=run.id)
                return self._result(
                    artifact,
                    resolved,
                    "completed" if invocation.status == "completed" else "pending_confirmation",
                    "Tool invocation handled.",
                    confirmation_id=invocation.confirmation_id,
                    tool_invocation_id=invocation.id,
                    run_id=run.id,
                )
        output = ToolInvocationService(self.db).invoke_direct(tool, input_payload)
        return self._result(
            artifact,
            resolved,
            "completed",
            "Tool invocation handled.",
            task_id=output.get("task_id"),
            run_id=output.get("run_id"),
            tool_invocation_id=output.get("tool_invocation_id"),
        )

    def _handle_promote_skill(self, artifact: Artifact, resolved: ResolvedAction, run_id: str | None) -> ArtifactActionResult:
        skill_candidate_id = self._bound_entity_id(resolved, "skill_candidate")
        if not skill_candidate_id:
            return self._result(artifact, resolved, "noop", "promote_skill requires a skill_candidate binding.", run_id=run_id)
        candidate = self.db.get(SkillCandidate, skill_candidate_id)
        if not candidate:
            return self._result(artifact, resolved, "failed", "Linked skill candidate was not found.", run_id=run_id)
        skill = SkillCandidateService(self.db).promote(candidate)
        self.db.commit()
        return self._result(artifact, resolved, "completed", "Skill candidate promoted.", run_id=run_id, next_actions=[{"skill_id": skill.id}])

    def _result(
        self,
        artifact: Artifact,
        resolved: ResolvedAction,
        status: str,
        message: str,
        *,
        confirmation_id: str | None = None,
        memory_id: str | None = None,
        tool_invocation_id: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
        artifact_version_id: str | None = None,
        next_actions: list[dict[str, Any]] | None = None,
    ) -> ArtifactActionResult:
        return ArtifactActionResult(
            status=status,
            action_id=resolved.action.id,
            artifact_id=artifact.id,
            block_id=resolved.block.id if resolved.block else None,
            confirmation_id=confirmation_id,
            memory_id=memory_id,
            tool_invocation_id=tool_invocation_id,
            task_id=task_id,
            run_id=run_id,
            artifact_version_id=artifact_version_id,
            message=message,
            next_actions=next_actions or [],
        )

    def _confirmation_id(self, resolved: ResolvedAction) -> str | None:
        return resolved.action.confirmation_id or self._bound_entity_id(resolved, "confirmation")

    @staticmethod
    def _bound_entity_id(resolved: ResolvedAction, entity_type: str) -> str | None:
        if resolved.binding and resolved.binding.entity_type == entity_type:
            return resolved.binding.entity_id
        return None

    @staticmethod
    def _event_type_for_action(action_type: str) -> str:
        mapping = {
            "approve": "artifact.action.approved",
            "confirm": "artifact.action.approved",
            "reject": "artifact.action.rejected",
            "select": "artifact.option.selected",
            "edit": "artifact.block.edited",
            "create_memory": "memory.candidate.created",
            "promote_skill": "skill.candidate.promoted",
            "invoke_tool": "tool.invocation.requested",
            "continue_task": "task.continue_requested",
            "regenerate": "artifact.regenerate_requested",
            "export": "artifact.export_requested",
        }
        return mapping.get(action_type, "artifact.action.clicked")

    @staticmethod
    def _artifact_spec_run_id(schema: dict[str, Any]) -> str | None:
        value = schema.get("run_id")
        return str(value) if value else None

    def _safe_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        sanitized = self.sanitizer.sanitize(payload)
        if not isinstance(sanitized, dict):
            return {}
        for key in ("contract_text", "raw_contract", "document_text", "full_text"):
            if key in sanitized:
                sanitized[key] = "[REDACTED]"
        return sanitized

    @staticmethod
    def _dict_value(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}
