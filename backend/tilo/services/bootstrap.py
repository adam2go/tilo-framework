from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.core.config import get_settings
from tilo.models import Agent, Project, Skill, Tool, User, Workspace


def seed_defaults(db: Session) -> None:
    settings = get_settings()
    user = db.scalar(select(User).where(User.email == "demo@tilo.local"))
    if not user:
        user = User(email="demo@tilo.local", name="Demo User")
        db.add(user)
        db.commit()
        db.refresh(user)

    workspace = db.scalar(select(Workspace).where(Workspace.name == "Tilo Demo Workspace"))
    if not workspace:
        workspace = Workspace(owner_user_id=user.id, name="Tilo Demo Workspace", description="Default workspace for v0.1 demos.")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

    if not db.scalar(select(Project).where(Project.workspace_id == workspace.id)):
        db.add(Project(workspace_id=workspace.id, name="Demo Project", description="Run contract, sales, and competitive analysis demos."))
    if not db.scalar(select(Tool).where(Tool.workspace_id == workspace.id)):
        db.add(Tool(workspace_id=workspace.id, name="Mock Search", type="mock_search", description="Offline mock search provider.", permission_level="low"))

    agent = db.scalar(select(Agent).where(Agent.workspace_id == workspace.id))
    if not agent:
        agent = Agent(
            workspace_id=workspace.id,
            name="Tilo Agent",
            description="Memory-native artifact agent.",
            system_prompt="Create structured artifacts, ask for confirmations, and extract useful memory candidates.",
            model=settings.default_model,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)

    if not db.scalar(select(Skill).where(Skill.workspace_id == workspace.id)):
        db.add_all(
            [
                Skill(workspace_id=workspace.id, name="Contract Review", trigger_description="contract clause agreement nda", instructions_markdown="Identify risks and produce a contract_review artifact."),
                Skill(workspace_id=workspace.id, name="Sales Follow-up", trigger_description="sales customer crm follow up", instructions_markdown="Score customer opportunities and create confirmation items."),
                Skill(workspace_id=workspace.id, name="Competitive Analysis", trigger_description="competitor competitive market research", instructions_markdown="Create a comparison table and opportunity summary."),
            ]
        )
    db.commit()
