import { apiFetch } from "./api";
import type { SurfaceSpec, SurfaceTurn } from "./surface";

/**
 * Surface-protocol fetch helpers.
 *
 *   GET  /api/runs/{run_id}/surface-turns
 *   GET  /api/conversations/{session_id}/surface-turns
 *   POST /api/interactions
 *
 * Action semantics
 * ----------------
 * Every surface block click becomes a UIInteractionEvent on the backend
 * — that *is* the user's action stream, the foundation of ROAM's
 * Observe → Memorize loop. Surface block ids are NOT artifact block ids
 * (the SurfaceSpec is composed independently of the underlying Artifact),
 * so we never route through the artifact-action runtime here.
 *
 * Higher-level effects (e.g. "confirm a memory candidate") are layered
 * on top of the interaction event by the caller via the dedicated REST
 * endpoints (`/api/memories/{id}/confirm`).
 */

export async function fetchRunSurfaceTurns(runId: string): Promise<SurfaceTurn[]> {
  return apiFetch<SurfaceTurn[]>(`/api/runs/${runId}/surface-turns`);
}

export async function fetchSessionSurfaceTurns(
  sessionId: string,
  limit = 50,
): Promise<SurfaceTurn[]> {
  return apiFetch<SurfaceTurn[]>(
    `/api/conversations/${sessionId}/surface-turns?limit=${limit}`,
  );
}

// Backwards-compatible aliases.
export const listRunSurfaceTurns = fetchRunSurfaceTurns;
export const listSessionSurfaceTurns = fetchSessionSurfaceTurns;

export interface ExecuteSurfaceActionParams {
  /** The fully-validated SurfaceSpec the action belongs to. */
  surface: SurfaceSpec;
  /** Id of the action being fired (from `block.actions[*].id`). */
  actionId: string;
  /** The workspace this run belongs to (required to record the event). */
  workspaceId: string;
  sessionId?: string | null;
  runId?: string | null;
  /** Optional bound artifact id (for cross-reference, NOT for routing). */
  artifactId?: string | null;
  payload?: Record<string, unknown>;
}

export interface SurfaceActionResult {
  observation_id: string;
  status: "recorded";
  /** The action object that was fired, for downstream effects. */
  action: { id: string; action_type: string; payload?: Record<string, unknown> | null };
}

/**
 * Record a surface action click as an observable interaction event.
 *
 * The renderer always calls this; higher-level effects are invoked by
 * the caller after the event is persisted (see CoworkSurfaceDemo for
 * the memory-confirm example).
 */
export async function executeSurfaceAction(
  params: ExecuteSurfaceActionParams,
): Promise<SurfaceActionResult> {
  const { surface, actionId, workspaceId, sessionId, runId, artifactId, payload } = params;

  const owningBlock = surface.blocks.find((block) =>
    (block.actions ?? []).some((action) => action.id === actionId),
  );
  const action = owningBlock?.actions?.find((a) => a.id === actionId);
  const blockId = owningBlock?.id ?? null;

  const event = await apiFetch<{ id: string }>(`/api/interactions`, {
    method: "POST",
    body: JSON.stringify({
      workspace_id: workspaceId,
      session_id: sessionId ?? null,
      run_id: runId ?? null,
      artifact_id: artifactId ?? null,
      block_id: blockId,
      action_id: actionId,
      event_type: `surface.${surface.intent}.${action?.action_type ?? "click"}`,
      payload: {
        intent: surface.intent,
        surface_id: surface.surface_id,
        action_type: action?.action_type ?? null,
        operation: action?.action_type ?? null,
        ...(action?.payload ?? {}),
        ...(payload ?? {}),
      },
    }),
  });

  return {
    observation_id: event.id,
    status: "recorded",
    action: {
      id: actionId,
      action_type: action?.action_type ?? "unknown",
      payload: action?.payload ?? null,
    },
  };
}
