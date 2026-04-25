from typing import Any

from app.models import Memory, Skill, Task
from app.services.artifact.spec import ArtifactTypeDetector


class Planner:
    def plan(self, task: Task, memories: list[Memory], skills: list[Skill]) -> dict[str, Any]:
        artifact_type = ArtifactTypeDetector().detect(task.input_message)
        return {
            "goal": task.title,
            "artifact_type": artifact_type,
            "selected_skill_ids": [skill.id for skill in skills],
            "steps": [
                {"type": "recall_memory", "description": f"Use {len(memories)} relevant confirmed memories."},
                {"type": "select_skill", "description": f"Use {len(skills)} matching reusable skills."},
                {"type": "invoke_tool", "description": "Use registered mock tools for external context."},
                {"type": "generate_artifact", "description": f"Generate a {artifact_type} artifact."},
                {"type": "ask_confirmation", "description": "Create human decision items for high-risk actions."},
                {"type": "extract_memory", "description": "Create unconfirmed memory candidates for future runs."},
            ],
        }
