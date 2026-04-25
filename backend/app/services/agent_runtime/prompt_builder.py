from app.models import Agent, Memory, Skill, Task, Tool


class PromptBuilder:
    def build(
        self,
        task: Task,
        agent: Agent | None,
        memories: list[Memory],
        skills: list[Skill],
        tools: list[Tool],
    ) -> dict:
        return {
            "system_prompt": agent.system_prompt if agent else "",
            "task": {"title": task.title, "input_message": task.input_message},
            "memories": [{"type": memory.type, "content": memory.content} for memory in memories],
            "skills": [{"name": skill.name, "trigger": skill.trigger_description} for skill in skills],
            "tools": [{"name": tool.name, "type": tool.type, "permission_level": tool.permission_level} for tool in tools],
            "artifact_requirements": {"schema_driven": True},
        }
