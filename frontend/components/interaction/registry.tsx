"use client";

import { useState } from "react";
import { AlertTriangle, Check, Clock, Database, FilePenLine, Gauge, Play, ShieldAlert, Sparkles, X } from "lucide-react";
import { apiFetch } from "../../lib/api";
import type { Artifact, ArtifactAction, ArtifactBlock, Memory, UIInteractionEvent } from "../../lib/types";

type InteractionProps = {
  artifact: Artifact;
  block: ArtifactBlock;
};

type InteractionComponent = (props: InteractionProps) => JSX.Element;

function eventTypeForAction(action: ArtifactAction) {
  if (action.action_type === "approve" || action.action_type === "confirm") return "artifact.action.approved";
  if (action.action_type === "reject") return "artifact.action.rejected";
  if (action.action_type === "select") return "artifact.option.selected";
  if (action.action_type === "edit") return "artifact.block.edited";
  if (action.action_type === "create_memory") return "memory.candidate.created";
  if (action.action_type === "promote_skill") return "skill.candidate.promoted";
  if (action.action_type === "invoke_tool") return "tool.invocation.requested";
  return "artifact.action.clicked";
}

function ActionButtons({ artifact, block }: InteractionProps) {
  const [status, setStatus] = useState<string | null>(null);
  const actions = block.actions || [];
  if (!actions.length) return null;

  async function handleAction(action: ArtifactAction) {
    setStatus("Saving observation");
    try {
      await recordInteraction(artifact, block, action);
      await applyAction(artifact, block, action);
      setStatus("Observation saved");
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
    </div>
  );
}

async function recordInteraction(artifact: Artifact, block: ArtifactBlock, action: ArtifactAction) {
  return apiFetch<UIInteractionEvent>("/api/interactions", {
    method: "POST",
    body: JSON.stringify({
      workspace_id: artifact.workspace_id,
      project_id: artifact.project_id || null,
      artifact_id: artifact.id,
      block_id: block.id,
      action_id: action.id,
      run_id: artifact.run_id || null,
      event_type: eventTypeForAction(action),
      payload: {
        artifact_type: artifact.type,
        block_type: block.type,
        action_type: action.action_type,
        confirmation_id: action.confirmation_id || null,
        state_binding: action.state_binding || block.state_binding || null,
        payload: action.payload || {}
      }
    })
  });
}

async function applyAction(artifact: Artifact, block: ArtifactBlock, action: ArtifactAction) {
  const binding = action.state_binding || block.state_binding;
  if ((action.action_type === "approve" || action.action_type === "confirm") && action.confirmation_id) {
    await apiFetch(`/api/confirmations/${action.confirmation_id}/approve`, {
      method: "POST",
      body: JSON.stringify({ decision: { source: "roam_component", action_id: action.id } })
    });
    return;
  }
  if (action.action_type === "reject" && action.confirmation_id) {
    await apiFetch(`/api/confirmations/${action.confirmation_id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason: "Rejected from ROAM component" })
    });
    return;
  }
  if ((action.action_type === "approve" || action.action_type === "confirm") && binding?.entity_type === "memory") {
    await apiFetch(`/api/memories/${binding.entity_id}/confirm`, { method: "POST" });
    return;
  }
  if (action.action_type === "reject" && binding?.entity_type === "memory") {
    await apiFetch(`/api/memories/${binding.entity_id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason: "Rejected from ROAM component" })
    });
    return;
  }
  if (action.action_type === "create_memory") {
    const content = String(action.payload?.content || block.data.content || "");
    if (!content) return;
    await apiFetch<Memory>("/api/memories", {
      method: "POST",
      body: JSON.stringify({
        workspace_id: artifact.workspace_id,
        project_id: artifact.project_id || null,
        source_run_id: artifact.run_id || null,
        source_type: "ui_interaction",
        source_id: artifact.id,
        type: String(action.payload?.type || block.data.memory_type || "task_experience"),
        content,
        confidence: Number(block.data.confidence || 0.7),
        status: "candidate",
        is_confirmed: false,
        structured_payload: { artifact_id: artifact.id, block_id: block.id, action_id: action.id }
      })
    });
    return;
  }
  if (action.action_type === "promote_skill" && binding?.entity_type === "skill_candidate") {
    await apiFetch(`/api/skills/candidates/${binding.entity_id}/promote`, { method: "POST" });
    return;
  }
  if (action.action_type === "invoke_tool" && action.payload?.tool_id) {
    await apiFetch(`/api/tools/${String(action.payload.tool_id)}/invoke`, {
      method: "POST",
      body: JSON.stringify({ input: action.payload.input || {} })
    });
  }
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
    setRiskStatus((current) => ({ ...current, [riskId]: "Saving observation" }));
    try {
      const action = {
        id: `${actionType}_${riskId}`,
        label: actionType,
        action_type: actionType,
        confirmation_required: false,
        payload: { risk_id: riskId, clause: risk.clause, risk_level: risk.risk_level },
      } satisfies ArtifactAction;
      await recordInteraction(artifact, block, action);
      setRiskStatus((current) => ({ ...current, [riskId]: "Observation saved" }));
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
