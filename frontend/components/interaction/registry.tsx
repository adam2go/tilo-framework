"use client";

import { useState } from "react";
import { AlertTriangle, Check, Clock, Database, FilePenLine, Gauge, Play, ShieldAlert, Sparkles, X } from "lucide-react";
import { executeArtifactAction } from "../../lib/artifactActions";
import type { Artifact, ArtifactAction, ArtifactBlock, ArtifactActionResult } from "../../lib/types";

type InteractionProps = {
  artifact: Artifact;
  block: ArtifactBlock;
};

type InteractionComponent = (props: InteractionProps) => JSX.Element;

function ActionButtons({ artifact, block }: InteractionProps) {
  const [status, setStatus] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<ArtifactActionResult | null>(null);
  const actions = block.actions || [];
  if (!actions.length) return null;

  async function handleAction(action: ArtifactAction) {
    setStatus("Running action");
    try {
      const result = await runArtifactAction(artifact, block, action, {});
      setLastResult(result);
      setStatus(`${result.status}: ${result.message}`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Action failed");
    }
  }

  return (
    <div className="interaction-actions">
      {actions.map((action) => (
        <button className="small-button" key={action.id} onClick={() => void handleAction(action)}>
          {action.action_type === "reject" ? <X size={14} /> : <Check size={14} />}
          {action.label}
        </button>
      ))}
      {status ? <span className="interaction-status">{status}</span> : null}
      {lastResult?.warnings.length ? <small>{lastResult.warnings.join(" ")}</small> : null}
    </div>
  );
}

async function runArtifactAction(artifact: Artifact, block: ArtifactBlock, action: ArtifactAction, payload: Record<string, unknown>) {
  return executeArtifactAction({
    artifactId: artifact.id,
    actionId: action.id,
    blockId: block.id,
    runId: artifact.run_id || null,
    payload: {
      artifact_type: artifact.type,
      block_type: block.type,
      action_type: action.action_type,
      ...payload,
    },
  });
}

export function ApprovalCard({ artifact, block }: InteractionProps) {
  return (
    <section className="interaction-card approval-card">
      <div className="interaction-title-row">
        <ShieldAlert size={18} />
        <div>
          <strong>{String(block.data.title || block.title || "Approval")}</strong>
          <span>{String(block.data.risk_level || "review")}</span>
        </div>
      </div>
      <p>{String(block.data.content || block.data.description || "")}</p>
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export function RiskSummary({ artifact, block }: InteractionProps) {
  const high = Number(block.data.high_count || 0);
  const medium = Number(block.data.medium_count || 0);
  const low = Number(block.data.low_count || 0);
  return (
    <section className="interaction-card risk-summary-card">
      <div className="interaction-title-row">
        <AlertTriangle size={18} />
        <div>
          <strong>{block.title || "Risk Summary"}</strong>
          <span>{String(block.data.status || "review_ready")} · confidence {String(block.data.confidence || "0.8")}</span>
        </div>
      </div>
      <div className="risk-summary-grid">
        <div className="risk-summary-metric high">
          <strong>{high}</strong>
          <span>High</span>
        </div>
        <div className="risk-summary-metric medium">
          <strong>{medium}</strong>
          <span>Medium</span>
        </div>
        <div className="risk-summary-metric low">
          <strong>{low}</strong>
          <span>Low</span>
        </div>
      </div>
      <p>{String(block.data.summary || "")}</p>
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export function RiskReviewPanel({ artifact, block }: InteractionProps) {
  const [riskStatus, setRiskStatus] = useState<Record<string, string>>({});
  const risks = (block.data.risks as Array<Record<string, unknown>>) || [];

  async function decideRisk(risk: Record<string, unknown>, actionType: "approve" | "edit" | "reject") {
    const riskId = String(risk.id || risk.clause || "risk");
    setRiskStatus((current) => ({ ...current, [riskId]: "Running action" }));
    try {
      const fallbackActionId = actionType === "approve" ? "accept_risks" : "revise_risks";
      const action = (block.actions || []).find((item) => item.id === fallbackActionId) || (block.actions || [])[0];
      if (!action) throw new Error("No artifact action is available for this risk.");
      const result = await runArtifactAction(artifact, block, action, {
        risk_id: riskId,
        risk_decision: actionType,
        clause: risk.clause,
        risk_level: risk.risk_level,
      });
      setRiskStatus((current) => ({ ...current, [riskId]: `${result.status}: ${result.message}` }));
    } catch (err) {
      setRiskStatus((current) => ({ ...current, [riskId]: err instanceof Error ? err.message : "Action failed" }));
    }
  }

  return (
    <section className="interaction-card">
      <div className="interaction-title-row">
        <ShieldAlert size={18} />
        <strong>{block.title || "Risk Review"}</strong>
      </div>
      <div className="risk-review-grid">
        {risks.map((risk, index) => (
          <article className="risk-block risk-review-item" key={String(risk.id || index)}>
            <div>
              <strong>{String(risk.clause || "Risk")}</strong>
              <span className={`risk-level ${String(risk.risk_level || "medium")}`}>{String(risk.risk_level || "medium")}</span>
            </div>
            <p>{String(risk.issue || "")}</p>
            <small>{String(risk.suggested_revision || "")}</small>
            {risk.evidence ? <small>Evidence: {String(risk.evidence)}</small> : null}
            <div className="risk-item-actions">
              <button className="small-button" onClick={() => void decideRisk(risk, "approve")}>Approve</button>
              <button className="small-button" onClick={() => void decideRisk(risk, "edit")}>Edit</button>
              <button className="small-button" onClick={() => void decideRisk(risk, "reject")}>Reject</button>
            </div>
            {riskStatus[String(risk.id || risk.clause || "risk")] ? (
              <small>{riskStatus[String(risk.id || risk.clause || "risk")]}</small>
            ) : null}
          </article>
        ))}
      </div>
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export function ComparisonMatrix({ artifact, block }: InteractionProps) {
  const columns = ((block.data.columns as Array<string | { key: string; label: string }>) || []).map((column) =>
    typeof column === "string" ? { key: column, label: column } : column
  );
  const rows = (block.data.rows as Array<Record<string, string>>) || [];
  return (
    <section className="interaction-card">
      <div className="interaction-title-row">
        <Sparkles size={18} />
        <strong>{block.title || "Comparison Matrix"}</strong>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index}>{columns.map((column) => <td key={column.key}>{row[column.key]}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export function MetricDashboard({ artifact, block }: InteractionProps) {
  const metrics = (block.data.metrics as Array<Record<string, unknown>>) || [];
  const insights = (block.data.insights as string[]) || [];
  return (
    <section className="interaction-card">
      <div className="interaction-title-row">
        <Gauge size={18} />
        <strong>{block.title || "Metric Dashboard"}</strong>
      </div>
      <div className="metric-dashboard">
        {metrics.map((metric, index) => (
          <div className="metric-block" key={`${String(metric.label)}-${index}`}>
            <span>{String(metric.label || "")}</span>
            <strong>{String(metric.value || "")}</strong>
            {metric.delta ? <small>{String(metric.delta)}</small> : null}
          </div>
        ))}
      </div>
      {insights.length ? (
        <ul className="artifact-list">{insights.map((item) => <li key={item}>{item}</li>)}</ul>
      ) : null}
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export function MemoryCandidateCard({ artifact, block }: InteractionProps) {
  return (
    <section className="interaction-card memory-candidate-card">
      <div className="interaction-title-row">
        <Database size={18} />
        <div>
          <strong>{block.title || "Memory candidate"}</strong>
          <span>confidence {String(block.data.confidence || "0.7")}</span>
        </div>
      </div>
      <p>{String(block.data.content || "")}</p>
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export function ToolCallPreview({ artifact, block }: InteractionProps) {
  return (
    <section className="interaction-card">
      <div className="interaction-title-row">
        <Play size={18} />
        <div>
          <strong>{String(block.data.tool_name || block.title || "Tool call")}</strong>
          <span>{String(block.data.permission_level || "low")} permission</span>
        </div>
      </div>
      <p>{String(block.data.summary || "")}</p>
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export function ActionQueue({ artifact, block }: InteractionProps) {
  const items = (block.data.items as Array<Record<string, unknown>>) || [];
  return (
    <section className="interaction-card">
      <div className="interaction-title-row">
        <Clock size={18} />
        <strong>{block.title || "Action Queue"}</strong>
      </div>
      <div className="action-queue">
        {items.map((item, index) => (
          <article className="action-queue-item" key={String(item.id || index)}>
            <strong>{String(item.title || "Action")}</strong>
            <span>{String(item.detail || "")}</span>
            <small>{String(item.status || "ready")}</small>
          </article>
        ))}
      </div>
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export function EditableDocumentPreview({ artifact, block }: InteractionProps) {
  const highlights = (block.data.highlights as string[]) || [];
  return (
    <section className="interaction-card editable-document-placeholder">
      <div className="interaction-title-row">
        <FilePenLine size={18} />
        <div>
          <strong>{String(block.data.heading || block.title || "Editable draft")}</strong>
          <span>{String(block.data.status || "draft")}</span>
        </div>
      </div>
      <div className="editable-preview">{String(block.data.content || "")}</div>
      {highlights.length ? (
        <div className="revision-highlights">
          {highlights.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      ) : null}
      <ActionButtons artifact={artifact} block={block} />
    </section>
  );
}

export const interactionComponentRegistry: Record<string, InteractionComponent> = {
  risk_summary: RiskSummary,
  approval_card: ApprovalCard,
  risk_review_panel: RiskReviewPanel,
  comparison_matrix: ComparisonMatrix,
  metric_dashboard: MetricDashboard,
  memory_candidate_card: MemoryCandidateCard,
  tool_call_preview: ToolCallPreview,
  action_queue: ActionQueue,
  editable_document_preview: EditableDocumentPreview,
  editable_document_placeholder: EditableDocumentPreview
};

export function renderInteractionComponent(artifact: Artifact, block: ArtifactBlock) {
  const Component = interactionComponentRegistry[block.type];
  return Component ? <Component artifact={artifact} block={block} /> : null;
}
