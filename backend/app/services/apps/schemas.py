from typing import Literal

from pydantic import BaseModel, Field


class AgentAppEntry(BaseModel):
    type: Literal["conversation"] = "conversation"
    default_prompt: str


class AgentAppRuntime(BaseModel):
    model: str = "default"
    deterministic_fallback: bool = True
    memory: Literal["enabled", "disabled"] = "enabled"
    interaction_policy: str


class AgentAppSurfaceConfig(BaseModel):
    mini: list[str] = Field(default_factory=list)
    rich: list[str] = Field(default_factory=list)


class AgentAppSampleInput(BaseModel):
    type: str
    name: str
    path: str
    resolved_path: str | None = None


class AgentAppToolConfig(BaseModel):
    name: str
    required: bool = False


class AgentAppManifest(BaseModel):
    id: str
    version: str
    name: str
    description: str
    entry: AgentAppEntry
    runtime: AgentAppRuntime
    surfaces: AgentAppSurfaceConfig = Field(default_factory=AgentAppSurfaceConfig)
    sample_inputs: list[AgentAppSampleInput] = Field(default_factory=list)
    tools: list[AgentAppToolConfig] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
