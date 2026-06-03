"use client";

/**
 * ArtifactBlocks — the rendering vocabulary for ArtifactSpec blocks.
 *
 * The Canvas iterates `artifact.schema_json.blocks` (filtered by view) and
 * maps each `block.type` to a React component here. Types not present in
 * the map get a generic fallback card. This means:
 *   - ANY agent can emit ANY block type it likes.
 *   - If the Canvas knows how to render it, it gets a specialised visual.
 *   - Otherwise it renders a clean "raw data" card. Zero crashes.
 *
 * Domain-specialised renderers (clause_reader, risk_radar, revision_diff)
 * live here too. They are NOT coupled to a specific agent; they're part of
 * the block vocabulary. An NDA-review agent or a compliance agent can emit
 * a `clause_reader` block and it'll render identically.
 */

import { useMemo, useRef, useEffect, useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ExternalLink,
  FileText,
  ShieldAlert,
} from "lucide-react";
import type { ArtifactBlock as ArtifactBlockType } from "../../lib/types";
import { blockData } from "../../lib/types";

// --------------------------------------------------------------------------- //
// Public API                                                                  //
// --------------------------------------------------------------------------- //

export interface ArtifactBlockProps {
  block: ArtifactBlockType;
  /** Optional callback when an action inside a block fires. */
  onAction?: (blockId: string, actionId: string, payload?: Record<string, unknown>) => void;
}

/**
 * Render a single ArtifactBlock. Used by ArtifactCanvas inside each view tab.
 */
export function ArtifactBlockRenderer({ block, onAction }: ArtifactBlockProps) {
  const Cmp = RENDERERS[block.type] ?? GenericBlock;
  return <Cmp block={block} onAction={onAction} />;
}

// --------------------------------------------------------------------------- //
// Renderer registry                                                           //
// --------------------------------------------------------------------------- //

type BlockRenderer = (props: ArtifactBlockProps) => JSX.Element;

const RENDERERS: Record<string, BlockRenderer> = {
  // Domain specialised
  risk_summary: RiskSummaryBlock,
  risk_review_panel: RiskReviewPanelBlock,
  risk_radar: RiskRadarBlock,
  clause_reader: ClauseReaderBlock,
  revision_diff: RevisionDiffBlock,
  editable_document_preview: EditableDocumentBlock,
  memory_candidate_card: MemoryCandidateBlock,
  // Generic structured
  metric_dashboard: MetricDashboardBlock,
  action_queue: ActionQueueBlock,
  comparison_matrix: ComparisonMatrixBlock,
  tool_call_preview: ToolCallPreviewBlock,
  approval_card: ApprovalCardBlock,
  markdown: MarkdownBlock,
};

// --------------------------------------------------------------------------- //
// Generic fallback                                                            //
// --------------------------------------------------------------------------- //

