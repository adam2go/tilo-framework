import type { ComponentType } from "react";
import type {
  ArtifactLinkData,
  ComparisonData,
  DecisionData,
  EditableData,
  EvidenceData,
  FallbackData,
  FormData,
  HeadingData,
  LinkData,
  ListData,
  ProgressData,
  SurfaceAction,
  SurfaceBlock,
  SurfaceBlockType,
  SurfaceSpec,
  TextData,
} from "../../lib/surface";

export type DataForBlock<T extends SurfaceBlockType> =
  T extends "heading" ? HeadingData :
  T extends "text" ? TextData :
  T extends "evidence" ? EvidenceData :
  T extends "comparison" ? ComparisonData :
  T extends "decision" ? DecisionData :
  T extends "form" ? FormData :
  T extends "progress" ? ProgressData :
  T extends "list" ? ListData :
  T extends "link" ? LinkData :
  T extends "editable" ? EditableData :
  T extends "artifact_link" ? ArtifactLinkData :
  T extends "fallback" ? FallbackData :
  never;

export interface BlockEnvelopeOf<T extends SurfaceBlockType> {
  id: string;
  type: T;
  data: DataForBlock<T>;
  fallback_text: string;
  actions?: SurfaceAction[];
  state_binding?: SurfaceBlock["state_binding"];
}

/**
 * Props passed to every block component (default or user override).
 *
 * `fire(actionId, payload?)` is the headless action dispatcher: invoke it
 * with one of `block.actions[].id` and the renderer routes through
 * `<TiloRenderer onAction>`. This keeps blocks visual-only.
 */
export interface BlockProps<T extends SurfaceBlockType> {
  block: BlockEnvelopeOf<T>;
  surface: SurfaceSpec;
  fire: (actionId: string, optionPayload?: Record<string, unknown>) => void | Promise<void>;
}

export type BlockComponent<T extends SurfaceBlockType> = ComponentType<BlockProps<T>>;

/**
 * Per-type override map accepted by `<TiloRenderer components={...}>`.
 * Pass any subset; unspecified types render with the built-in defaults.
 */
export type BlockOverrides = {
  [K in SurfaceBlockType]?: BlockComponent<K>;
};

/**
 * Event payload emitted by `<TiloRenderer onAction>`.
 */
export interface TiloAction {
  action: SurfaceAction;
  block: SurfaceBlock;
  surface: SurfaceSpec;
  payload?: Record<string, unknown>;
}
