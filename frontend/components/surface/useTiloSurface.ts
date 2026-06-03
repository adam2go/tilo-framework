"use client";

import { useCallback, useEffect, useState } from "react";
import { listRunSurfaceTurns, listSessionSurfaceTurns } from "../../lib/surfaceClient";
import type { SurfaceTurn } from "../../lib/surface";

export interface UseTiloSurfaceOptions {
  runId?: string | null;
  sessionId?: string | null;
  /**
   * Polling interval in ms, used while the run looks "in progress". Set to
   * `0` to disable polling — useful when the host app already drives a
   * refresh after `sendConversationMessage` returns.
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
 * Hook that loads the SurfaceTurn stream for either a run or a conversation
 * session.
 *
 * - When `runId` is provided, loads turns for just that run.
 * - When `sessionId` is provided (and `runId` is not), loads the full
 *   timeline for that conversation, oldest first.
 *
 * No SSE in v1; a future Phase will add `/api/runs/{id}/events` for
 * push-based streaming. For now polling is opt-in and bounded.
 */
export function useTiloSurface(options: UseTiloSurfaceOptions): UseTiloSurfaceResult {
  const { runId, sessionId, pollingMs = 0, enabled = true } = options;
  const [turns, setTurns] = useState<SurfaceTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchTurns = useCallback(async () => {
    if (!enabled) return;
    if (!runId && !sessionId) return;
    setLoading(true);
    setError(null);
    try {
      if (runId) {
        setTurns(await listRunSurfaceTurns(runId));
      } else if (sessionId) {
        setTurns(await listSessionSurfaceTurns(sessionId));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [runId, sessionId, enabled]);

  useEffect(() => {
    void fetchTurns();
  }, [fetchTurns]);

  useEffect(() => {
    if (!pollingMs || !enabled) return;
    const interval = window.setInterval(() => void fetchTurns(), pollingMs);
    return () => window.clearInterval(interval);
  }, [pollingMs, fetchTurns, enabled]);

  return { turns, loading, error, refresh: fetchTurns };
}
