/**
 * @tilo/react — React renderer SDK for Tilo Agent Interaction Protocol (AIP).
 *
 * Surface rendering:
 *   import { TiloRenderer } from "@tilo/react";
 *
 * Artifact block rendering:
 *   import { renderArtifactBlock, blockRenderers } from "@tilo/react";
 *
 * API client + hook:
 *   import { createTiloClient, useTiloSurface } from "@tilo/react";
 */

// Surface renderer
export { TiloRenderer } from "./TiloRenderer";
export type { TiloRendererProps } from "./TiloRenderer";

// Surface block components (for overrides)
export {
  ArtifactLinkBlock,
  ComparisonBlock,
  DecisionBlock,
  EditableBlock,
  EvidenceBlock,
  FallbackBlock,
  FormBlock,
  HeadingBlock,
  LinkBlock,
  ListBlock,
  ProgressBlock,
  TextBlock,
} from "./blocks";

// Artifact block rendering
export { renderArtifactBlock, blockRenderers } from "./blockRenderers";

// API client
export { createTiloClient } from "./client";
export type {
  TiloClient,
  TiloClientOptions,
  ExecuteSurfaceActionParams,
  SurfaceActionResult,
} from "./client";

// Hook
export { useTiloSurface } from "./useTiloSurface";
export type { UseTiloSurfaceOptions, UseTiloSurfaceResult } from "./useTiloSurface";

// Types — surface protocol
export type {
  SurfaceSpec,
  SurfaceBlock,
  SurfaceBlockType,
  SurfaceIntent,
  SurfaceTurn,
  SurfaceAction,
  BudgetHint,
  Severity,
  HeadingData,
  TextData,
  EvidenceData,
  ComparisonData,
  DecisionData,
  FormData,
  ProgressData,
  ListData,
  LinkData,
  EditableData,
  ArtifactLinkData,
  FallbackData,
} from "./surface";
export { NOOP_ACTION_ID, SURFACE_SCHEMA_VERSION } from "./surface";

// Types — block overrides
export type {
  BlockProps,
  BlockComponent,
  BlockOverrides,
  TiloAction,
} from "./block-types";

// Types — artifact
export type {
  ArtifactBlock,
  ArtifactAction,
  ArtifactActionType,
  ArtifactSpec,
  ArtifactView,
  StateBinding,
} from "./artifact-types";
export { blockData } from "./artifact-types";
