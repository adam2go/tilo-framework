from typing import Any

from sqlalchemy.orm import Session

from app.models import Agent, Artifact, Confirmation, ConversationSession, Memory, Run, Task
from app.services.agent_context import AgentContextBuilder
from app.services.agent_runtime.executor import Executor
from app.services.agent_runtime.planner import Planner
from app.services.agent_runtime.prompt_builder import PromptBuilder
from app.services.agent_runtime.state_machine import RunStateMachine
from app.services.artifact.generator import ArtifactGenerator
from app.services.improvement.metrics import RunMetricsService
from app.services.inbox.confirmations import ConfirmationService
from app.services.interactions.events import UIInteractionEventService
from app.services.memory.extraction import MemoryExtractionService
from app.services.memory.recall import MemoryRecallService, recall_results_to_json
from app.services.skill.selector import SkillSelector
from app.services.trace.recorder import TraceRecorder


class RunManager:
    def __init__(self, db: Session):
        self.db = db
        self.trace = TraceRecorder(db)
        self.state_machine = RunStateMachine()

    def execute(self, task: Task, run: Run, agent: Agent | None = None, session_id: str | None = None) -> dict[str, list[Any]]:
        self.state_machine.transition(task, run, "running")
        self.db.commit()

        artifact: Artifact | None = None
        confirmations: list[Confirmation] = []
        memory_candidates: list[Memory] = []
        tool_outputs: list[dict[str, Any]] = []
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

            tool_outputs = Executor(self.db, self.trace).invoke_tools(task, run)
            artifact = ArtifactGenerator(self.db, self.trace).generate(task, run, memories, tool_outputs)
            confirmations = ConfirmationService(self.db, self.trace).create_for_artifact(task, run, artifact)
            memory_candidates = MemoryExtractionService(self.db, self.trace).extract_candidates(task, run, artifact)

            self.state_machine.transition(task, run, "completed")
            run.result_summary = f"Generated {artifact.type} artifact with {len(confirmations)} confirmation item(s)."
            RunMetricsService(self.db).record_completed(
                task=task,
                run=run,
                artifact_count=1,
                confirmation_count=len(confirmations),
                memory_candidate_count=len(memory_candidates),
                tool_call_count=len(tool_outputs),
            )
            self.db.commit()
            self.db.refresh(task)
            self.db.refresh(run)

            return {"artifacts": [artifact], "confirmations": confirmations, "memory_candidates": memory_candidates}
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
            return {"artifacts": [artifact] if artifact else [], "confirmations": confirmations, "memory_candidates": memory_candidates}


RuntimeResult = dict[str, list[Artifact | Confirmation | Memory]]
