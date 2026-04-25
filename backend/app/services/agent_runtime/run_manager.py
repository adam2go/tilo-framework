from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Agent, Artifact, Confirmation, Memory, Run, Task
from app.services.agent_runtime.executor import Executor
from app.services.agent_runtime.planner import Planner
from app.services.agent_runtime.prompt_builder import PromptBuilder
from app.services.artifact.generator import ArtifactGenerator
from app.services.improvement.metrics import RunMetricsService
from app.services.inbox.confirmations import ConfirmationService
from app.services.memory.extraction import MemoryExtractionService
from app.services.memory.recall import MemoryRecallService, recall_results_to_json
from app.services.skill.selector import SkillSelector
from app.services.trace.recorder import TraceRecorder


class RunManager:
    def __init__(self, db: Session):
        self.db = db
        self.trace = TraceRecorder(db)

    def execute(self, task: Task, run: Run, agent: Agent | None = None) -> dict[str, list[Any]]:
        run.status = "running"
        run.started_at = datetime.utcnow()
        task.status = "running"
        self.db.commit()

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

        prompt = PromptBuilder().build(task, agent, memories, skills, [])
        self.trace.record(run.id, "build_prompt", "Build prompt context", "Built safe runtime context from task, memory, skills, and tools.", output_json={"memory_count": len(prompt["memories"]), "skill_count": len(prompt["skills"])})

        plan = Planner().plan(task, memories, skills)
        run.plan_json = plan
        self.trace.record(run.id, "plan", "Build execution plan", "Created a lightweight rule-based execution plan.", output_json=plan)

        tool_outputs = Executor(self.db, self.trace).invoke_tools(task, run)
        artifact = ArtifactGenerator(self.db, self.trace).generate(task, run, memories, tool_outputs)
        confirmations = ConfirmationService(self.db, self.trace).create_for_artifact(task, run, artifact)
        memory_candidates = MemoryExtractionService(self.db, self.trace).extract_candidates(task, run, artifact)

        run.status = "completed"
        run.result_summary = f"Generated {artifact.type} artifact with {len(confirmations)} confirmation item(s)."
        run.completed_at = datetime.utcnow()
        task.status = "completed"
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


RuntimeResult = dict[str, list[Artifact | Confirmation | Memory]]
