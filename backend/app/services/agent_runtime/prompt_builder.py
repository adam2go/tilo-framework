from app.models import Agent, Memory, Skill, Task, Tool, UIInteractionEvent


class PromptBuilder:
    def build(
        self,
        task: Task,
        agent: Agent | None,
        memories: list[Memory],
        skills: list[Skill],
        tools: list[Tool],
        recent_ui_observations: list[UIInteractionEvent] | None = None,
    ) -> dict:
        return {
            "system_prompt": agent.system_prompt if agent else "",
            "task": {"title": task.title, "input_message": task.input_message},
            "memories": [{"type": memory.type, "content": memory.content} for memory in memories],
            "recent_ui_observations": [
                {
                    "event_type": observation.event_type,
                    "artifact_id": observation.artifact_id,
                    "run_id": observation.run_id,
                    "payload": observation.payload_json,
                }
                for observation in (recent_ui_observations or [])
            ],
            "skills": [{"name": skill.name, "trigger": skill.trigger_description} for skill in skills],
            "tools": [{"name": tool.name, "type": tool.type, "permission_level": tool.permission_level} for tool in tools],
            "artifact_requirements": {"schema_driven": True},
        }
