from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agent, Skill, Task


class SkillSelector:
    def __init__(self, db: Session):
        self.db = db

    def select_for_task(self, task: Task, agent: Agent | None) -> list[Skill]:
        stmt = select(Skill).where(Skill.workspace_id == task.workspace_id)
        skills = list(self.db.scalars(stmt).all())
        if agent and agent.enabled_skill_ids:
            enabled = set(agent.enabled_skill_ids)
            skills = [skill for skill in skills if skill.id in enabled]

        query = task.input_message.lower()
        selected = [
            skill
            for skill in skills
            if any(
                text and text.lower() in query
                for text in (skill.name, skill.description, skill.trigger_description)
            )
        ]
        return selected or skills[:3]
