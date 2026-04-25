from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WorkspaceCreate(BaseModel):
    name: str
    description: str = ""
    owner_user_id: str | None = None


class WorkspaceRead(WorkspaceCreate, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    workspace_id: str
    name: str
    description: str = ""


class ProjectRead(ProjectCreate, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class AgentCreate(BaseModel):
    workspace_id: str
    name: str
    description: str = ""
    system_prompt: str = ""
    model: str = "gpt-4.1-mini"
    enabled_tool_ids: list[str] = Field(default_factory=list)
    enabled_skill_ids: list[str] = Field(default_factory=list)
    memory_scope: str = "workspace"


class AgentRead(AgentCreate, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    workspace_id: str
    project_id: str | None = None
    agent_id: str | None = None
    title: str | None = None
    input_message: str


class TaskRead(ORMModel):
    id: str
    workspace_id: str
    project_id: str | None
    agent_id: str | None
    title: str
    input_message: str
    status: str
    created_at: datetime
    updated_at: datetime


class RunRead(ORMModel):
    id: str
    task_id: str
    status: str
    plan_json: dict[str, Any] | None
    result_summary: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    workspace_id: str
    project_id: str | None = None
    agent_id: str | None = None
    content: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class MessageResponse(BaseModel):
    task_id: str
    run_id: str
    status: str


class MemoryCreate(BaseModel):
    workspace_id: str
    project_id: str | None = None
    user_id: str | None = None
    type: str = "task_experience"
    content: str
    source_type: str = "manual"
    source_id: str | None = None
    confidence: float = 0.75
    is_confirmed: bool = False
    expires_at: datetime | None = None
    embedding: list[float] | None = None


class MemoryRead(MemoryCreate, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class MemoryRecallRequest(BaseModel):
    workspace_id: str
    project_id: str | None = None
    type: str | None = None
    query: str
    limit: int = 5


class ArtifactCreate(BaseModel):
    workspace_id: str
    project_id: str | None = None
    task_id: str | None = None
    run_id: str | None = None
    type: str = "document"
    title: str
    schema_json: dict[str, Any]
    version: int = 1


class ArtifactRead(ArtifactCreate, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class ConfirmationRead(ORMModel):
    id: str
    workspace_id: str
    task_id: str | None
    run_id: str | None
    type: str
    title: str
    description: str
    payload_json: dict[str, Any]
    status: str
    decision_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ConfirmationApproveRequest(BaseModel):
    decision: dict[str, Any] = Field(default_factory=dict)


class ConfirmationRejectRequest(BaseModel):
    reason: str | None = None


class ConfirmationEditRequest(BaseModel):
    decision: dict[str, Any] = Field(default_factory=dict)
    edited_payload: dict[str, Any] = Field(default_factory=dict)


class SkillCreate(BaseModel):
    workspace_id: str
    name: str
    description: str = ""
    trigger_description: str = ""
    instructions_markdown: str = ""
    input_schema_json: dict[str, Any] = Field(default_factory=dict)
    output_schema_json: dict[str, Any] = Field(default_factory=dict)
    artifact_template_json: dict[str, Any] | None = None
    required_tool_ids: list[str] = Field(default_factory=list)
    version: int = 1


class SkillRead(SkillCreate, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class ToolCreate(BaseModel):
    workspace_id: str
    name: str
    type: str = "mock_search"
    description: str = ""
    config_json: dict[str, Any] = Field(default_factory=dict)
    permission_level: str = "low"


class ToolRead(ToolCreate, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class ToolInvokeRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class TraceStepRead(ORMModel):
    id: str
    run_id: str
    step_type: str
    title: str
    summary: str
    input_json: dict[str, Any] | None
    output_json: dict[str, Any] | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
