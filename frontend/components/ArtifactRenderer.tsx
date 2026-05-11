"use client";

import Link from "next/link";
import { useState } from "react";
import { executeArtifactAction } from "../lib/artifactActions";
import type { Artifact, ArtifactSpecV1 } from "../lib/types";
import { renderArtifactBlock } from "./artifact/blockRenderers";
import { renderInteractionComponent } from "./interaction/registry";

type ArtifactRendererProps = {
  artifact: Artifact | null;
  sessionId?: string | null;
};

export function ArtifactRenderer({ artifact, sessionId = null }: ArtifactRendererProps) {
  if (!artifact) {
    return <div className="artifact-placeholder">Send a message to generate an artifact.</div>;
  }
  const schema = normalizeArtifactSpec(artifact.schema_json);
  return (
    <article className="artifact">
      <ArtifactHeader artifact={artifact} schema={schema} />
      <ArtifactSchemaRenderer artifact={artifact} schema={schema} sessionId={sessionId} />
      <ArtifactActions artifact={artifact} schema={schema} sessionId={sessionId} />
    </article>
  );
}

function ArtifactHeader({ artifact, schema }: { artifact: Artifact; schema: ArtifactSpecV1 }) {
  return (
    <header className="section-header">
      <div>
        <span className="eyebrow">{schema.artifact_type}</span>
        <h2>{artifact.title}</h2>
      </div>
      <div className="artifact-header-actions">
        <Link className="small-link" href={`/artifacts/${artifact.id}`}>
          Open
        </Link>
        <span className="status-pill">{schema.status}</span>
      </div>
    </header>
  );
}

export function ArtifactSchemaRenderer({ artifact, schema, sessionId = null }: { artifact: Artifact; schema: ArtifactSpecV1; sessionId?: string | null }) {
  return (
    <div className="artifact-blocks">
      {schema.blocks.map((block) => (
        <div key={block.id}>{renderInteractionComponent(artifact, block, { sessionId }) || renderArtifactBlock(block)}</div>
      ))}
    </div>
  );
}

function ArtifactActions({ artifact, schema, sessionId = null }: { artifact: Artifact; schema: ArtifactSpecV1; sessionId?: string | null }) {
  const [statusByAction, setStatusByAction] = useState<Record<string, string>>({});
  const actions = schema.actions || [];
  if (!actions.length) {
    return null;
  }
  async function handleAction(actionId: string) {
    setStatusByAction((current) => ({ ...current, [actionId]: "Running action" }));
    try {
      const result = await executeArtifactAction({
        artifactId: artifact.id,
        actionId,
        sessionId: sessionId || null,
        runId: schema.run_id || artifact.run_id || null,
        source: "web",
        payload: {},
      });
      setStatusByAction((current) => ({ ...current, [actionId]: `${result.status}: ${result.message}` }));
    } catch (err) {
      setStatusByAction((current) => ({ ...current, [actionId]: err instanceof Error ? err.message : "Action failed" }));
    }
  }
  return (
    <section className="artifact-actions">
      {actions.map((action) => (
        <div className="artifact-action" key={action.id}>
          <strong>{action.label}</strong>
          <span>{action.confirmation_required ? `Confirmation ${action.confirmation_id ? "linked" : "required"}` : action.action_type}</span>
          <button className="small-button" onClick={() => void handleAction(action.id)} type="button">
            Run
          </button>
          {statusByAction[action.id] ? <small>{statusByAction[action.id]}</small> : null}
        </div>
      ))}
    </section>
  );
}

export function normalizeArtifactSpec(schema: ArtifactSpecV1): ArtifactSpecV1 {
  return {
    ...schema,
    version: "artifact_spec.v1",
    status: schema.status || "ready",
    actions: schema.actions || [],
    provenance: schema.provenance || [],
    memory_refs: schema.memory_refs || [],
    run_id: schema.run_id || null
  };
}
