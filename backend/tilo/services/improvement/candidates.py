from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.models import Artifact, Feedback, Run, Skill, SkillCandidate, Task


class SkillCandidateService:
    def __init__(self, db: Session):
        self.db = db

    def maybe_create_from_feedback(self, feedback: Feedback) -> SkillCandidate | None:
        if not feedback.run_id or not self._is_positive_signal(feedback):
            return None
        run = self.db.get(Run, feedback.run_id)
        if not run or run.status != "completed":
            return None
        task = self.db.get(Task, run.task_id)
        if not task:
            return None
        if self.db.scalar(select(SkillCandidate).where(SkillCandidate.source_run_id == run.id)):
            return None

        artifact = self.db.scalar(select(Artifact).where(Artifact.run_id == run.id).order_by(Artifact.created_at.desc()))
        artifact_type = artifact.type if artifact else "document"
        candidate = SkillCandidate(
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            source_run_id=run.id,
            name=self._candidate_name(artifact_type),
            description=f"Reusable workflow proposed from successful run: {task.title}",
            trigger_description=self._trigger_description(task.input_message),
            instructions_markdown=self._instructions_markdown(task.input_message, artifact_type),
            artifact_template_json=self._template_from_artifact(artifact),
            status="pending_review",
            eval_report_json={
                "source": "positive_feedback",
                "feedback_id": feedback.id,
                "rating": feedback.rating,
                "requires_human_review": True,
            },
        )
        self.db.add(candidate)
        self.db.flush()
        return candidate

    def approve(self, candidate: SkillCandidate) -> SkillCandidate:
        candidate.status = "approved"
        candidate.eval_report_json = {
            **(candidate.eval_report_json or {}),
            "approval_gate": "human_approved",
        }
        return candidate

    def reject(self, candidate: SkillCandidate, reason: str | None = None) -> SkillCandidate:
        candidate.status = "rejected"
        candidate.eval_report_json = {
            **(candidate.eval_report_json or {}),
            "rejection_reason": reason,
        }
        return candidate

    def promote(self, candidate: SkillCandidate) -> Skill:
        if candidate.status != "approved":
            raise ValueError("Skill candidate must be approved before promotion")
        self._validate_candidate(candidate)
        skill = Skill(
            workspace_id=candidate.workspace_id,
            name=candidate.name,
            description=candidate.description,
            trigger_description=candidate.trigger_description,
            instructions_markdown=candidate.instructions_markdown,
            input_schema_json={},
            output_schema_json={},
            artifact_template_json=candidate.artifact_template_json,
            required_tool_ids=[],
            version=1,
        )
        self.db.add(skill)
        self.db.flush()
        candidate.status = "promoted"
        candidate.promoted_skill_id = skill.id
        candidate.eval_report_json = {
            **(candidate.eval_report_json or {}),
            "promotion_gate": "approved_candidate_promoted",
            "promoted_skill_id": skill.id,
        }
        return skill

    @staticmethod
    def _is_positive_signal(feedback: Feedback) -> bool:
        text = (feedback.feedback_text or "").lower()
        return feedback.feedback_type == "useful" or (feedback.rating is not None and feedback.rating >= 4) or "save this as a skill" in text

    @staticmethod
    def _candidate_name(artifact_type: str) -> str:
        title = artifact_type.replace("_", " ").title()
        return f"{title} Workflow"

    @staticmethod
    def _trigger_description(message: str) -> str:
        words = [word.strip(".,!?;:").lower() for word in message.split() if len(word.strip(".,!?;:")) > 3]
        return " ".join(dict.fromkeys(words[:12]))

    @staticmethod
    def _instructions_markdown(message: str, artifact_type: str) -> str:
        return (
            f"Use this reusable workflow for requests similar to: {message}\n\n"
            f"Produce an `{artifact_type}` artifact using the framework artifact schema, keep high-risk actions confirmation-gated, "
            "and extract only reviewable memory candidates."
        )

    @staticmethod
    def _validate_candidate(candidate: SkillCandidate) -> None:
        if not candidate.name.strip():
            raise ValueError("Skill candidate name is required")
        if not candidate.instructions_markdown.strip():
            raise ValueError("Skill candidate instructions are required")
        template: dict[str, Any] | None = candidate.artifact_template_json
        if template and template.get("actions"):
            for action in template["actions"]:
                payload = action.get("payload", {})
                if payload.get("permission_level") == "high" and not action.get("confirmation_required"):
                    raise ValueError("High-risk artifact actions must require confirmation")

    @staticmethod
    def _template_from_artifact(artifact: Artifact | None) -> dict[str, Any] | None:
        if not artifact:
            return None
        template = dict(artifact.schema_json)
        template["actions"] = [
            {key: value for key, value in action.items() if key != "confirmation_id"}
            for action in template.get("actions", [])
        ]
        for block in template.get("blocks", []):
            block["actions"] = [
                {key: value for key, value in action.items() if key != "confirmation_id"}
                for action in block.get("actions", [])
            ]
        template["provenance"] = []
        template["memory_refs"] = []
        template["run_id"] = None
        return template
