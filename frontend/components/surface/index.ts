/**
 * Tilo Surface — reference React renderer for `tilo.surface.v1`.
 *
 * This is the **only** public entry point for the surface renderer. Internal
 * modules (`./blocks`, `./types`) are implementation details and may move.
 * Host apps that want a different renderer should consume `lib/surface.ts`
 * (types) + `lib/surfaceClient.ts` (fetch helpers) directly.
 */

export { TiloRenderer } from "./TiloRenderer";
export type { TiloRendererProps } from "./TiloRenderer";
export { useTiloSurface } from "./useTiloSurface";
export type { UseTiloSurfaceOptions, UseTiloSurfaceResult } from "./useTiloSurface";
export type { BlockComponent, BlockOverrides, BlockProps, TiloAction } from "./types";
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