function GenericBlock({ block }: ArtifactBlockProps) {
  return (
    <div className="ab-card">
      <div className="ab-card-head">
        <span className="ab-type-pill">{block.type}</span>
        {block.title ? <strong>{block.title}</strong> : null}
      </div>
      <pre className="ab-card-json">{JSON.stringify(blockData(block), null, 2)}</pre>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// RISK_SUMMARY                                                                //
// --------------------------------------------------------------------------- //

function RiskSummaryBlock({ block }: ArtifactBlockProps) {
  const d = blockData(block) as Record<string, unknown>;
  const high = Number(d.high_count ?? 0);
  const medium = Number(d.medium_count ?? 0);
  const low = Number(d.low_count ?? 0);
  const total = Math.max(1, high + medium + low);
  const confidence = String(d.confidence ?? "—");
  const summary = String(d.summary ?? "");
  return (
    <div className="ab-risk-summary">
      <div className="ab-kpis">
        <div className="ab-kpi high"><span className="ab-kpi-label">High</span><strong>{high}</strong></div>
        <div className="ab-kpi medium"><span className="ab-kpi-label">Medium</span><strong>{medium}</strong></div>
        <div className="ab-kpi low"><span className="ab-kpi-label">Low</span><strong>{low}</strong></div>
        <div className="ab-kpi conf"><span className="ab-kpi-label">Confidence</span><strong>{confidence}</strong></div>
      </div>
      <div className="ab-distribution">
        <span className="ab-dist-label">Severity distribution</span>
        <div className="ab-dist-bar">
          <span className="seg high" style={{ width: `${(high / total) * 100}%` }} />
          <span className="seg medium" style={{ width: `${(medium / total) * 100}%` }} />
          <span className="seg low" style={{ width: `${(low / total) * 100}%` }} />
        </div>
      </div>
      {summary ? <p className="ab-summary-text">{summary}</p> : null}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// RISK_REVIEW_PANEL                                                           //
// --------------------------------------------------------------------------- //

interface RiskItem {
  id: string;
  clause: string;
  risk_level: string;
  issue: string;
  suggested_revision: string;
  evidence?: string;
}

function RiskReviewPanelBlock({ block }: ArtifactBlockProps) {
  const risks = ((blockData(block) as Record<string, unknown>).risks ?? []) as RiskItem[];
  const [sortKey, setSortKey] = useState<"severity" | "clause">("severity");
  const sorted = useMemo(() => {
    const order: Record<string, number> = { high: 0, medium: 1, low: 2 };
    const copy = [...risks];
    copy.sort(sortKey === "severity"
      ? (a, b) => (order[a.risk_level] ?? 9) - (order[b.risk_level] ?? 9)
      : (a, b) => a.clause.localeCompare(b.clause));
    return copy;
  }, [risks, sortKey]);

  if (!risks.length) return <div className="ab-empty">No risk findings.</div>;
  return (
    <div className="ab-risk-table-wrap">
      <div className="ab-table-toolbar">
        <div className="ab-table-title"><ShieldAlert size={14} /> Risk findings</div>
        <div className="ab-table-sort">
          Sort:
          <button type="button" className={sortKey === "severity" ? "chip active" : "chip"} onClick={() => setSortKey("severity")}>Severity</button>
          <button type="button" className={sortKey === "clause" ? "chip active" : "chip"} onClick={() => setSortKey("clause")}>Clause</button>
        </div>
      </div>
      <table className="ab-risk-table">
        <thead><tr><th>Severity</th><th>Clause</th><th>Issue</th></tr></thead>
        <tbody>
          {sorted.map((r) => (
            <tr key={r.id} className={`row-${r.risk_level}`}>
              <td><span className={`pill pill-${r.risk_level}`}>{r.risk_level}</span></td>
              <td className="clause-cell">{r.clause}</td>
              <td className="issue-cell">{r.issue}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// RISK_RADAR                                                                  //
// --------------------------------------------------------------------------- //

function RiskRadarBlock({ block }: ArtifactBlockProps) {
  const data = blockData(block) as { axes?: Array<{ id: string; label: string; normalised: number; score: number }>; total_risks?: number };
  const axes = data.axes ?? [];
  if (!axes.length) return <div className="ab-empty">No radar data.</div>;
  return (
    <div className="ab-radar">
      <div className="ab-radar-title"><ShieldAlert size={13} /> Risk radar · {data.total_risks ?? 0} findings</div>
      <div className="ab-radar-bars">
        {axes.map((axis) => (
          <div key={axis.id} className="ab-radar-row">
            <span className="ab-radar-label">{axis.label}</span>
            <div className="ab-radar-track">
              <div
                className={`ab-radar-fill ${axis.normalised > 0.7 ? "high" : axis.normalised > 0.4 ? "medium" : "low"}`}
                style={{ width: `${axis.normalised * 100}%` }}
              />
            </div>
            <span className="ab-radar-score">{axis.score}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// CLAUSE_READER                                                               //
// --------------------------------------------------------------------------- //

interface ClauseAnchor {
  risk_id: string;
  clause: string;
  severity: string;
  issue: string;
  suggested_revision: string;
  evidence?: string;
}

function ClauseReaderBlock({ block }: ArtifactBlockProps) {
  const data = blockData(block) as { content?: string; clause_anchors?: ClauseAnchor[]; language?: string; source?: string | null };
  const content = data.content ?? "";
  const anchors = data.clause_anchors ?? [];
  const [selected, setSelected] = useState<string | null>(anchors[0]?.risk_id ?? null);
  const readerRef = useRef<HTMLDivElement | null>(null);

  const activeAnchor = useMemo(() => anchors.find((a) => a.risk_id === selected) ?? anchors[0] ?? null, [anchors, selected]);
  const clauseTargets = useMemo(() => {
    const raw = activeAnchor?.clause ?? "";
    return raw.split(/[/,、，]/).map((s) => s.trim()).filter(Boolean);
  }, [activeAnchor]);

  useEffect(() => {
    if (!clauseTargets.length || !readerRef.current) return;
    const el = readerRef.current.querySelector<HTMLElement>(`[data-clause="${clauseTargets[0]}"]`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [clauseTargets.join("|")]);

  const blocks = useMemo(() => parseMarkdownBlocks(content), [content]);
  const highlightSet = new Set(clauseTargets);

  return (
    <div className="ab-clause-reader">
      <aside className="ab-clause-list">
        <header><ShieldAlert size={12} /> Risks <em>{anchors.length}</em></header>
        <ul>
          {anchors.map((a) => (
            <li key={a.risk_id}>
              <button type="button" className={`clause-entry ${selected === a.risk_id ? "active" : ""}`} onClick={() => setSelected(a.risk_id)}>
                <span className={`pill pill-${a.severity}`}>{a.severity}</span>
                <div><strong>{a.clause}</strong><small>{truncate(a.issue, 100)}</small></div>
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <section className="ab-clause-body">
        {activeAnchor ? (
          <div className="ab-clause-callout">
            <div className="callout-head"><span className={`pill pill-${activeAnchor.severity}`}>{activeAnchor.severity}</span><strong>Clause {activeAnchor.clause}</strong></div>
            <p className="callout-issue"><AlertTriangle size={12} /> {activeAnchor.issue}</p>
            <p className="callout-revision"><CheckCircle2 size={12} /> {activeAnchor.suggested_revision}</p>
            {activeAnchor.evidence ? <p className="callout-evidence"><FileText size={12} /> {activeAnchor.evidence}</p> : null}
          </div>
        ) : null}
        <div className="ab-clause-md" ref={readerRef}>
          {blocks.map((b, i) => {
            const isHl = b.clause && highlightSet.has(b.clause);
            const cls = `${b.kind} ${isHl ? "highlighted" : ""}`;
            const key = `${i}-${b.clause ?? ""}`;
            if (b.kind === "h1") return <h2 key={key} className={cls} data-clause={b.clause ?? undefined}>{b.text}</h2>;
            if (b.kind === "h2") return <h3 key={key} className={cls} data-clause={b.clause ?? undefined}>{b.text}</h3>;
            if (b.kind === "h3") return <h4 key={key} className={cls} data-clause={b.clause ?? undefined}>{b.text}</h4>;
            return <p key={key} className={cls} data-clause={b.clause ?? undefined}>{b.text}</p>;
          })}
        </div>
      </section>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// REVISION_DIFF                                                               //
// --------------------------------------------------------------------------- //

interface RevHunk { id: string; title: string; severity: string; before: string; after: string; status: string }

function RevisionDiffBlock({ block }: ArtifactBlockProps) {
  const data = blockData(block) as { summary?: { heading?: string; content?: string; highlights?: string[] }; hunks?: RevHunk[] };
  const hunks = data.hunks ?? [];
  const summary = data.summary;
  return (
    <div className="ab-revision-diff">
      {summary ? (
        <div className="ab-rev-summary">
          <strong>{summary.heading}</strong>
          <p>{summary.content}</p>
          {summary.highlights?.length ? (
            <ul className="ab-rev-highlights">
              {summary.highlights.map((h) => <li key={h}><CheckCircle2 size={11} /> {h}</li>)}
            </ul>
          ) : null}
        </div>
      ) : null}
      {hunks.length ? (
        <div className="ab-rev-hunks">
          {hunks.map((hunk) => (
            <div key={hunk.id} className={`ab-rev-hunk ${hunk.severity}`}>
              <div className="hunk-head"><span className={`pill pill-${hunk.severity}`}>{hunk.severity}</span><strong>{hunk.title}</strong></div>
              <div className="hunk-grid">
                <div className="hunk-before"><span className="hunk-label">Current</span><p>{hunk.before}</p></div>
                <div className="hunk-after"><span className="hunk-label">Proposed</span><p>{hunk.after}</p></div>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// EDITABLE_DOCUMENT_PREVIEW                                                   //
// --------------------------------------------------------------------------- //

function EditableDocumentBlock({ block }: ArtifactBlockProps) {
  const d = blockData(block) as { heading?: string; content?: string; highlights?: string[]; status?: string };
  return (
    <div className="ab-card">
      <div className="ab-card-head"><strong>{d.heading ?? block.title ?? "Document"}</strong><small>{d.status ?? "draft"}</small></div>
      <p className="ab-doc-content">{d.content}</p>
      {d.highlights?.length ? <ul className="ab-doc-highlights">{d.highlights.map((h) => <li key={h}><CheckCircle2 size={11} /> {h}</li>)}</ul> : null}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// MEMORY_CANDIDATE_CARD                                                       //
// --------------------------------------------------------------------------- //

function MemoryCandidateBlock({ block }: ArtifactBlockProps) {
  const d = blockData(block) as { content?: string; memory_type?: string; confidence?: number };
  return (
    <div className="ab-card candidate">
      <div className="ab-card-head"><span className="ab-type-pill">memory</span><small>confidence {((d.confidence ?? 0) * 100).toFixed(0)}%</small></div>
      <p>{d.content}</p>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// METRIC_DASHBOARD                                                            //
// --------------------------------------------------------------------------- //

function MetricDashboardBlock({ block }: ArtifactBlockProps) {
  const d = blockData(block) as { metrics?: Array<{ label: string; value: unknown; delta?: string }>; insights?: string[] };
  return (
    <div className="ab-metrics">
      <div className="ab-kpis">
        {(d.metrics ?? []).map((m) => (
          <div key={m.label} className="ab-kpi"><span className="ab-kpi-label">{m.label}</span><strong>{String(m.value)}</strong>{m.delta ? <small>{m.delta}</small> : null}</div>
        ))}
      </div>
      {d.insights?.length ? <ul className="ab-insights">{d.insights.map((t) => <li key={t}>{t}</li>)}</ul> : null}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// ACTION_QUEUE                                                                //
// --------------------------------------------------------------------------- //

function ActionQueueBlock({ block }: ArtifactBlockProps) {
  const d = blockData(block) as { items?: Array<{ id: string; title: string; detail?: string; status?: string }> };
  return (
    <div className="ab-action-queue">
      {(d.items ?? []).map((item) => (
        <div key={item.id} className={`ab-action-item ${item.status ?? "ready"}`}>
          <strong>{item.title}</strong>
          {item.detail ? <small>{item.detail}</small> : null}
          <span className="ab-action-status">{item.status ?? "ready"}</span>
        </div>
      ))}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// COMPARISON_MATRIX                                                           //
// --------------------------------------------------------------------------- //

function ComparisonMatrixBlock({ block }: ArtifactBlockProps) {
  const d = blockData(block) as { columns?: Array<{ key: string; label: string }>; rows?: Array<Record<string, string>> };
  const cols = d.columns ?? [];
  const rows = d.rows ?? [];
  if (!cols.length) return <GenericBlock block={block} />;
  return (
    <div className="ab-comparison">
      <table>
        <thead><tr>{cols.map((c) => <th key={c.key}>{c.label}</th>)}</tr></thead>
        <tbody>{rows.map((row, i) => <tr key={i}>{cols.map((c) => <td key={c.key}>{row[c.key] ?? ""}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// TOOL_CALL_PREVIEW                                                           //
// --------------------------------------------------------------------------- //

function ToolCallPreviewBlock({ block }: ArtifactBlockProps) {
  const d = blockData(block) as { tool_name?: string; permission_level?: string; summary?: string };
  return (
    <div className="ab-card">
      <div className="ab-card-head"><span className="ab-type-pill">{d.tool_name ?? "Tool"}</span><small>{d.permission_level}</small></div>
      <p>{d.summary}</p>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// APPROVAL_CARD                                                               //
// --------------------------------------------------------------------------- //

function ApprovalCardBlock({ block }: ArtifactBlockProps) {
  const d = blockData(block) as { title?: string; content?: string; risk_level?: string };
  return (
    <div className={`ab-card ${d.risk_level === "high" ? "high" : ""}`}>
      <div className="ab-card-head"><strong>{d.title ?? block.title}</strong></div>
      <p>{d.content}</p>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// MARKDOWN                                                                    //
// --------------------------------------------------------------------------- //

function MarkdownBlock({ block }: ArtifactBlockProps) {
  const content = String((blockData(block) as Record<string, unknown>).content ?? "");
  return <div className="ab-markdown"><p>{content}</p></div>;
}

// --------------------------------------------------------------------------- //
// Shared helpers                                                              //
// --------------------------------------------------------------------------- //

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

interface ParsedBlock { kind: "h1" | "h2" | "h3" | "p"; text: string; clause: string | null }

function parseMarkdownBlocks(content: string): ParsedBlock[] {
  const lines = content.split(/\r?\n/);
  const result: ParsedBlock[] = [];
  let para: string[] = [];
  const flush = () => { if (para.length) { const t = para.join(" ").trim(); if (t) result.push({ kind: "p", text: t, clause: detectClause(t) }); para = []; } };
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) { flush(); continue; }
    const h1 = /^#\s+(.*)$/.exec(line);
    const h2 = /^##\s+(.*)$/.exec(line);
    const h3 = /^###\s+(.*)$/.exec(line);
    if (h1) { flush(); result.push({ kind: "h1", text: h1[1], clause: detectClause(h1[1]) }); }
    else if (h2) { flush(); result.push({ kind: "h2", text: h2[1], clause: detectClause(h2[1]) }); }
    else if (h3) { flush(); result.push({ kind: "h3", text: h3[1], clause: detectClause(h3[1]) }); }
    else { para.push(line); }
  }
  flush();
  return result;
}

function detectClause(text: string): string | null {
  const bold = /^\*\*(\d+(?:\.\d+)?)\*\*/.exec(text.trim());
  if (bold) return bold[1];
  const cn = /^第\s*(\d+(?:\.\d+)?)\s*条/.exec(text.trim());
  if (cn) return cn[1];
  const num = /^(\d+\.\d+)(?:[\s、:：.])/.exec(text.trim());
  if (num) return num[1];
  return null;
}
