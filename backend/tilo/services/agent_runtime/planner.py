"""Lightweight rule-based planner.

Phase 1 evolution: each step now carries `signal`, `risk_level`, `category`,
and `requires_user_decision` metadata so `RunManager` can ask the
InteractionPolicy whether the step needs UI, no UI, or text.

The planner remains deterministic. Future LLM-driven planners will produce
richer plans but MUST keep the same per-step metadata fields.
"""

from typing import Any

from tilo.models import Memory, Skill, Task
from tilo.services.artifact.spec import ArtifactTypeDetector


class Planner:
    def plan(self, task: Task, memories: list[Memory], skills: list[Skill]) -> dict[str, Any]:
        artifact_type = ArtifactTypeDetector().detect(task.input_message)
        risk_signal = self._risk_signal_for(artifact_type)

        steps: list[dict[str, Any]] = [
            {
                "type": "recall_memory",
                "description": f"Use {len(memories)} relevant confirmed memories.",
                "signal": "memory_recall",
                "risk_level": "low",
                "category": "memory",
                "requires_user_decision": False,
            },
            {
                "type": "select_skill",
                "description": f"Use {len(skills)} matching reusable skills.",
                "signal": "skill_selection",
                "risk_level": "low",
                "category": "skill",
                "requires_user_decision": False,
            },
            {
                "type": "invoke_tool",
                "description": "Use registered mock tools for external context.",
                "signal": "tool_invocation",
                "risk_level": "low",
                "category": "tool",
                "requires_user_decision": False,
            },
            {
                "type": "generate_artifact",
                "description": f"Generate a {artifact_type} artifact.",
                "signal": risk_signal,
                "risk_level": self._risk_level_for(artifact_type),
                "category": self._category_for(artifact_type),
                "requires_user_decision": artifact_type == "contract_review",
                "artifact_type": artifact_type,
            },
            {
                "type": "ask_confirmation",
                "description": "Create human decision items for high-risk actions.",
                "signal": "confirmation_request",
                "risk_level": "medium",
                "category": "confirmation",
                "requires_user_decision": True,
            },
            {
                "type": "extract_memory",
                "description": "Create unconfirmed memory candidates for future runs.",
                "signal": "user_preference_detected",
                "risk_level": "low",
                "category": "memory",
                "requires_user_decision": False,
            },
        ]

        return {
            "goal": task.title,
            "artifact_type": artifact_type,
            "selected_skill_ids": [skill.id for skill in skills],
            "steps": steps,
        }

    @staticmethod
    def _risk_signal_for(artifact_type: str) -> str:
        return {
            "contract_review": "contract_risk_review",
            "dashboard": "sales_followup_review",
            "table": "comparative_review",
        }.get(artifact_type, "result_ready")

    @staticmethod
    def _risk_level_for(artifact_type: str) -> str:
        return "high" if artifact_type == "contract_review" else "medium"

    @staticmethod
    def _category_for(artifact_type: str) -> str:
        return {
            "contract_review": "liability",
            "dashboard": "sales",
            "table": "competitive",
        }.get(artifact_type, "general")
