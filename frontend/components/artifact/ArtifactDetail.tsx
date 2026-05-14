"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import type { Artifact } from "../../lib/types";

/**
 * Minimal artifact detail page. The Surface Protocol refactor replaced
 * the per-artifact custom renderer; this page now reads the underlying
 * metadata and links back to the SurfaceTurn stream that referenced
 * this artifact, plus the raw run trace.
 *
 * For the v0.1 product loop the canonical UI lives at /demo via the
 * cowork SurfaceTurn renderer. This route exists for ops/debug.
 */
export function ArtifactDetail({
  artifactId,
}: {
  artifactId: string;
  channel?: string;
  sessionId?: string | null;
}) {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void load();
    async function load() {
      try {
        setArtifact(await apiFetch<Artifact>(`/api/artifacts/${artifactId}`));
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load artifact");
      }
    }
  }, [artifactId]);

  if (error) {
    return <div className="error-box">{error}</div>;
  }

  if (!artifact) {
    return <div className="artifact-placeholder">Loading artifact...</div>;
  }

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const runId = artifact.run_id;
  const schemaJson = artifact.schema_json as { artifact_type?: string; status?: string };

  return (
    <div className="artifact-result-page" style={{ padding: 32, maxWidth: 880, margin: "0 auto" }}>
      <header className="artifact-result-header" style={{ marginBottom: 24 }}>
        <span className="eyebrow" style={{ color: "#707987", fontSize: 12, textTransform: "uppercase" }}>
          Artifact · {schemaJson.artifact_type ?? "unknown"}
        </span>
        <h1 style={{ margin: "6px 0 8px", fontSize: 26 }}>{artifact.title}</h1>
        <p style={{ color: "#3c4250" }}>
          The user-facing surfaces for this artifact live in the SurfaceTurn stream.
          This page is for inspection.
        </p>
      </header>

      <section style={{ display: "grid", gap: 12, gridTemplateColumns: "120px 1fr", color: "#171a1f" }}>
        <strong>Status</strong>
        <span>{schemaJson.status ?? "unknown"}</span>
        <strong>Version</strong>
        <span>v{artifact.version}</span>
        <strong>Task</strong>
        <span>{artifact.task_id || "No linked task"}</span>
        <strong>Run</strong>
        <span>
          {runId ? (
            <Link href={`${apiBase}/api/runs/${runId}/surface-turns`} target="_blank">
              {runId} · view surface turns ↗
            </Link>
          ) : (
            "No linked run"
          )}
        </span>
        <strong>Trace</strong>
        <span>
          {runId ? (
            <Link href={`${apiBase}/api/runs/${runId}/trace`} target="_blank">
              Open trace ↗
            </Link>
          ) : (
            "No trace link"
          )}
        </span>
      </section>

      <details style={{ marginTop: 24 }}>
        <summary style={{ cursor: "pointer", color: "#707987" }}>Raw artifact JSON</summary>
        <pre style={{
          background: "#f7f7f5",
          padding: 16,
          borderRadius: 8,
          overflow: "auto",
          fontSize: 12,
          marginTop: 8,
        }}>
          {JSON.stringify(artifact, null, 2)}
        </pre>
      </details>
    </div>
  );
}
