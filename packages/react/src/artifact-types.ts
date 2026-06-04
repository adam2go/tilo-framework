/**
 * Artifact (AIP v1) TypeScript types for @tilo/react.
 * Mirrors backend/tilo/schemas/artifact.py.
 */

export type ArtifactActionType =
  | "approve" | "reject" | "edit" | "select" | "continue_task"
  | "regenerate" | "invoke_tool" | "create_memory" | "promote_skill"
  | "export" | "confirm";

export type StateBinding = {
  entity_type: "artifact" | "confirmation" | "memory" | "skill_candidate" | "tool_invocation" | "task" | "run";
  entity_id: string;
  field?: string | null;
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

export type ArtifactBlock = {
  id: string;
  type: string;
  title?: string | null;
  /** AIP v1 uses `props`; v0.x used `data`. Both are supported. */
  props?: Record<string, unknown>;
  data?: Record<string, unknown>;
  actions?: ArtifactAction[];
  state_binding?: StateBinding | null;
};

/** Resolve block data — prefers `props` (AIP v1), falls back to `data` (v0.x). */
export function blockData(block: ArtifactBlock): Record<string, unknown> {
  return block.props ?? block.data ?? {};
}

export type ArtifactView = {
  id: string;
  label: string;
  icon?: string | null;
  description?: string | null;
  layout?: string | null;
  block_ids: string[];
  renderer?: string | null;
};

export type ArtifactSpec = {
  version: string;
  artifact_type?: string | null;
  title: string;
  status: string;
  blocks: ArtifactBlock[];
  actions?: ArtifactAction[];
  views?: ArtifactView[];
  follow_ups?: string[];
  run_id?: string | null;
};
