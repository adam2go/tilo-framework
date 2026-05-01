export type Workspace = { id: string; name: string; description: string };
export type Project = { id: string; workspace_id: string; name: string; description: string };
export type Agent = { id: string; workspace_id: string; name: string; description: string };
export type Run = { id: string; task_id: string; status: string; result_summary?: string | null };
export type RunMetrics = {
  id: string;
  run_id: string;
  workspace_id: string;
  success: boolean;
  latency_ms: number;
  artifact_count: number;
  confirmation_count: number;
  memory_candidate_count: number;
  tool_call_count: number;
  error_count: number;
  user_feedback_score?: number | null;
  created_at: string;
};
export type Task = { id: string; title: string; input_message: string; status: string };

export type ArtifactActionType =
  | "approve"
  | "reject"
  | "edit"
  | "select"
  | "continue_task"
  | "regenerate"
  | "invoke_tool"
  | "create_memory"
  | "promote_skill"
  | "export"
  | "confirm";

export type StateBinding = {
  entity_type: "artifact" | "confirmation" | "memory" | "skill_candidate" | "tool_invocation" | "task" | "run";
  entity_id: string;
  field?: string | null;
};

export type ArtifactBlock = {
  id: string;
  type: string;
  title?: string | null;
  data: Record<string, unknown>;
  actions?: ArtifactAction[];
  state_binding?: StateBinding | null;
};

export type ArtifactAction = {
  id: string;
  label: string;
  action_type: ArtifactActionType;
  confirmation_required: boolean;
  confirmation_id?: string | null;
  payload?: Record<string, unknown>;
  state_binding?: StateBinding | null;
};

export type ProvenanceRef = {
  type: string;
  id: string;
  label?: string | null;
};

export type ArtifactSpecV1 = {
  version: "artifact_spec.v1";
  artifact_type: string;
  title: string;
  status: "draft" | "streaming" | "ready" | "failed";
  blocks: ArtifactBlock[];
  actions: ArtifactAction[];
  provenance: ProvenanceRef[];
  memory_refs: string[];
  run_id?: string | null;
};

export type Artifact = {
  id: string;
  workspace_id: string;
  project_id?: string | null;
  task_id?: string | null;
  run_id?: string | null;
  type: string;
  title: string;
  schema_json: ArtifactSpecV1;
  version: number;
  created_at: string;
  updated_at: string;
};

export type Confirmation = {
  id: string;
  workspace_id: string;
  task_id?: string | null;
  run_id?: string | null;
  type: string;
  title: string;
  description: string;
  status: string;
  payload_json: Record<string, unknown>;
  decision_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type Memory = {
  id: string;
  workspace_id: string;
  project_id?: string | null;
  scope_type: string;
  scope_id?: string | null;
  type: string;
  content: string;
  confidence: number;
  salience: number;
  status: "candidate" | "confirmed" | "rejected" | "archived" | string;
  is_confirmed: boolean;
  source_run_id?: string | null;
  source_id?: string | null;
  structured_payload?: Record<string, unknown> | null;
  last_recalled_at?: string | null;
  recall_count: number;
  created_at: string;
};

export type TraceStep = {
  id: string;
  step_type: string;
  title: string;
  summary: string;
  input_json?: Record<string, unknown> | null;
  output_json?: Record<string, unknown> | null;
  status: string;
};

export type Skill = {
  id: string;
  workspace_id: string;
  name: string;
  description: string;
  trigger_description: string;
  instructions_markdown?: string;
  version: number;
};

export type Feedback = {
  id: string;
  workspace_id: string;
  project_id?: string | null;
  run_id?: string | null;
  artifact_id?: string | null;
  memory_id?: string | null;
  skill_id?: string | null;
  rating?: number | null;
  feedback_text?: string | null;
  feedback_type: string;
  created_at: string;
};

export type SkillCandidate = {
  id: string;
  workspace_id: string;
  project_id?: string | null;
  source_run_id: string;
  name: string;
  description: string;
  trigger_description: string;
  instructions_markdown: string;
  artifact_template_json?: Record<string, unknown> | null;
  status: "pending_review" | "approved" | "rejected" | "promoted" | string;
  eval_report_json?: Record<string, unknown> | null;
  promoted_skill_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type UIInteractionEvent = {
  id: string;
  workspace_id: string;
  project_id?: string | null;
  user_id?: string | null;
  artifact_id?: string | null;
  block_id?: string | null;
  action_id?: string | null;
  run_id?: string | null;
  event_type: string;
  payload_json: Record<string, unknown>;
  created_at: string;
};

export type RuntimeCapabilities = {
  llm_enabled: boolean;
  llm_configured: boolean;
  llm_runtime_mode: "llm" | "deterministic" | string;
  llm_provider: string;
  llm_provider_family: string;
  llm_supported_providers: string[];
  default_model: string;
  telegram_enabled: boolean;
  public_app_url: string;
};

export type AgentAppManifest = {
  id: string;
  version: string;
  name: string;
  description: string;
  entry: {
    type: "conversation";
    default_prompt: string;
  };
  runtime: {
    model: string;
    deterministic_fallback: boolean;
    memory: "enabled" | "disabled";
    interaction_policy: string;
  };
  surfaces: {
    mini: string[];
    rich: string[];
  };
  sample_inputs: Array<{
    type: string;
    name: string;
    path: string;
    resolved_path?: string | null;
  }>;
  tools: Array<{
    name: string;
    required: boolean;
  }>;
  channels: string[];
};
