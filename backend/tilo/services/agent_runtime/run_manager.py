from typing import Any

from sqlalchemy.orm import Session

from tilo.models import (
    Agent,
    Artifact,
    Confirmation,
    ConversationSession,
    Memory,
    Run,
    SurfaceTurn,
    Task,
)
from tilo.services.agent_context import AgentContextBuilder
from tilo.services.agent_runtime.executor import Executor
from tilo.services.agent_runtime.planner import Planner
from tilo.services.agent_runtime.prompt_builder import PromptBuilder
from tilo.services.agent_runtime.state_machine import RunStateMachine
from tilo.services.artifact.generator import ArtifactGenerator
from tilo.services.improvement.metrics import RunMetricsService
from tilo.services.inbox.confirmations import ConfirmationService
from tilo.services.interaction_policy.schemas import (
    InteractionContext,
    InteractionDecision,
    InteractionDecisionType,
    InteractionPolicy,
)
from tilo.services.interaction_policy.service import InteractionPolicyService
from tilo.services.interactions.events import UIInteractionEventService
from tilo.services.memory.extraction import MemoryExtractionService
from tilo.services.memory.recall import MemoryRecallService, recall_results_to_json
from tilo.services.skill.selector import SkillSelector
from tilo.services.surface.composer import (
    ComposerInput,
    DeterministicSurfaceComposer,
    safe_compose,
)
from tilo.services.surface.persistence import SurfaceTurnService
from tilo.services.trace.recorder import TraceRecorder


# Plan-step types that are eligible for surface emission. Excluding the rest
# (e.g. recall_memory) prevents low-value mini surfaces from polluting the
# conversation. This is the runtime expression of "less UI is the default"
# (see docs/INTERACTION_POLICY.md).
_SURFACE_EMITTING_STEP_TYPES = {
    "generate_artifact",
    "ask_confirmation",
    "extract_memory",
    "ask_clarification",
    "collect_input",
    "offer_choices",
}


