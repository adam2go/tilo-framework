from app.models import Agent, Memory, Skill, Task, Tool, UIInteractionEvent

MAX_PROMPT_TURNS = 12
MAX_PROMPT_OBSERVATIONS = 5
MAX_PROMPT_TURN_CHARS = 500


class PromptBuilder:
    def build(
        self,
        task: Task,
        agent: Agent | None,
        memories: list[Memory],
        skills: list[Skill],
        tools: list[Tool],
        recent_ui_observations: list[UIInteractionEvent] | None = None,
        recent_conversation_turns: list[dict] | None = None,
    ) -> dict:
        capped_turns = [self._compact_turn(turn) for turn in (recent_conversation_turns or [])[-MAX_PROMPT_TURNS:]]
        capped_observations = [
            {
                "event_type": observation.event_type,
                "artifact_id": observation.artifact_id,
                "run_id": observation.run_id,
                "payload": observation.payload_json,
            }
            for observation in (recent_ui_observations or [])[:MAX_PROMPT_OBSERVATIONS]
        ]
        return {
            "system_prompt": agent.system_prompt if agent else "",
            "task": {"title": task.title, "input_message": task.input_message},
            "memories": [{"type": memory.type, "content": memory.content} for memory in memories],
            "conversation_context": {
                "recent_turns": capped_turns,
                "recent_observations": capped_observations,
            },
            "recent_ui_observations": capped_observations,
            "recent_conversation_turns": capped_turns,
            "skills": [{"name": skill.name, "trigger": skill.trigger_description} for skill in skills],
            "tools": [{"name": tool.name, "type": tool.type, "permission_level": tool.permission_level} for tool in tools],
            "artifact_requirements": {"schema_driven": True},
        }

    def _compact_turn(self, turn: dict) -> dict:
        compact = {
            "turn_type": turn.get("turn_type"),
            "role": turn.get("role"),
            "content": self._truncate(turn.get("content")),
            "surface_type": turn.get("surface_type"),
            "artifact_id": turn.get("artifact_id"),
            "run_id": turn.get("run_id"),
            "interaction_id": turn.get("interaction_id"),
        }
        if turn.get("observation"):
            compact["observation"] = turn["observation"]
        return {key: value for key, value in compact.items() if value is not None}

    @staticmethod
    def _truncate(content) -> str | None:
        if content is None:
            return None
        text = str(content)
        if len(text) <= MAX_PROMPT_TURN_CHARS:
            return text
        return f"{text[:MAX_PROMPT_TURN_CHARS]}... [truncated {len(text) - MAX_PROMPT_TURN_CHARS} chars]"
