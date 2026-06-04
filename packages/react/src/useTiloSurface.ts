"use client";

import { useCallback, useEffect, useState } from "react";
import type { SurfaceTurn } from "./surface";
import type { TiloClient } from "./client";

export interface UseTiloSurfaceOptions {
  client: TiloClient;
  runId?: string | null;
  sessionId?: string | null;
  /**
   * Polling interval in ms while the run is in progress.
   * Set to `0` (default) to disable polling — useful when the host app
   * already triggers a refresh after `sendMessage` returns.
   */
  pollingMs?: number;
  enabled?: boolean;
}

export interface UseTiloSurfaceResult {
  turns: SurfaceTurn[];
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

/**
 * Loads SurfaceTurns for a run or conversation session.
 *
 * @example
 * const client = createTiloClient({ baseUrl: "http://localhost:8000" });
 * const { turns, loading } = useTiloSurface({ client, runId });
 */
export function useTiloSurface({
  client,
  runId,
  sessionId,
  pollingMs = 0,
  enabled = true,
}: UseTiloSurfaceOptions): UseTiloSurfaceResult {
  const [turns, setTurns] = useState<SurfaceTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchTurns = useCallback(async () => {
    if (!enabled || (!runId && !sessionId)) return;
    setLoading(true);
    setError(null);
    try {
      if (runId) {
        setTurns(await client.fetchRunSurfaceTurns(runId));
      } else if (sessionId) {
        setTurns(await client.fetchSessionSurfaceTurns(sessionId));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [client, runId, sessionId, enabled]);

  useEffect(() => { void fetchTurns(); }, [fetchTurns]);

  useEffect(() => {
    if (!pollingMs || !enabled) return;
    const id = window.setInterval(() => void fetchTurns(), pollingMs);
    return () => window.clearInterval(id);
  }, [pollingMs, fetchTurns, enabled]);

  return { turns, loading, error, refresh: fetchTurns };
}