class RunManager:
    def __init__(self, db: Session):
        self.db = db
        self.trace = TraceRecorder(db)
        self.state_machine = RunStateMachine()
        self._composer = DeterministicSurfaceComposer()
        self._surface_turns = SurfaceTurnService(db)

    def execute(self, task: Task, run: Run, agent: Agent | None = None, session_id: str | None = None) -> dict[str, list[Any]]:
        self.state_machine.transition(task, run, "running")
        self.db.commit()

        artifact: Artifact | None = None
        confirmations: list[Confirmation] = []
        memory_candidates: list[Memory] = []
        tool_outputs: list[dict[str, Any]] = []
        surface_turns: list[SurfaceTurn] = []

        try:
            recall_results = MemoryRecallService(self.db).recall_for_task_with_scores(task, run_id=run.id)
            memories = [result.memory for result in recall_results]
            self.trace.record(
                run.id,
                "recall_memory",
                "Recall memory",
                f"Recalled {len(memories)} confirmed memories.",
                {"query": task.input_message},
                {"count": len(memories), "strategy": "hybrid_v0.2", "scores": recall_results_to_json(recall_results)},
            )

            skills = SkillSelector(self.db).select_for_task(task, agent)
            self.trace.record(run.id, "select_skill", "Select skills", f"Selected {len(skills)} candidate skills.", output_json={"skill_ids": [skill.id for skill in skills]})

            resolved_session_id = session_id or run.session_id
            recent_ui_observations = UIInteractionEventService(self.db).recent_for_context(workspace_id=task.workspace_id, project_id=task.project_id)
            recent_conversation_turns: list[dict[str, Any]] = []
            app_id: str | None = None
            if resolved_session_id:
                session = self.db.get(ConversationSession, resolved_session_id)
                app_id = session.app_id if session else "contract-review-agent"
                context = AgentContextBuilder(self.db).build(
                    app_id=app_id,
                    workspace_id=task.workspace_id,
                    project_id=task.project_id,
                    session_id=resolved_session_id,
                )
                recent_conversation_turns = context["recent_conversation_turns"]
                recent_ui_observations = context["recent_ui_observations"]
            prompt = PromptBuilder().build(
                task,
                agent,
                memories,
                skills,
                [],
                recent_ui_observations=recent_ui_observations,
                recent_conversation_turns=recent_conversation_turns,
            )
            self.trace.record(
                run.id,
                "build_prompt",
                "Build prompt context",
                "Built safe runtime context from task, memory, skills, tools, recent turns, and recent UI observations.",
                output_json={
                    "memory_count": len(prompt["memories"]),
                    "confirmed_memory_count": len(memories),
                    "skill_count": len(prompt["skills"]),
                    "recent_ui_observation_count": len(prompt["recent_ui_observations"]),
                    "recent_conversation_turn_count": len(prompt["recent_conversation_turns"]),
                },
            )

            plan = Planner().plan(task, memories, skills)
            run.plan_json = plan
            self.trace.record(run.id, "plan", "Build execution plan", "Created a lightweight rule-based execution plan.", output_json=plan)

            # ------------------------------------------------------------- #
            # Phase 2: streaming surface loop                                #
            # ------------------------------------------------------------- #
            #
            # Walk the plan once. For each step:
            #   1. evaluate the InteractionPolicy (Phase 1, retained);
            #   2. perform the side effect the step represents
            #      (generate_artifact, invoke_tool, extract_memory, ...);
            #   3. if the policy decision asks for UI, compose a SurfaceSpec
            #      via the DeterministicSurfaceComposer and persist a
            #      SurfaceTurn (which also writes a ConversationTurn).
            #
            # Tool invocation runs once before the loop (preserves existing
            # behaviour); generate_artifact is the step that produces the
            # rich artifact and the matching escalate_to_rich surface.
            tool_outputs = Executor(self.db, self.trace).invoke_tools(task, run)

            policy = self._load_policy(run_id=run.id, app_id=app_id)
            decisions: list[InteractionDecision] = []
            counters = _Counters()

            for index, step in enumerate(plan.get("steps", [])):
                ctx = self._context_from_step(step, counters=counters)
                decision = (
                    InteractionPolicyService().evaluate(policy, ctx)
                    if policy is not None
                    else InteractionDecision(decision=InteractionDecisionType.no_ui, reason="policy_unavailable")
                )
                decisions.append(decision)
                self.trace.record(
                    run.id,
                    "policy_decision",
                    f"Policy: step {index} ({step.get('type', 'step')})",
                    self._policy_summary(decision, step),
                    input_json=self._safe_step_for_trace(step),
                    output_json=self._policy_decision_to_json(decision, step_index=index),
                )

                # Step side effect: only generate_artifact has one in this
                # deterministic v0.1 runtime. Others are accounted for after
                # the loop (extract_memory) or already-completed (recall_memory,
                # select_skill, invoke_tool). Future steps with side effects
                # should branch here.
                if step.get("type") == "generate_artifact" and artifact is None:
                    artifact = ArtifactGenerator(self.db, self.trace).generate(task, run, memories, tool_outputs)
                    confirmations = ConfirmationService(self.db, self.trace).create_for_artifact(task, run, artifact)

                # Surface emission: only when policy says so AND the step is
                # surface-eligible. Less-UI default is enforced by the gate.
                if (
                    decision.decision == InteractionDecisionType.mini_surface
                    or decision.decision == InteractionDecisionType.rich_surface
                ) and step.get("type") in _SURFACE_EMITTING_STEP_TYPES:
                    surface_turn = self._emit_surface(
                        task=task,
                        run=run,
                        plan_step=step,
                        plan_step_index=index,
                        decision=decision,
                        memories=memories,
                        tool_outputs=tool_outputs,
                        artifact=artifact,
                        ordinal=len(surface_turns),
                        session_id=resolved_session_id,
                    )
                    if surface_turn is not None:
                        surface_turns.append(surface_turn)
                        counters.record(decision)

            # extract_memory side effect: always runs after the loop, so the
            # confirm_memory surface (when policy emitted one) has a candidate
            # to point at. Memory candidates persist independently of whether
            # a UI was emitted — that's the whole point of "candidate-first".
            memory_candidates = MemoryExtractionService(self.db, self.trace).extract_candidates(task, run, artifact)

            plan["policy_decisions"] = [
                self._policy_decision_to_json(decision, step_index=index)
                for index, decision in enumerate(decisions)
            ]
            plan["surface_turn_ids"] = [turn.id for turn in surface_turns]
            run.plan_json = plan

            self.state_machine.transition(task, run, "completed")
            artifact_summary = (
                f"Generated {artifact.type} artifact with {len(confirmations)} confirmation item(s)."
                if artifact
                else "Run completed without an artifact."
            )
            run.result_summary = (
                f"{artifact_summary} Emitted {len(surface_turns)} surface turn(s)."
            )
            RunMetricsService(self.db).record_completed(
                task=task,
                run=run,
                artifact_count=1 if artifact else 0,
                confirmation_count=len(confirmations),
                memory_candidate_count=len(memory_candidates),
                tool_call_count=len(tool_outputs),
            )
            self.db.commit()
            self.db.refresh(task)
            self.db.refresh(run)

            return {
                "artifacts": [artifact] if artifact else [],
                "confirmations": confirmations,
                "memory_candidates": memory_candidates,
                "surface_turns": surface_turns,
            }
        except Exception as exc:
            self.db.rollback()
            safe_error = RunStateMachine.safe_reason(str(exc) or exc.__class__.__name__)
            self.state_machine.transition(task, run, "failed", safe_error)
            RunMetricsService(self.db).record_completed(
                task=task,
                run=run,
                artifact_count=1 if artifact else 0,
                confirmation_count=len(confirmations),
                memory_candidate_count=len(memory_candidates),
                tool_call_count=len(tool_outputs),
                error_count=1,
            )
            self.trace.record_failed(
                run.id,
                "runtime_error",
                "Runtime failed",
                "Run failed with a safe error summary.",
                output_json={"error": safe_error, "error_type": exc.__class__.__name__},
            )
            self.db.commit()
            self.db.refresh(task)
            self.db.refresh(run)
            return {
                "artifacts": [artifact] if artifact else [],
                "confirmations": confirmations,
                "memory_candidates": memory_candidates,
                "surface_turns": surface_turns,
            }

    # ------------------------------------------------------------------ #
    # Surface emission                                                   #
    # ------------------------------------------------------------------ #

    def _emit_surface(
        self,
        *,
        task: Task,
        run: Run,
        plan_step: dict[str, Any],
        plan_step_index: int,
        decision: InteractionDecision,
        memories: list[Memory],
        tool_outputs: list[dict[str, Any]],
        artifact: Artifact | None,
        ordinal: int,
        session_id: str | None,
    ) -> SurfaceTurn | None:
        if decision.intent is None:
            # Defensive: a UI decision without an intent shouldn't happen
            # after Phase 1 schema normalisation, but if it does we skip
            # silently rather than blow up the whole run.
            self.trace.record(
                run.id,
                "surface_skipped",
                f"Surface skipped · step {plan_step_index}",
                "Policy decision had no intent; surface emission skipped.",
                output_json=self._policy_decision_to_json(decision, step_index=plan_step_index),
                status="completed",
            )
            return None

        artifact_summary = self._artifact_summary(artifact)
        composer_input = ComposerInput(
            intent=decision.intent,
            decision=decision,
            plan_step=plan_step,
            plan_step_index=plan_step_index,
            task=task,
            run=run,
            memories=memories,
            tool_outputs=tool_outputs,
            artifact_id=artifact.id if artifact else None,
            artifact_summary=artifact_summary,
        )
        composed = safe_compose(composer_input, self._composer)

        turn = self._surface_turns.persist(
            task=task,
            run=run,
            composed=composed,
            decision=decision,
            plan_step=plan_step,
            plan_step_index=plan_step_index,
            ordinal=ordinal,
            session_id=session_id,
            artifact_id=artifact.id if artifact else None,
        )
        self.trace.record(
            run.id,
            "render_surface",
            f"Render surface · {decision.intent.value} (step {plan_step_index})",
            f"Persisted SurfaceTurn ordinal={ordinal} via {composed.composer_mode}.",
            output_json={
                "surface_turn_id": turn.id,
                "intent": decision.intent.value,
                "budget_hint": turn.budget_hint,
                "composer_mode": composed.composer_mode,
                "fallback_reason": composed.fallback_reason,
                "ordinal": ordinal,
            },
        )
        return turn

    @staticmethod
    def _artifact_summary(artifact: Artifact | None) -> dict[str, Any] | None:
        if artifact is None:
            return None
        schema = artifact.schema_json or {}
        risk_block = next(
            (block for block in schema.get("blocks", []) if block.get("id") == "risk_summary"),
            None,
        )
        memory_block = next(
            (block for block in schema.get("blocks", []) if block.get("id") == "memory_candidate"),
            None,
        )
        summary: dict[str, Any] = {
            "artifact_id": artifact.id,
            "title": artifact.title,
            "summary": (risk_block.get("data", {}).get("summary") if risk_block else None) or schema.get("title"),
            "high_count": (risk_block.get("data", {}).get("high_count") if risk_block else None),
            "medium_count": (risk_block.get("data", {}).get("medium_count") if risk_block else None),
            "low_count": (risk_block.get("data", {}).get("low_count") if risk_block else None),
        }
        if memory_block:
            summary["memory_candidate"] = memory_block.get("data") or {}
        return summary

    # ------------------------------------------------------------------ #
    # Policy helpers                                                     #
    # ------------------------------------------------------------------ #

    def _load_policy(self, *, run_id: str, app_id: str | None) -> InteractionPolicy | None:
        if app_id is None:
            return None
        try:
            return InteractionPolicyService().load_for_app(app_id)
        except (FileNotFoundError, ValueError) as exc:
            self.trace.record(
                run_id,
                "policy_decision",
                "Policy load skipped",
                f"Could not load policy for app {app_id!r}; defaulting to no_ui for all steps.",
                output_json={"error": str(exc), "app_id": app_id},
            )
            return None

    @staticmethod
    def _context_from_step(step: dict[str, Any], *, counters: "_Counters") -> InteractionContext:
        return InteractionContext(
            artifact_type=step.get("artifact_type"),
            risk_level=step.get("risk_level"),
            requires_user_decision=step.get("requires_user_decision"),
            category=step.get("category"),
            signal=step.get("signal"),
            mini_surfaces_used=counters.mini,
            confirmations_used=counters.confirmations,
            memory_cards_used=counters.memory,
        )

    @staticmethod
    def _policy_decision_to_json(decision: InteractionDecision, *, step_index: int) -> dict[str, Any]:
        return {
            "step_index": step_index,
            "decision": decision.decision.value,
            "intent": decision.intent.value if decision.intent else None,
            "surface": decision.surface,
            "reason": decision.reason,
            "rule_id": decision.rule_id,
        }

    @staticmethod
    def _policy_summary(decision: InteractionDecision, step: dict[str, Any]) -> str:
        target = (
            decision.intent.value if decision.intent
            else decision.surface or "—"
        )
        return f"{decision.decision.value} ({target}) · reason={decision.reason}"

    @staticmethod
    def _safe_step_for_trace(step: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": step.get("type"),
            "signal": step.get("signal"),
            "risk_level": step.get("risk_level"),
            "category": step.get("category"),
            "requires_user_decision": step.get("requires_user_decision"),
            "artifact_type": step.get("artifact_type"),
        }


class _Counters:
    """Real-time UI budget counters during a single run."""

    __slots__ = ("mini", "confirmations", "memory")

    def __init__(self) -> None:
        self.mini = 0
        self.confirmations = 0
        self.memory = 0

    def record(self, decision: InteractionDecision) -> None:
        if decision.decision != InteractionDecisionType.mini_surface:
            return
        self.mini += 1
        if decision.intent is not None:
            if decision.intent.value == "request_approval":
                self.confirmations += 1
            elif decision.intent.value == "confirm_memory":
                self.memory += 1


RuntimeResult = dict[str, list[Artifact | Confirmation | Memory | SurfaceTurn]]


__all__ = ["RunManager", "RuntimeResult", "InteractionPolicy"]
