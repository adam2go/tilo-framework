import { apiFetch } from "./api";
import type { ArtifactActionExecutePayload, ArtifactActionResult } from "./types";

export async function executeArtifactAction({
  actionId,
  artifactId,
  blockId,
  idempotencyKey,
  payload = {},
  runId,
  sessionId,
  source = "web",
}: {
  artifactId: string;
  actionId: string;
  blockId?: string | null;
  sessionId?: string | null;
  runId?: string | null;
  source?: "web" | "telegram" | "api" | string;
  payload?: Record<string, unknown>;
  idempotencyKey?: string | null;
}) {
  const body: ArtifactActionExecutePayload = {
    block_id: blockId || null,
    session_id: sessionId || null,
    run_id: runId || null,
    source,
    payload,
    idempotency_key: idempotencyKey || null,
  };
  return apiFetch<ArtifactActionResult>(`/api/artifacts/${artifactId}/actions/${actionId}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
