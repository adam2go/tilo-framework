/**
 * Tilo Surface Protocol v1 — TypeScript types.
 *
 * Hand-aligned with `backend/app/schemas/surface.py` and the JSON Schema
 * exported at `frontend/lib/surface.schema.json`. The latter is the
 * machine-readable source of truth; this file mirrors it for ergonomic
 * use in TypeScript renderers. Drift is caught by the protocol round-trip
 * tests and the schema-export `--check` mode (see `scripts/export_surface_schema.py`).
 */

export const SURFACE_SCHEMA_VERSION = "tilo.surface.v1" as const;

export const NOOP_ACTION_ID = "__noop__" as const;

export type SurfaceIntent =
  | "request_approval"
  | "collect_input"
  | "present_result"
  | "offer_choices"
  | "confirm_memory"
  | "show_progress"
  | "escalate_to_rich"
  | "ask_clarification";

export type BudgetHint = "mini" | "rich";
export type BlockCompat = "graceful" | "strict";

export type Severity = "info" | "low" | "medium" | "high";

export type SurfaceBlockType =
  | "heading"
  | "text"
  | "evidence"
  | "comparison"
  | "decision"
  | "form"
  | "progress"
  | "list"
  | "link"
  | "editable"
  | "artifact_link"
  | "fallback";

// ---------- Block data shapes (mirror Pydantic models) -------------------- //

export interface HeadingData { text: string; severity?: Severity | null }
export interface TextData { content: string }
export interface EvidenceData { excerpt: string; source_ref: string; source_label?: string | null }

export interface ComparisonSide { label: string; value: string; severity?: Severity | null }
export interface ComparisonRow { label: string; left: string; right: string; severity?: Severity | null }
export interface ComparisonData {
  shape: "side_by_side" | "table";
  left?: ComparisonSide | null;
  right?: ComparisonSide | null;
  rows: ComparisonRow[];
}

export interface DecisionOption {
  id: string;
  label: string;
  value: string;
  action_id: string;
  severity?: Severity | null;
}
export interface DecisionData {
  prompt?: string | null;
  mode: "single" | "multi";
  options: DecisionOption[];
}

export type FormFieldKind = "text" | "number" | "textarea" | "select" | "toggle" | "date";
export interface FormFieldOption { label: string; value: string }
export interface FormField {
  name: string;
  label: string;
  kind: FormFieldKind;
  required: boolean;
  placeholder?: string | null;
  min?: number | null;
  max?: number | null;
  step?: number | null;
  options: FormFieldOption[];
  default?: unknown;
}
export interface FormData { fields: FormField[]; submit_action_id: string }

export type ProgressShape = "steps" | "percent" | "status";
export type ProgressState = "pending" | "running" | "done" | "failed" | "skipped";
export interface ProgressStep { id: string; label: string; state: ProgressState }
export interface ProgressData {
  shape: ProgressShape;
  percent?: number | null;
  status?: string | null;
  steps: ProgressStep[];
}

export interface ListItemData { text: string; severity?: Severity | null }
export interface ListData { ordered: boolean; items: ListItemData[] }

export type LinkTarget = "drawer" | "page" | "webview" | "external";
export interface LinkData { label: string; url: string; target: LinkTarget }

export type EditableKind = "rich_text" | "structured";
export interface EditableData {
  kind: EditableKind;
  value: string;
  schema?: Record<string, unknown> | null;
  submit_action_id: string;
  highlights: string[];
}

export interface ArtifactLinkData {
  artifact_id: string;
  title: string;
  summary?: string | null;
  open_action_id: string;
}

export interface FallbackData { content: string }

// ---------- Action contract (unchanged from artifact_spec.v1) ------------- //

export type SurfaceActionType =
  | "approve" | "reject" | "edit" | "select"
  | "continue_task" | "regenerate" | "invoke_tool"
  | "create_memory" | "promote_skill" | "export" | "confirm";

export interface SurfaceStateBinding {
  entity_type:
    | "artifact" | "confirmation" | "memory"
    | "skill_candidate" | "tool_invocation" | "task" | "run";
  entity_id: string;
  field?: string | null;
}

export interface SurfaceAction {
  id: string;
  label: string;
  action_type: SurfaceActionType;
  confirmation_required: boolean;
  confirmation_id?: string | null;
  payload?: Record<string, unknown>;
  state_binding?: SurfaceStateBinding | null;
}

// ---------- Block envelope ------------------------------------------------ //

interface BlockEnvelope<T extends SurfaceBlockType, D> {
  id: string;
  type: T;
  data: D;
  fallback_text: string;
  actions?: SurfaceAction[];
  state_binding?: SurfaceStateBinding | null;
}

export type SurfaceBlock =
  | BlockEnvelope<"heading", HeadingData>
  | BlockEnvelope<"text", TextData>
  | BlockEnvelope<"evidence", EvidenceData>
  | BlockEnvelope<"comparison", ComparisonData>
  | BlockEnvelope<"decision", DecisionData>
  | BlockEnvelope<"form", FormData>
  | BlockEnvelope<"progress", ProgressData>
  | BlockEnvelope<"list", ListData>
  | BlockEnvelope<"link", LinkData>
  | BlockEnvelope<"editable", EditableData>
  | BlockEnvelope<"artifact_link", ArtifactLinkData>
  | BlockEnvelope<"fallback", FallbackData>;

// ---------- Top-level SurfaceSpec ----------------------------------------- //

export interface ProvenanceRef { type: string; id: string; label?: string | null }

export interface SurfaceFallbacks {
  telegram?: { inline_keyboard: Array<Array<Record<string, unknown>>> };
  slack?: { blocks: Array<Record<string, unknown>> };
  email?: { html: string };
  [channel: string]: unknown;
}

export interface SurfaceSpec {
  schema_version: typeof SURFACE_SCHEMA_VERSION;
  surface_id: string;
  turn_id: string;
  run_id: string;

  intent: SurfaceIntent;
  budget_hint: BudgetHint;
  block_compat: BlockCompat;

  blocks: SurfaceBlock[];
  fallback_text: string;
  fallbacks?: SurfaceFallbacks | null;

  provenance: ProvenanceRef[];
  memory_refs: string[];
  metadata: Record<string, unknown>;
}

// ---------- Server-side row wrapping a SurfaceSpec ------------------------ //

export interface SurfaceTurn {
  id: string;
  run_id: string;
  session_id: string | null;
  workspace_id: string;
  project_id: string | null;
  ordinal: number;
  intent: SurfaceIntent;
  budget_hint: BudgetHint;
  status: string;
  surface_spec_json: SurfaceSpec;
  policy_decision_json: {
    step_index: number;
    decision: string;
    intent: string | null;
    surface: string | null;
    reason: string;
    rule_id: string | null;
  } | null;
  plan_step_index: number | null;
  plan_step_type: string | null;
  artifact_id: string | null;
  composer_mode: "deterministic" | "llm" | "deterministic_fallback" | string;
  created_at: string;
}
