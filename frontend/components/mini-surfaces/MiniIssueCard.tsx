import { ArrowUpRight, Check } from "lucide-react";
import type { Artifact } from "../../lib/types";

export function MiniIssueCard({
  artifact,
  labels,
  onApprove,
  onEdit,
  onFullReview,
  primaryRisk,
  summary,
}: {
  artifact: Artifact;
  labels: {
    title: string;
    activeRisk: string;
    recommendedRevision: string;
    evidence: string;
    high: string;
    medium: string;
    low: string;
    approveRevision: string;
    editDirection: string;
    openFullReview: string;
  };
  onApprove: () => Promise<void>;
  onEdit: () => Promise<void>;
  onFullReview: () => Promise<void>;
  primaryRisk?: Record<string, unknown>;
  summary?: Record<string, unknown>;
}) {
  return (
    <article className="mini-surface-card contract-review-mini">
      <header>
        <span className="eyebrow">MiniIssueCard</span>
        <h2>{artifact.title}</h2>
      </header>
      {summary ? (
        <div className="mini-risk-metrics">
          <div><strong>{String(summary.high_count || 0)}</strong><span>{labels.high}</span></div>
          <div><strong>{String(summary.medium_count || 0)}</strong><span>{labels.medium}</span></div>
          <div><strong>{String(summary.low_count || 0)}</strong><span>{labels.low}</span></div>
        </div>
      ) : null}
      {primaryRisk ? (
        <section className="mini-active-risk">
          <strong>{labels.activeRisk}: {String(primaryRisk.clause || "")}</strong>
          <p>{String(primaryRisk.issue || "")}</p>
          <b>{labels.recommendedRevision}</b>
          <p>{String(primaryRisk.suggested_revision || "")}</p>
          {primaryRisk.evidence ? <small>{labels.evidence}: {String(primaryRisk.evidence)}</small> : null}
        </section>
      ) : null}
      <div className="mini-surface-actions">
        <button className="primary-button" onClick={() => void onApprove()}><Check size={14} /> {labels.approveRevision}</button>
        <button className="secondary-action" onClick={() => void onEdit()}>{labels.editDirection}</button>
        <button className="secondary-action" onClick={() => void onFullReview()}><ArrowUpRight size={14} /> {labels.openFullReview}</button>
      </div>
    </article>
  );
}
