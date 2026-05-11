"use client";

import Link from "next/link";
import { ArtifactRenderer } from "../ArtifactRenderer";
import { RoamStatusStrip } from "./RoamStatusStrip";
import type { Artifact, ArtifactBlock } from "../../lib/types";

const contractOrder = [
  { id: "contract_input", title: "Contract Input", description: "Goal captured and task created.", stage: "Render" },
  { id: "risk_review", title: "Risk Review", description: "Clause-level risks are rendered as actionable review nodes.", stage: "Render" },
  { id: "human_approval", title: "Human Approval", description: "Decision is confirmation-gated and traceable.", stage: "Observe" },
  { id: "revision_draft", title: "Revision Draft", description: "Agent prepares a structured revision preview.", stage: "Act" },
  { id: "memory_update", title: "Memory Update", description: "Preference can become reviewable long-term memory.", stage: "Memorize" },
  { id: "next_action", title: "Next Action", description: "Queue follow-up workflow actions.", stage: "Act" },
];

function statusForNode(index: number, artifact: Artifact | null) {
  if (!artifact) return index === 0 ? "active" : "idle";
  if (index < 2) return "completed";
  if (index === 2) return "pending";
  if (index === 3) return "active";
  return "idle";
}

function blocksByType(blocks: ArtifactBlock[]) {
  return new Set(blocks.map((block) => block.type));
}

export function WorkflowSurface({ artifact, sessionId = null }: { artifact: Artifact | null; sessionId?: string | null }) {
  const blockTypes = blocksByType(artifact?.schema_json.blocks || []);
  return (
    <section className="workflow-surface">
      <header className="workflow-surface-header">
        <div>
          <span className="eyebrow">Generated SaaS Workflow Surface</span>
          <h2>{artifact?.title || "Contract Review ROAM Demo"}</h2>
          <p>
            A sequential workflow where rendered components produce durable observations, trigger safe actions, and create reviewable memory.
          </p>
        </div>
        {artifact ? (
          <Link className="secondary-link" href={`/artifacts/${artifact.id}`}>
            Open result page
          </Link>
        ) : null}
      </header>

      <RoamStatusStrip activeIndex={artifact ? 2 : 0} />

      <div className="workflow-stepper">
        {contractOrder.map((node, index) => (
          <article className={`workflow-node ${statusForNode(index, artifact)}`} key={node.id}>
            <span>{index + 1}</span>
            <div>
              <strong>{node.title}</strong>
              <small>{node.stage}</small>
              <p>{node.description}</p>
            </div>
          </article>
        ))}
      </div>

      {artifact ? (
        <ArtifactRenderer artifact={artifact} sessionId={sessionId} />
      ) : (
        <div className="workflow-placeholder">
          <strong>Run the Contract Review demo to render the workflow.</strong>
          <span>Expected components: RiskSummary, RiskReviewPanel, ApprovalCard, EditableDocumentPreview, MemoryCandidateCard, ActionQueue.</span>
        </div>
      )}

      {artifact && !blockTypes.has("risk_summary") ? (
        <div className="workflow-placeholder">
          <strong>Legacy artifact detected</strong>
          <span>Run the Contract Review demo again to generate the full ROAM workflow blocks.</span>
        </div>
      ) : null}
    </section>
  );
}
