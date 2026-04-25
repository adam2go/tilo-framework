from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def new_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    owner_user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String, default="gpt-4.1-mini")
    enabled_tool_ids: Mapped[list] = mapped_column(JSON, default=list)
    enabled_skill_ids: Mapped[list] = mapped_column(JSON, default=list)
    memory_scope: Mapped[str] = mapped_column(String, default="workspace")


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey("workspaces.id"), index=True)
    project_id: Mapped[str | None] = mapped_column(String, ForeignKey("projects.id"), nullable=True, index=True)
    agent_id: Mapped[str | None] = mapped_column(String, ForeignKey("agents.id"), nullable=True)
    title: Mapped[str] = mapped_column(String)
    input_message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="created")


class Run(Base, TimestampMixin):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(String, ForeignKey("tasks.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="queued")
    plan_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Memory(Base, TimestampMixin):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey("workspaces.id"), index=True)
    project_id: Mapped[str | None] = mapped_column(String, ForeignKey("projects.id"), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    type: Mapped[str] = mapped_column(String, default="task_experience")
    content: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String, default="run")
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)


class Artifact(Base, TimestampMixin):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey("workspaces.id"), index=True)
    project_id: Mapped[str | None] = mapped_column(String, ForeignKey("projects.id"), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String, ForeignKey("tasks.id"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String, ForeignKey("runs.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String, default="document")
    title: Mapped[str] = mapped_column(String)
    schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(default=1)


class Confirmation(Base, TimestampMixin):
    __tablename__ = "confirmations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey("workspaces.id"), index=True)
    task_id: Mapped[str | None] = mapped_column(String, ForeignKey("tasks.id"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String, ForeignKey("runs.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String, default="approval")
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="pending")
    decision_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    trigger_description: Mapped[str] = mapped_column(Text, default="")
    instructions_markdown: Mapped[str] = mapped_column(Text, default="")
    input_schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    artifact_template_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required_tool_ids: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(default=1)


class Tool(Base, TimestampMixin):
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String, default="mock_search")
    description: Mapped[str] = mapped_column(Text, default="")
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    permission_level: Mapped[str] = mapped_column(String, default="low")


class TraceStep(Base):
    __tablename__ = "trace_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.id"), index=True)
    step_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text, default="")
    input_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String, default="completed")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
