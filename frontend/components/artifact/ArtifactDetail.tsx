"use client";

import { useEffect, useState } from "react";
import { ArtifactRenderer, normalizeArtifactSpec } from "../ArtifactRenderer";
import { apiFetch } from "../../lib/api";
import type { Artifact } from "../../lib/types";

export function ArtifactDetail({ artifactId }: { artifactId: string }) {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void load();
  }, [artifactId]);

  async function load() {
    try {
      setArtifact(await apiFetch<Artifact>(`/api/artifacts/${artifactId}`));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load artifact");
    }
  }

  if (error) {
    return <div className="error-box">{error}</div>;
  }

  if (!artifact) {
    return <div className="artifact-placeholder">Loading artifact...</div>;
  }

  const schema = normalizeArtifactSpec(artifact.schema_json);
  const runId = schema.run_id || artifact.run_id;
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return (
    <div className="artifact-result-page">
      <header className="artifact-result-header">
        <div>
          <span className="eyebrow">Artifact Result · {schema.artifact_type}</span>
          <h1>{artifact.title}</h1>
          <p>Standalone ROAM result page with generated components, durable actions, linked run context, and memory references.</p>
        </div>
        <span className="status-pill">{schema.status}</span>
      </header>
      <div className="artifact-detail">
        <ArtifactRenderer artifact={artifact} />
        <aside className="artifact-meta">
          <h2>Version</h2>
          <span>v{artifact.version}</span>
          <h2>Actions</h2>
          <span>{schema.actions.length + schema.blocks.reduce((count, block) => count + (block.actions?.length || 0), 0)} available</span>
          <h2>Task</h2>
          <span>{artifact.task_id || "No linked task"}</span>
          <h2>Run</h2>
          <span>{runId || "No linked run"}</span>
          <h2>Trace</h2>
          {runId ? (
            <a className="small-link" href={`${apiBase}/api/runs/${runId}/trace`} target="_blank" rel="noreferrer">
              Open trace
            </a>
          ) : (
            <span>No trace link</span>
          )}
          <h2>Memory refs</h2>
          <span>{schema.memory_refs.length ? schema.memory_refs.join(", ") : "None"}</span>
          <h2>Provenance</h2>
          <span>{schema.provenance.length ? schema.provenance.map((item) => item.label || item.id).join(", ") : "None"}</span>
        </aside>
      </div>
    </div>
  );
}
