/**
 * Tilo API client for @tilo/react.
 *
 * All functions accept a `baseUrl` so the package works with any Tilo
 * backend deployment, not just localhost.
 *
 * @example
 * const client = createTiloClient("http://localhost:8000");
 * const turns = await client.fetchRunSurfaceTurns(runId);
 */

import type { SurfaceSpec, SurfaceTurn } from "./surface";

export interface TiloClientOptions {
  /** Base URL of the Tilo backend, e.g. "http://localhost:8000" */
  baseUrl: string;
  /** Optional fetch override (for testing or custom auth headers). */
  fetcher?: typeof fetch;
}

async function apiFetch<T>(baseUrl: string, path: string, init?: RequestInit, fetcher = fetch): Promise<T> {
  const url = `${baseUrl.replace(/\/$/, "")}${path}`;
  const res = await fetcher(url, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`Tilo API ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export interface TiloClient {
  fetchRunSurfaceTurns(runId: string): Promise<SurfaceTurn[]>;
  fetchSessionSurfaceTurns(sessionId: string, limit?: number): Promise<SurfaceTurn[]>;
  executeSurfaceAction(params: ExecuteSurfaceActionParams): Promise<SurfaceActionResult>;
}

export interface ExecuteSurfaceActionParams {
  surface: SurfaceSpec;
  actionId: string;
  workspaceId: string;
  sessionId?: string | null;
  runId?: string | null;
  artifactId?: string | null;
  payload?: Record<string, unknown>;
}

export interface SurfaceActionResult {
  observation_id: string;
  status: "recorded";
  action: { id: string; action_type: string; payload?: Record<string, unknown> | null };
}

export function createTiloClient({ baseUrl, fetcher = fetch }: TiloClientOptions): TiloClient {
  const get = <T>(path: string) => apiFetch<T>(baseUrl, path, undefined, fetcher);
  const post = <T>(path: string, body: unknown) =>
    apiFetch<T>(baseUrl, path, { method: "POST", body: JSON.stringify(body) }, fetcher);

  return {
    fetchRunSurfaceTurns: (runId) => get<SurfaceTurn[]>(`/api/runs/${runId}/surface-turns`),
    fetchSessionSurfaceTurns: (sessionId, limit = 50) =>
      get<SurfaceTurn[]>(`/api/conversations/${sessionId}/surface-turns?limit=${limit}`),

    async executeSurfaceAction({ surface, actionId, workspaceId, sessionId, runId, artifactId, payload }) {
      const owningBlock = surface.blocks.find((b) => (b.actions ?? []).some((a) => a.id === actionId));
      const action = owningBlock?.actions?.find((a) => a.id === actionId);
      const event = await post<{ id: string }>("/api/interactions", {
        workspace_id: workspaceId,
        session_id: sessionId ?? null,
        run_id: runId ?? null,
        artifact_id: artifactId ?? null,
        block_id: owningBlock?.id ?? null,
        action_id: actionId,
        event_type: `surface.${surface.intent}.${action?.action_type ?? "click"}`,
        payload: {
          intent: surface.intent,
          surface_id: surface.surface_id,
          action_type: action?.action_type ?? null,
          ...(action?.payload ?? {}),
          ...(payload ?? {}),
        },
      });
      return {
        observation_id: event.id,
        status: "recorded" as const,
        action: { id: actionId, action_type: action?.action_type ?? "unknown", payload: action?.payload ?? null },
      };
    },
  };
}
