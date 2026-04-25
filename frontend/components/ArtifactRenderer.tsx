"use client";

import type { Artifact, ArtifactSpecV1 } from "../lib/types";
import { renderArtifactBlock } from "./artifact/blockRenderers";

export function ArtifactRenderer({ artifact }: { artifact: Artifact | null }) {
  if (!artifact) {
    return <div className="artifact-placeholder">Send a message to generate an artifact.</div>;
  }
  const schema = normalizeArtifactSpec(artifact.schema_json);
  return (
    <article className="artifact">
      <ArtifactHeader artifact={artifact} schema={schema} />
      <ArtifactSchemaRenderer schema={schema} />
      <ArtifactActions schema={schema} />
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
      <span className="status-pill">{schema.status}</span>
    </header>
  );
}

export function ArtifactSchemaRenderer({ schema }: { schema: ArtifactSpecV1 }) {
  return (
    <div className="artifact-blocks">
      {schema.blocks.map((block) => (
        <div key={block.id}>{renderArtifactBlock(block)}</div>
      ))}
    </div>
  );
}

function ArtifactActions({ schema }: { schema: ArtifactSpecV1 }) {
  const actions = schema.actions || [];
  if (!actions.length) {
    return null;
  }
  return (
    <section className="artifact-actions">
      {actions.map((action) => (
        <div className="artifact-action" key={action.id}>
          <strong>{action.label}</strong>
          <span>{action.confirmation_required ? `Confirmation ${action.confirmation_id ? "linked" : "required"}` : action.action_type}</span>
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
