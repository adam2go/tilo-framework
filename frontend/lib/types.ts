export type Workspace = { id: string; name: string; description: string };
export type Project = { id: string; workspace_id: string; name: string; description: string };
export type Agent = { id: string; workspace_id: string; name: string; description: string };
export type Run = { id: string; task_id: string; status: string; result_summary?: string | null };
export type Task = { id: string; title: string; input_message: string; status: string };

export type ArtifactBlock = {
  id: string;
  type: string;
  data: Record<string, unknown>;
};

export type ArtifactSchema = {
  artifact_type: string;
  title: string;
  blocks: ArtifactBlock[];
};

export type Artifact = {
  id: string;
  type: string;
  title: string;
  schema_json: ArtifactSchema;
  created_at: string;
};

export type Confirmation = {
  id: string;
  title: string;
  description: string;
  status: string;
  payload_json: Record<string, unknown>;
};

export type Memory = {
  id: string;
  type: string;
  content: string;
  confidence: number;
  is_confirmed: boolean;
  created_at: string;
};

export type TraceStep = {
  id: string;
  step_type: string;
  title: string;
  summary: string;
  status: string;
};

export type Skill = {
  id: string;
  workspace_id: string;
  name: string;
  description: string;
  trigger_description: string;
  version: number;
};
