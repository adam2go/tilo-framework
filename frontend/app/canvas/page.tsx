"use client";

/**
 * Tilo 3D Canvas — Agent-generated spatial workspace.
 *
 * Highlights:
 * - Real backend trace polling (no fake stream)
 * - Heartbeat indicator while LLM is thinking
 * - Mouse wheel zooms the scene (not the browser)
 * - Tight grid layout that scales with panel count
 * - Interactive blocks: buttons, checkboxes, inputs, ratings — not just display
 */

import { useCallback, useEffect, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─────────────────────────────────────────────────────────────────────────── //
// Types                                                                       //
// ─────────────────────────────────────────────────────────────────────────── //

interface AIPBlock {
  id: string;
  type: string;
  title?: string | null;
  props?: Record<string, unknown>;
  data?: Record<string, unknown>;
  actions?: Array<{ id: string; label: string; action_type: string }>;
}

interface AIPView {
  id: string;
  label: string;
  block_ids?: string[];
}

interface AIPSpec {
  version: string;
  title: string;
  blocks: AIPBlock[];
  views?: AIPView[];
  follow_ups?: string[];
}

interface TraceStep {
  id: string;
  step_type: string;
  title: string;
  summary: string;
  status: string;
}

interface StreamLine {
  id: string;
  text: string;
  kind: "info" | "ok" | "warn" | "thinking";
}

// ─────────────────────────────────────────────────────────────────────────── //
// Safe data accessors — LLM output may not match our expected shapes          //
// ─────────────────────────────────────────────────────────────────────────── //

function asArray<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function asString(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && !Number.isNaN(value)) return value;
  if (typeof value === "string") {
    const parsed = parseFloat(value);
    if (!Number.isNaN(parsed)) return parsed;
  }
  return fallback;
}

// ─────────────────────────────────────────────────────────────────────────── //
// 3D layout: tight multi-row grid                                             //
// ─────────────────────────────────────────────────────────────────────────── //
// 3D layout: column-balanced masonry. Heights are measured at runtime so      //
// we never collide regardless of how tall a panel's content turns out to be.  //
// ─────────────────────────────────────────────────────────────────────────── //

const COLUMN_COUNT = 3;
const COLUMN_GAP_X = 50;   // horizontal gap between columns
const ROW_GAP_Y = 32;      // vertical gap between panels in a column
const FALLBACK_HEIGHT = 240; // height to assume before measurement

function panelWidthFor(blockType: string): number {
  if (blockType === "table") return 360;
  if (blockType === "diff" || blockType === "timeline") return 340;
  return 300;
}

interface PanelLayout {
  x: number;
  y: number;
  z: number;
  width: number;
  measuredHeight: number;
}

/**
 * Lay out N panels in 3 columns. The shortest column always gets the next
 * panel — a classic masonry algorithm — so we never overlap and the layout
 * stays balanced. Position is centered around (0, 0) so the canvas pivots
 * around the visual center of the spec.
 */
function computeMasonryLayout(
  blocks: AIPBlock[],
  measuredHeights: Record<string, number>,
): PanelLayout[] {
  const layouts: PanelLayout[] = [];
  const colHeights = new Array(COLUMN_COUNT).fill(0);
  const colWidths = new Array(COLUMN_COUNT).fill(0); // tracks each column's max panel width
  const colXs: number[] = [];

  // Pass 1: compute each column's max width so x-offsets stay tight
  blocks.forEach((b, i) => {
    const col = i % COLUMN_COUNT;
    colWidths[col] = Math.max(colWidths[col], panelWidthFor(b.type));
  });
  // Convert max widths into actual x offsets (centered)
  let xCursor = 0;
  for (let c = 0; c < COLUMN_COUNT; c += 1) {
    colXs.push(xCursor);
    xCursor += colWidths[c] + COLUMN_GAP_X;
  }
  const totalWidth = xCursor - COLUMN_GAP_X;
  const xCenterShift = totalWidth / 2;

  // Pass 2: pack each block into the shortest column
  for (const block of blocks) {
    const w = panelWidthFor(block.type);
    const h = measuredHeights[block.id] ?? FALLBACK_HEIGHT;

    let shortestCol = 0;
    for (let c = 1; c < COLUMN_COUNT; c += 1) {
      if (colHeights[c] < colHeights[shortestCol]) shortestCol = c;
    }

    // Anchor each panel by its center: x = column-left + colWidth/2 - panelWidth/2
    const colLeft = colXs[shortestCol] - xCenterShift;
    const x = colLeft + colWidths[shortestCol] / 2;
    const y = colHeights[shortestCol] + h / 2;
    layouts.push({ x, y, z: 0, width: w, measuredHeight: h });
    colHeights[shortestCol] += h + ROW_GAP_Y;
  }

  // Center vertically around the canvas origin
  const totalHeight = Math.max(...colHeights, 0);
  const yCenterShift = totalHeight / 2;
  return layouts.map((l) => ({ ...l, y: l.y - yCenterShift }));
}

function defaultScale(panelCount: number): number {
  if (panelCount > 6) return 0.7;
  if (panelCount > 3) return 0.9;
  return 1.0;
}

// ─────────────────────────────────────────────────────────────────────────── //
// Block content renderer — interactive, defensive                             //
// ─────────────────────────────────────────────────────────────────────────── //

function BlockContent({ block }: { block: AIPBlock }) {
  const d = (block.props ?? block.data ?? {}) as Record<string, unknown>;

  try {
    switch (block.type) {
      case "markdown":
      case "code":
      case "heading":
        return <div className="cx-markdown">{asString(d.content ?? d.text)}</div>;

      case "table":
        return <TableBlock data={d} />;

      case "chart":
        return <ChartBlock data={d} />;

      case "metric":
        return <MetricBlock data={d} title={asString(block.title)} />;

      case "diff":
        return (
          <div className="cx-diff">
            <div className="cx-diff-before">
              <span className="cx-diff-tag">- BEFORE</span>
              <p>{asString(d.before)}</p>
            </div>
            <div className="cx-diff-after">
              <span className="cx-diff-tag">+ AFTER</span>
              <p>{asString(d.after)}</p>
            </div>
            {d.context != null && <div className="cx-diff-context">{asString(d.context)}</div>}
          </div>
        );

      case "card":
        return <CardBlock data={d} title={asString(block.title)} />;

      case "list":
        return <ListBlock data={d} />;

      case "checklist":
        return <ChecklistBlock data={d} />;

      case "button_group":
        return <ButtonGroupBlock data={d} />;

      case "rating":
        return <RatingBlock data={d} />;

      case "confirmation":
        return <ConfirmWidget description={asString(d.description ?? d.title ?? "Requires confirmation")} riskLevel={asString(d.risk_level)} />;

      case "memory_card":
        return <MemoryWidget content={asString(d.content)} confidence={asNumber(d.confidence, 0.7)} />;

      case "form":
        return <FormBlock data={d} />;

      case "tool_preview":
        return (
          <div className="cx-card-inner">
            <div className="cx-card-title">{asString(d.tool_name ?? "Tool")}</div>
            <p>{asString(d.summary)}</p>
            {d.permission_level != null && (
              <div className="cx-card-severity">Permission: {asString(d.permission_level)}</div>
            )}
          </div>
        );

      case "timeline":
        return <TimelineBlock data={d} />;

      case "progress":
        return <ProgressBlock data={d} />;

      case "image":
        return <ImageBlock data={d} />;

      default:
        return <pre className="cx-json">{JSON.stringify(d, null, 2)}</pre>;
    }
  } catch (err) {
    return <pre className="cx-json error">RENDER_ERROR: {String(err)}{"\n\n"}{JSON.stringify(d, null, 2)}</pre>;
  }
}

function TableBlock({ data }: { data: Record<string, unknown> }) {
  const cols = asArray<{ key?: string; label?: string }>(data.columns);
  const rawRows = asArray<Record<string, unknown>>(data.rows);
  const [selectedRow, setSelectedRow] = useState<number | null>(null);

  if (cols.length === 0 && rawRows.length === 0) {
    return <pre className="cx-json">{JSON.stringify(data, null, 2)}</pre>;
  }
  const effectiveCols = cols.length > 0
    ? cols
    : rawRows.length > 0
      ? Object.keys(rawRows[0]).map((k) => ({ key: k, label: k }))
      : [];

  return (
    <div className="cx-table-wrap">
      <table className="cx-table interactive">
        <thead>
          <tr>{effectiveCols.map((c, i) => <th key={c.key ?? `c${i}`}>{c.label ?? c.key ?? ""}</th>)}</tr>
        </thead>
        <tbody>
          {rawRows.map((row, i) => (
            <tr
              key={i}
              className={selectedRow === i ? "selected" : ""}
              onClick={() => setSelectedRow(selectedRow === i ? null : i)}
            >
              {effectiveCols.map((c, j) => (
                <td key={c.key ?? `c${j}`}>{asString(row[c.key ?? ""])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {selectedRow !== null && (
        <div className="cx-table-action">
          ▸ Selected row {selectedRow + 1} —
          <button className="cx-btn small" onClick={(e) => { e.stopPropagation(); alert(`Drilled into row ${selectedRow + 1}`); }}>Drill in</button>
        </div>
      )}
    </div>
  );
}

function ChartBlock({ data }: { data: Record<string, unknown> }) {
  let axes = asArray<{ label?: string; score?: number; normalised?: number; value?: number }>(data.axes);
  if (axes.length === 0) {
    const inner = (data.data && typeof data.data === "object" ? data.data : {}) as Record<string, unknown>;
    const labels = asArray<unknown>(inner.labels);
    const datasets = asArray<Record<string, unknown>>(inner.datasets);
    const firstSeries = datasets.length > 0 ? asArray<unknown>(datasets[0].data) : [];
    if (labels.length > 0) {
      axes = labels.map((label, i) => ({ label: asString(label), score: asNumber(firstSeries[i], 0) }));
    }
  }
  if (axes.length === 0 && data.values && typeof data.values === "object") {
    axes = Object.entries(data.values as Record<string, unknown>).map(([k, v]) => ({ label: k, score: asNumber(v, 0) }));
  }
  if (axes.length === 0) {
    return <pre className="cx-json">{JSON.stringify(data, null, 2)}</pre>;
  }
  const scores = axes.map((a) => a.score ?? a.value ?? 0);
  const maxScore = Math.max(...scores, 1);
  return (
    <div className="cx-bars">
      {axes.map((axis, i) => {
        const score = axis.score ?? axis.value ?? 0;
        const ratio = axis.normalised != null ? axis.normalised : score / maxScore;
        return (
          <div key={`${axis.label ?? i}`} className="cx-bar-row">
            <span className="cx-bar-label">{asString(axis.label) || `Axis ${i + 1}`}</span>
            <div className="cx-bar-track">
              <div className="cx-bar-fill" style={{ width: `${Math.max(2, Math.min(100, ratio * 100))}%` }} />
            </div>
            <span className="cx-bar-num">{score}</span>
          </div>
        );
      })}
    </div>
  );
}

function MetricBlock({ data, title }: { data: Record<string, unknown>; title: string }) {
  const [active, setActive] = useState(false);
  return (
    <div className={`cx-metric ${active ? "active" : ""}`} onClick={() => setActive(!active)}>
      <div className="cx-metric-value">{asString(data.value)}</div>
      <div className="cx-metric-label">{asString(data.label ?? title)}</div>
      {data.delta != null && <div className="cx-metric-delta">{asString(data.delta)}</div>}
      {active && <div className="cx-metric-detail">▸ Click for breakdown</div>}
    </div>
  );
}

function CardBlock({ data, title }: { data: Record<string, unknown>; title: string }) {
  const cardTitle = asString(data.title ?? title);
  const content = asString(data.content ?? data.summary ?? data.description);
  const severity = asString(data.severity ?? data.status);
  const [expanded, setExpanded] = useState(false);
  const isLong = content.length > 180;
  const displayContent = isLong && !expanded ? content.slice(0, 180) + "..." : content;
  return (
    <div className="cx-card-inner">
      {cardTitle && <div className="cx-card-title">{cardTitle}</div>}
      {severity && <div className={`cx-card-severity ${severity.toLowerCase()}`}>{severity}</div>}
      <p>{displayContent}</p>
      {isLong && (
        <button className="cx-btn small" onClick={() => setExpanded(!expanded)}>
          {expanded ? "▴ Less" : "▾ More"}
        </button>
      )}
    </div>
  );
}

function ListBlock({ data }: { data: Record<string, unknown> }) {
  let items = asArray<unknown>(data.items);
  if (items.length === 0 && Array.isArray(data.list)) items = data.list as unknown[];
  if (items.length === 0) return <pre className="cx-json">{JSON.stringify(data, null, 2)}</pre>;
  return (
    <ul className="cx-list">
      {items.map((rawItem, i) => {
        if (typeof rawItem === "string") return <li key={i}>{rawItem}</li>;
        const item = (rawItem ?? {}) as Record<string, unknown>;
        const text = asString(item.text ?? item.title ?? item.label ?? item.name);
        const detail = asString(item.detail ?? item.description ?? item.severity);
        return (
          <li key={i}>
            {text}
            {detail && <small> — {detail}</small>}
          </li>
        );
      })}
    </ul>
  );
}

/** Interactive checklist — user can check/uncheck items */
function ChecklistBlock({ data }: { data: Record<string, unknown> }) {
  const items = asArray<Record<string, unknown>>(data.items);
  const [checked, setChecked] = useState<Set<number>>(() => {
    const initial = new Set<number>();
    items.forEach((it, i) => { if (it.checked === true || it.completed === true) initial.add(i); });
    return initial;
  });
  if (items.length === 0) return <pre className="cx-json">{JSON.stringify(data, null, 2)}</pre>;
  const toggle = (i: number) => {
    const next = new Set(checked);
    if (next.has(i)) next.delete(i);
    else next.add(i);
    setChecked(next);
  };
  const completed = checked.size;
  return (
    <div className="cx-checklist">
      <div className="cx-checklist-progress">
        <span>{completed}/{items.length} done</span>
        <div className="cx-progress-bar"><div className="cx-progress-fill" style={{ width: `${(completed / items.length) * 100}%` }} /></div>
      </div>
      <ul>
        {items.map((item, i) => (
          <li key={i} className={checked.has(i) ? "checked" : ""} onClick={() => toggle(i)}>
            <span className="cx-check-box">{checked.has(i) ? "☑" : "☐"}</span>
            <span className="cx-check-text">{asString(item.text ?? item.label ?? item.title)}</span>
            {item.detail != null && <small>{asString(item.detail)}</small>}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Interactive button group — clicking a button "fires" an action */
function ButtonGroupBlock({ data }: { data: Record<string, unknown> }) {
  const buttons = asArray<Record<string, unknown>>(data.buttons);
  const [fired, setFired] = useState<Set<string>>(new Set());
  if (buttons.length === 0) return <pre className="cx-json">{JSON.stringify(data, null, 2)}</pre>;
  return (
    <div className="cx-button-group">
      {buttons.map((btn, i) => {
        const label = asString(btn.label ?? btn.text);
        const id = asString(btn.action_id ?? btn.id ?? `btn_${i}`);
        const variant = asString(btn.variant ?? "default");
        const wasFired = fired.has(id);
        return (
          <button
            key={id}
            className={`cx-btn ${variant === "primary" ? "primary" : ""} ${wasFired ? "fired" : ""}`}
            onClick={() => setFired((prev) => new Set([...prev, id]))}
          >
            {wasFired ? "✓ " : ""}{label}
          </button>
        );
      })}
    </div>
  );
}

/** Star rating that user can change */
function RatingBlock({ data }: { data: Record<string, unknown> }) {
  const max = asNumber(data.max, 5);
  const initial = asNumber(data.value, 0);
  const [rating, setRating] = useState(initial);
  const label = asString(data.label);
  return (
    <div className="cx-rating">
      {label && <div className="cx-rating-label">{label}</div>}
      <div className="cx-stars">
        {Array.from({ length: max }).map((_, i) => (
          <button key={i} className={`cx-star ${i < rating ? "filled" : ""}`} onClick={() => setRating(i + 1)}>
            ★
          </button>
        ))}
        <span className="cx-rating-value">{rating}/{max}</span>
      </div>
    </div>
  );
}

function FormBlock({ data }: { data: Record<string, unknown> }) {
  const fields = asArray<Record<string, unknown>>(data.fields);
  const [values, setValues] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  if (fields.length === 0) return <pre className="cx-json">{JSON.stringify(data, null, 2)}</pre>;
  if (submitted) return <div className="cx-done">✓ FORM SUBMITTED · {Object.keys(values).length} FIELDS</div>;
  return (
    <div className="cx-form">
      {fields.map((f, i) => {
        const name = asString(f.name) || `field_${i}`;
        const label = asString(f.label ?? f.name);
        const kind = asString(f.kind ?? f.type, "text");
        return (
          <div key={name} className="cx-form-field">
            <label>{label}</label>
            <input
              type={kind === "number" ? "number" : "text"}
              placeholder={asString(f.placeholder ?? label)}
              value={values[name] ?? ""}
              onChange={(e) => setValues({ ...values, [name]: e.target.value })}
            />
          </div>
        );
      })}
      <button className="cx-btn primary" onClick={() => setSubmitted(true)}>Submit</button>
    </div>
  );
}

function TimelineBlock({ data }: { data: Record<string, unknown> }) {
  const items = asArray<Record<string, unknown>>(data.items);
  const [activeIdx, setActiveIdx] = useState<number | null>(null);
  if (items.length === 0) return <pre className="cx-json">{JSON.stringify(data, null, 2)}</pre>;
  return (
    <ol className="cx-timeline">
      {items.map((item, i) => (
        <li
          key={i}
          className={activeIdx === i ? "active" : ""}
          onClick={() => setActiveIdx(activeIdx === i ? null : i)}
        >
          <span className="cx-timeline-time">{asString(item.time ?? item.date)}</span>
          <span className="cx-timeline-title">{asString(item.title ?? item.label)}</span>
          {(item.description != null || activeIdx === i) && (
            <span className="cx-timeline-desc">{asString(item.description)}</span>
          )}
        </li>
      ))}
    </ol>
  );
}

function ProgressBlock({ data }: { data: Record<string, unknown> }) {
  const percent = asNumber(data.percent ?? data.value, 0);
  const steps = asArray<Record<string, unknown>>(data.steps);
  return (
    <div className="cx-progress">
      <div className="cx-progress-bar">
        <div className="cx-progress-fill" style={{ width: `${Math.max(0, Math.min(100, percent))}%` }} />
      </div>
      <div className="cx-progress-pct">{Math.round(percent)}%</div>
      {steps.length > 0 && (
        <ol className="cx-progress-steps">
          {steps.map((s, i) => (
            <li key={i} className={asString(s.state)}>{asString(s.label)}</li>
          ))}
        </ol>
      )}
    </div>
  );
}

function ImageBlock({ data }: { data: Record<string, unknown> }) {
  const src = asString(data.src ?? data.url);
  const alt = asString(data.alt ?? data.caption);
  if (!src) return <pre className="cx-json">{JSON.stringify(data, null, 2)}</pre>;
  /* eslint-disable-next-line @next/next/no-img-element */
  return <img className="cx-image" src={src} alt={alt} />;
}

function ConfirmWidget({ description, riskLevel }: { description: string; riskLevel?: string }) {
  const [status, setStatus] = useState<"pending" | "approved" | "rejected">("pending");
  if (status === "approved") return <div className="cx-done">✓ APPROVED · MEMORY GENERATED</div>;
  if (status === "rejected") return <div className="cx-done warn">✕ REJECTED · NO ACTION TAKEN</div>;
  return (
    <div className="cx-confirm">
      <p>{description}</p>
      {riskLevel && <div className={`cx-card-severity ${riskLevel.toLowerCase()}`}>RISK: {riskLevel}</div>}
      <div className="cx-confirm-btns">
        <button className="cx-btn primary" onClick={() => setStatus("approved")}>✓ Approve</button>
        <button className="cx-btn" onClick={() => setStatus("rejected")}>✕ Reject</button>
      </div>
    </div>
  );
}

function MemoryWidget({ content, confidence }: { content: string; confidence: number }) {
  const [confirmed, setConfirmed] = useState(false);
  const [edit, setEdit] = useState(false);
  const [text, setText] = useState(content);
  return (
    <div className="cx-memory">
      {edit ? (
        <textarea className="cx-memory-edit" value={text} onChange={(e) => setText(e.target.value)} />
      ) : (
        <p>{text}</p>
      )}
      <div className="cx-memory-meta">confidence: {Math.round(confidence * 100)}%</div>
      {!confirmed ? (
        <div className="cx-confirm-btns">
          <button className="cx-btn primary" onClick={() => setConfirmed(true)}>◉ Confirm</button>
          <button className="cx-btn" onClick={() => setEdit(!edit)}>{edit ? "Done" : "✎ Edit"}</button>
        </div>
      ) : (
        <div className="cx-done">✓ SAVED · AVAILABLE IN FUTURE SESSIONS</div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────── //
// Sample goals — everyday scenarios, fast & demo-friendly                     //
// ─────────────────────────────────────────────────────────────────────────── //

const SAMPLE_GOALS = [
  {
    icon: "✈",
    label: "Plan a SF Weekend",
    goal: "Plan a 3-day San Francisco weekend trip for 2 people in late September. Mix iconic landmarks, local food, and a Napa day-trip. Budget around $1500 per person excluding flights.",
    color: "#22d3ee",
    /** Always available — has a baked-in fixture for offline/no-LLM mode. */
    requiresLLM: false,
    fixturePath: "/canvas-fixtures/sf-trip.json",
  },
  {
    icon: "⌥",
    label: "Review a Pull Request",
    goal: "Review pull request #482 from the feat/session-auth branch. It replaces the JWT auth middleware with Redis-backed sessions across 5 files (+312 / −187 LOC). Flag risky changes, list verification items, and decide whether to approve the merge.",
    color: "#10b981",
    requiresLLM: true,
  },
  {
    icon: "◆",
    label: "Weekly Sales Briefing",
    goal: "Generate a sales follow-up briefing for this week — top accounts, pending decisions, recommended next actions.",
    color: "#f97316",
    requiresLLM: true,
  },
];

const HEARTBEAT_MESSAGES = [
  "thinking",
  "analyzing context",
  "consulting skill hints",
  "drafting view structure",
  "selecting block types",
  "composing JSON spec",
  "validating output schema",
  "almost there",
];

// ─────────────────────────────────────────────────────────────────────────── //
// Main Component                                                              //
// ─────────────────────────────────────────────────────────────────────────── //

interface Turn {
  id: string;
  goal: string;
  spec_title: string;
  blocks: AIPBlock[];
  follow_ups: string[];
  generation_mode: string;
  created_at: number;
  measured_heights: Record<string, number>;
}

const MAX_TURNS = 5;
const TURN_DEPTH_STEP = 900; // z-distance between turns (larger = more parallax)
const TURN_OPACITY_FACTOR = 0.35; // active=1, one-back=0.35, two-back=0.12...

export default function TiloCanvasPage() {
  const [goal, setGoal] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [activeTurnId, setActiveTurnId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orbitY, setOrbitY] = useState(0);
  const [orbitX, setOrbitX] = useState(0);
  const [zoom, setZoom] = useState(1.0);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [dragMode, setDragMode] = useState<"none" | "pan" | "orbit">("none");
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [streamLines, setStreamLines] = useState<StreamLine[]>([]);
  const [streamCollapsed, setStreamCollapsed] = useState(false);
  const [heartbeatText, setHeartbeatText] = useState("");
  const [elapsedSec, setElapsedSec] = useState(0);
  /** null = checking, true/false = result. Used to decide which samples to show. */
  const [llmAvailable, setLlmAvailable] = useState<boolean | null>(null);
  const streamRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<HTMLDivElement>(null);

  // Detect LLM availability once on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/runtime/capabilities`)
      .then((r) => r.json())
      .then((d) => setLlmAvailable(Boolean(d.llm_enabled && d.llm_configured)))
      .catch(() => setLlmAvailable(false));
  }, []);

  // ─── Derived: active turn ──────────────────────────────────────────────── //
  const activeTurn = turns.find((t) => t.id === activeTurnId) ?? turns[turns.length - 1] ?? null;
  const activeBlocks = activeTurn?.blocks ?? [];
  const specTitle = activeTurn?.spec_title ?? "";
  const followUps = activeTurn?.follow_ups ?? [];
  const generationMode = activeTurn?.generation_mode ?? "";

  const pushLine = useCallback((text: string, kind: StreamLine["kind"] = "info") => {
    setStreamLines((prev) => [...prev, { id: `${Date.now()}-${Math.random()}`, text, kind }]);
  }, []);

  // Auto-scroll stream
  useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [streamLines]);

  // Reset view to default whenever active turn block count changes
  const resetView = useCallback(() => {
    setZoom(defaultScale(activeBlocks.length));
    setPanX(0);
    setPanY(0);
    setOrbitX(0);
    setOrbitY(0);
  }, [activeBlocks.length]);

  useEffect(() => {
    setZoom(defaultScale(activeBlocks.length));
    setPanX(0);
    setPanY(0);
  }, [activeBlocks.length, activeTurnId]);

  // ─────────────────────────────────────────────────────────────────────── //
  // Trackpad / wheel — Figma-style interaction:                              //
  //   • two-finger swipe → PAN (translate scene)                             //
  //   • pinch (Chrome reports as wheel + ctrlKey) → ZOOM around cursor       //
  //   • Cmd/Ctrl + wheel → ZOOM around cursor                                //
  //   • plain mouse wheel → also pan (vertical) — feels natural on mac       //
  //                                                                          //
  // EXCEPTION: when the cursor is over a scrollable element inside a panel   //
  // (checklist, list, table, code, …) and that element can still scroll in   //
  // the wheel direction, let the browser scroll the content normally.        //
  // ─────────────────────────────────────────────────────────────────────── //
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    /** Walk up from the wheel target — if an ancestor element has its own
     *  scrollable overflow AND can still scroll in the wheel direction,
     *  return true so the panel handles the wheel itself. */
    const wheelTargetIsScrollable = (e: WheelEvent): boolean => {
      let node: HTMLElement | null = e.target as HTMLElement | null;
      while (node && node !== scene) {
        const style = window.getComputedStyle(node);
        const oy = style.overflowY;
        const ox = style.overflowX;
        const canScrollY =
          (oy === "auto" || oy === "scroll") && node.scrollHeight > node.clientHeight;
        const canScrollX =
          (ox === "auto" || ox === "scroll") && node.scrollWidth > node.clientWidth;
        if (canScrollY) {
          // Has remaining scroll space in the wheel direction?
          if (e.deltaY > 0 && node.scrollTop + node.clientHeight < node.scrollHeight - 0.5) return true;
          if (e.deltaY < 0 && node.scrollTop > 0.5) return true;
        }
        if (canScrollX) {
          if (e.deltaX > 0 && node.scrollLeft + node.clientWidth < node.scrollWidth - 0.5) return true;
          if (e.deltaX < 0 && node.scrollLeft > 0.5) return true;
        }
        node = node.parentElement;
      }
      return false;
    };

    const onWheel = (e: WheelEvent) => {
      const isPinch = e.ctrlKey; // Chrome trackpad pinch reports ctrlKey=true
      const isCmdScroll = e.metaKey;
      const isZoomGesture = isPinch || isCmdScroll;

      // Pinch / Cmd-scroll always zooms the canvas, even over panel content.
      if (isZoomGesture) {
        e.preventDefault();
        const rect = scene.getBoundingClientRect();
        const cursorX = e.clientX - rect.left - rect.width / 2;
        const cursorY = e.clientY - rect.top - rect.height / 2;
        // Pinch deltas are tiny (~3-30); Cmd+wheel deltas are larger (~100)
        const sensitivity = isPinch ? 0.012 : 0.0025;
        const factor = Math.exp(-e.deltaY * sensitivity);

        setZoom((prevZoom) => {
          const nextZoom = Math.max(0.25, Math.min(3, prevZoom * factor));
          const ratio = nextZoom / prevZoom;
          // Adjust pan so the point under cursor stays put
          setPanX((prevPanX) => cursorX - (cursorX - prevPanX) * ratio);
          setPanY((prevPanY) => cursorY - (cursorY - prevPanY) * ratio);
          return nextZoom;
        });
        return;
      }

      // Plain wheel/swipe: if the cursor is over scrollable panel content,
      // let the browser scroll it natively (don't preventDefault, don't pan).
      if (wheelTargetIsScrollable(e)) return;

      // Otherwise, two-finger swipe / mouse wheel pans the scene.
      e.preventDefault();
      setPanX((prev) => prev - e.deltaX);
      setPanY((prev) => prev - e.deltaY);
    };

    scene.addEventListener("wheel", onWheel, { passive: false });
    return () => scene.removeEventListener("wheel", onWheel);
  }, []);

  // Keyboard shortcuts: + / - / 0 / 1 / arrows
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Skip when user is typing in an input/textarea
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;

      if ((e.metaKey || e.ctrlKey) && (e.key === "=" || e.key === "+")) {
        e.preventDefault();
        setZoom((p) => Math.min(3, p * 1.15));
      } else if ((e.metaKey || e.ctrlKey) && e.key === "-") {
        e.preventDefault();
        setZoom((p) => Math.max(0.25, p / 1.15));
      } else if (e.key === "0" && !e.metaKey && !e.ctrlKey) {
        setZoom(1);
        setPanX(0); setPanY(0);
      } else if (e.key === "1" && !e.metaKey && !e.ctrlKey) {
        resetView();
      } else if (e.key === "ArrowLeft") {
        setPanX((p) => p + 30);
      } else if (e.key === "ArrowRight") {
        setPanX((p) => p - 30);
      } else if (e.key === "ArrowUp") {
        setPanY((p) => p + 30);
      } else if (e.key === "ArrowDown") {
        setPanY((p) => p - 30);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [resetView]);

  // ─────────────────────────────────────────────────────────────────────── //
  // runFixture — offline path used when LLM is unavailable.                  //
  // Simulates a realistic agent run: trace steps stream in with the same     //
  // cadence as a real LLM (recall_memory → select_skill → ... → llm_gen     //
  // with heartbeat → render). The user sees identical UX, just from a       //
  // pre-recorded JSON spec.                                                  //
  // ─────────────────────────────────────────────────────────────────────── //
  const runFixture = useCallback(async (inputGoal: string, fixturePath: string) => {
    if (isGenerating) return;
    setIsGenerating(true);
    setError(null);
    setStreamLines([]);
    setStreamCollapsed(false);
    setHeartbeatText("");
    setElapsedSec(0);
    setOrbitY(0);
    setOrbitX(0);
    setZoom(1.0);
    setPanX(0);
    setPanY(0);

    const startTime = Date.now();
    const ts = () => new Date().toLocaleTimeString("en-US", { hour12: false });
    // Tick the elapsed counter
    const tickerId = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startTime) / 1000));
    }, 200);

    try {
      // Phase 1: bootstrap context (~300ms)
      pushLine(`[${ts()}] ◆ Initializing Tilo runtime...`);
      await new Promise((r) => setTimeout(r, 320));
      pushLine(`[${ts()}] → fetching workspace context`);
      await new Promise((r) => setTimeout(r, 250));
      pushLine(`[${ts()}] ✓ workspace=Tilo Demo Workspace agent=Tilo Agent`, "ok");
      pushLine(`[${ts()}] ◆ Dispatching task: "${inputGoal.slice(0, 60)}${inputGoal.length > 60 ? "..." : ""}"`);
      await new Promise((r) => setTimeout(r, 200));
      pushLine(`[${ts()}] → Run started · run_id=demo-fixture · streaming trace`, "ok");

      // Phase 2: simulated trace steps (matches real agent runtime ordering)
      const simulatedSteps: Array<{ type: string; title: string; summary?: string; delay: number }> = [
        { type: "recall_memory",      title: "Recall memory",        summary: "Found 0 prior preferences", delay: 600 },
        { type: "select_skill",       title: "Select skills",        summary: "Matched skill: trip_planning", delay: 500 },
        { type: "build_prompt",       title: "Build prompt context", summary: "1.3KB system + 0.4KB user", delay: 400 },
        { type: "plan",               title: "Build execution plan", summary: "4 steps — recall→tool→llm→artifact", delay: 350 },
        { type: "invoke_tool",        title: "Invoke Mock Search",   summary: "destinations + hotels + activities", delay: 800 },
      ];
      for (const step of simulatedSteps) {
        await new Promise((r) => setTimeout(r, step.delay));
        pushLine(`[${ts()}] ✓ ${step.type.padEnd(20)} ${step.title}`, "ok");
        if (step.summary) pushLine(`         ${step.summary}`, "info");
      }

      // Phase 3: simulated LLM thinking with heartbeat (~6s — what users
      // expect from a real run, but using the cached spec)
      pushLine(`[${ts()}] ◌ llm_generation       Calling tencent · deepseek-v4-flash`, "info");
      const thinkingDuration = 6000;
      const heartbeatStart = Date.now();
      while (Date.now() - heartbeatStart < thinkingDuration) {
        const elapsed = Math.floor((Date.now() - heartbeatStart) / 800);
        setHeartbeatText(HEARTBEAT_MESSAGES[elapsed % HEARTBEAT_MESSAGES.length]);
        await new Promise((r) => setTimeout(r, 250));
      }
      setHeartbeatText("");
      pushLine(`[${ts()}] ✓ llm_generation       Calling tencent · deepseek-v4-flash`, "ok");
      pushLine(`         Mode=cached; type=trip_planning.`, "info");
      pushLine(`[${ts()}] ✓ generate_artifact    Generate artifact`, "ok");
      pushLine(`[${ts()}] ◆ Generation mode: CACHED`, "warn");

      // Phase 4: load + animate the spec
      pushLine(`[${ts()}] → Materializing AIP spec...`);
      const spec: AIPSpec = await fetch(fixturePath).then((r) => r.json());
      const allBlocks = asArray<AIPBlock>(spec.blocks);
      pushLine(`[${ts()}] ✓ Spec received · ${allBlocks.length} blocks · ${asArray(spec.views).length} views`, "ok");

      const newTurnId = `turn-fixture-${Date.now()}`;
      const newTurn: Turn = {
        id: newTurnId,
        goal: inputGoal,
        spec_title: spec.title,
        blocks: [],
        follow_ups: asArray<string>(spec.follow_ups),
        generation_mode: "cached",
        created_at: Date.now(),
        measured_heights: {},
      };
      setTurns((prev) => {
        const next = [...prev, newTurn];
        return next.length > MAX_TURNS ? next.slice(next.length - MAX_TURNS) : next;
      });
      setActiveTurnId(newTurnId);

      for (let i = 0; i < allBlocks.length; i++) {
        await new Promise((r) => setTimeout(r, 180));
        const b = allBlocks[i];
        pushLine(`         ▸ rendering block[${i}]: ${b.type} → ${asString(b.title) || b.id}`, "info");
        setTurns((prev) => prev.map((t) =>
          t.id === newTurnId ? { ...t, blocks: [...t.blocks, b] } : t
        ));
      }

      pushLine(`[${ts()}] ◆ Render complete · all panels interactive`, "ok");
      setTimeout(() => setStreamCollapsed(true), 2500);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Fixture load failed";
      pushLine(`[${ts()}] ✗ ERROR: ${errMsg}`, "warn");
      setError(errMsg);
    } finally {
      clearInterval(tickerId);
      setIsGenerating(false);
      setHeartbeatText("");
    }
  }, [isGenerating, pushLine]);

  const generate = useCallback(async (inputGoal: string) => {
    if (!inputGoal.trim() || isGenerating) return;
    setIsGenerating(true);
    setError(null);
    setStreamLines([]);
    setStreamCollapsed(false);
    setHeartbeatText("");
    setElapsedSec(0);
    setOrbitY(0);
    setOrbitX(0);
    setZoom(1.0);
    setPanX(0);
    setPanY(0);

    const startTime = Date.now();
    const ts = () => new Date().toLocaleTimeString("en-US", { hour12: false });
    pushLine(`[${ts()}] ◆ Initializing Tilo runtime...`);

    try {
      pushLine(`[${ts()}] → fetching workspace context`);
      const bootstrap = await fetch(`${API_BASE}/api/bootstrap`).then((r) => r.json());
      const ws = bootstrap.workspace;
      const proj = bootstrap.projects?.[0];
      const agent = bootstrap.agents?.[0];
      if (!ws) throw new Error("No workspace found");
      pushLine(`[${ts()}] ✓ workspace=${ws.name?.slice(0, 30)} agent=${agent?.name?.slice(0, 30)}`, "ok");

      pushLine(`[${ts()}] ◆ Dispatching task: "${inputGoal.slice(0, 60)}${inputGoal.length > 60 ? "..." : ""}"`);

      const msg = await fetch(`${API_BASE}/api/messages/async`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: ws.id,
          project_id: proj?.id,
          agent_id: agent?.id,
          content: inputGoal,
          attachments: [],
        }),
      }).then((r) => r.json());

      pushLine(`[${ts()}] → Run started · run_id=${msg.run_id.slice(0, 8)} · streaming trace`, "ok");

      const seenStepIds = new Set<string>();
      const interestingTypes = new Set([
        "recall_memory", "select_skill", "build_prompt", "plan",
        "invoke_tool", "llm_generation", "generate_artifact",
        "extract_memory_candidates",
      ]);
      let lastStatus = "queued";
      let pollCount = 0;
      const maxPolls = 360;
      let runFinished = false;
      let llmStartTime: number | null = null;

      while (pollCount < maxPolls && !runFinished) {
        pollCount += 1;
        await new Promise((resolve) => setTimeout(resolve, 500));
        setElapsedSec(Math.floor((Date.now() - startTime) / 1000));

        let runStatus: { status: string } | null = null;
        try {
          runStatus = await fetch(`${API_BASE}/api/runs/${msg.run_id}`).then((r) => r.json());
        } catch { /* network blip */ }

        const trace: TraceStep[] = await fetch(`${API_BASE}/api/runs/${msg.run_id}/trace`)
          .then((r) => r.json())
          .catch(() => []);

        const llmStep = trace.find((s) => s.step_type === "llm_generation");
        if (llmStep && llmStep.status === "running" && llmStartTime === null) {
          llmStartTime = Date.now();
          setHeartbeatText("LLM is composing artifact spec");
        } else if (llmStep && llmStep.status !== "running" && llmStartTime !== null) {
          setHeartbeatText("");
          llmStartTime = null;
        }
        if (llmStartTime !== null) {
          const elapsed = Math.floor((Date.now() - llmStartTime) / 3000);
          setHeartbeatText(HEARTBEAT_MESSAGES[elapsed % HEARTBEAT_MESSAGES.length]);
        }

        for (const step of trace) {
          if (seenStepIds.has(step.id)) continue;
          if (!interestingTypes.has(step.step_type)) {
            seenStepIds.add(step.id);
            continue;
          }
          if (step.status === "running") continue;
          seenStepIds.add(step.id);
          const icon = step.status === "completed" ? "✓" : step.status === "failed" ? "✗" : "◌";
          const kind: StreamLine["kind"] = step.status === "completed" ? "ok" : step.status === "failed" ? "warn" : "info";
          pushLine(`[${ts()}] ${icon} ${step.step_type.padEnd(20)} ${step.title.slice(0, 60)}`, kind);
          if (step.summary && step.summary !== step.title) {
            pushLine(`         ${step.summary.slice(0, 80)}`, "info");
          }
        }

        if (runStatus?.status && runStatus.status !== lastStatus) {
          lastStatus = runStatus.status;
        }
        if (runStatus?.status === "completed" || runStatus?.status === "failed") {
          runFinished = true;
          break;
        }
      }

      setHeartbeatText("");
      if (!runFinished) throw new Error("Run timeout (180s ceiling)");
      if (lastStatus === "failed") throw new Error("Run failed — see backend logs");

      const finalTrace: TraceStep[] = await fetch(`${API_BASE}/api/runs/${msg.run_id}/trace`).then((r) => r.json());
      const llmStep = finalTrace.find((s) => s.step_type === "llm_generation");
      const llmStepWithMode = llmStep as TraceStep & { output_json?: { runtime_mode?: string } };
      const mode = llmStepWithMode?.output_json?.runtime_mode ?? "deterministic";
      pushLine(`[${ts()}] ◆ Generation mode: ${mode.toUpperCase()}`, mode === "llm" ? "ok" : "warn");

      pushLine(`[${ts()}] → Materializing AIP spec...`);
      const artifacts = await fetch(
        `${API_BASE}/api/artifacts?workspace_id=${ws.id}&task_id=${msg.task_id}`
      ).then((r) => r.json());

      const artifact = artifacts[0];
      if (!artifact) throw new Error("No artifact generated");

      const spec: AIPSpec = artifact.schema_json;
      const allBlocks = asArray<AIPBlock>(spec.blocks);
      pushLine(`[${ts()}] ✓ Spec received · ${allBlocks.length} blocks · ${asArray(spec.views).length} views`, "ok");

      // Create a new turn (push older turns back in z-space).
      const newTurnId = `turn-${msg.run_id}`;
      const newTurn: Turn = {
        id: newTurnId,
        goal: inputGoal,
        spec_title: spec.title,
        blocks: [],
        follow_ups: asArray<string>(spec.follow_ups),
        generation_mode: mode,
        created_at: Date.now(),
        measured_heights: {},
      };
      setTurns((prev) => {
        // Keep latest MAX_TURNS only — drop the very oldest if over
        const next = [...prev, newTurn];
        if (next.length > MAX_TURNS) return next.slice(next.length - MAX_TURNS);
        return next;
      });
      setActiveTurnId(newTurnId);

      // Animate blocks into the new turn one by one
      for (let i = 0; i < allBlocks.length; i++) {
        await new Promise((resolve) => setTimeout(resolve, 180));
        const b = allBlocks[i];
        pushLine(`         ▸ rendering block[${i}]: ${b.type} → ${asString(b.title) || b.id}`, "info");
        setTurns((prev) => prev.map((t) =>
          t.id === newTurnId ? { ...t, blocks: [...t.blocks, b] } : t
        ));
      }

      pushLine(`[${ts()}] ◆ Render complete · all panels interactive`, "ok");
      setTimeout(() => setStreamCollapsed(true), 2500);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Generation failed";
      pushLine(`[${ts()}] ✗ ERROR: ${errMsg}`, "warn");
      setError(errMsg);
    } finally {
      setIsGenerating(false);
      setHeartbeatText("");
    }
  }, [isGenerating, pushLine]);

  // ─────────────────────────────────────────────────────────────────────── //
  // Mouse drag — pan by default, Shift+drag for 3D orbit                     //
  // ─────────────────────────────────────────────────────────────────────── //
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.closest(".cx-panel") || target.closest(".cx-stream")) return;
    setDragMode(e.shiftKey ? "orbit" : "pan");
    setDragStart({ x: e.clientX, y: e.clientY });
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragMode === "none") return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    if (dragMode === "pan") {
      setPanX((prev) => prev + dx);
      setPanY((prev) => prev + dy);
    } else if (dragMode === "orbit") {
      setOrbitY((prev) => prev + dx * 0.3);
      setOrbitX((prev) => Math.max(-30, Math.min(30, prev + dy * 0.15)));
    }
    setDragStart({ x: e.clientX, y: e.clientY });
  }, [dragMode, dragStart]);

  const handleMouseUp = useCallback(() => setDragMode("none"), []);

  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.closest(".cx-panel") || target.closest(".cx-stream")) return;
    resetView();
  }, [resetView]);

  return (
    <div className="cx-page">
      <header className="cx-header">
        <div className="cx-header-left">
          <div className="cx-brand">
            <span className="cx-brand-mark">◈</span>
            <span className="cx-brand-name">Tilo</span>
          </div>
          <div className="cx-tagline">
            <span className="cx-tagline-main">Agent output → Interactive UI</span>
            <span className="cx-tagline-sub">live trace · structured artifact · human-in-the-loop</span>
          </div>
          {generationMode && (
            <span className={`cx-mode ${generationMode}`}>
              {generationMode === "llm" ? "⚡ LLM" : generationMode === "cached" ? "◆ Cached" : "◆ Deterministic"}
            </span>
          )}
        </div>
        <div className="cx-header-right">
          {specTitle && <span className="cx-spec-title">{specTitle}</span>}
          {activeBlocks.length > 0 && (
            <span className="cx-zoom-badge" onClick={resetView} title="Click to fit (or press 1)">
              ⌖ {Math.round(zoom * 100)}%
            </span>
          )}
          <ShortcutsHint />
        </div>
      </header>

      <div
        ref={sceneRef}
        className={`cx-scene ${dragMode === "pan" ? "panning" : dragMode === "orbit" ? "orbiting" : ""}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onDoubleClick={handleDoubleClick}
      >
        <div
          className="cx-orbit"
          style={{
            transform: `translate3d(${panX}px, ${panY}px, 0) scale(${zoom}) rotateX(${orbitX}deg) rotateY(${orbitY}deg)`,
          }}
        >
          {turns.map((turn) => {
            // Distance from active turn (0 = front, 1 = one back, …)
            const activeIdx = turns.findIndex((t) => t.id === (activeTurnId ?? turns[turns.length - 1]?.id));
            const turnIdx = turns.findIndex((t) => t.id === turn.id);
            const depth = activeIdx - turnIdx; // 0 means front; positive = older
            const isActive = depth === 0;
            const z = -Math.abs(depth) * TURN_DEPTH_STEP;
            const opacity = depth === 0 ? 1 : Math.max(0.08, Math.pow(TURN_OPACITY_FACTOR, Math.abs(depth)));
            const layouts = computeMasonryLayout(turn.blocks, turn.measured_heights);

            return (
              <div
                key={turn.id}
                className={`cx-turn ${isActive ? "active" : "archived"}`}
                style={{
                  transform: `translate3d(0, 0, ${z}px)`,
                  opacity,
                  pointerEvents: isActive ? "auto" : "none",
                }}
                onClick={() => { if (!isActive) setActiveTurnId(turn.id); }}
              >
                {turn.blocks.map((block, index) => {
                  const layout = layouts[index];
                  const hasMeasured = turn.measured_heights[block.id] != null;
                  return (
                    <Panel
                      key={`${turn.id}-${block.id}`}
                      block={block}
                      layout={layout}
                      hasMeasured={hasMeasured}
                      animationDelay={index * 60}
                      onMeasured={(h) => {
                        if (turn.measured_heights[block.id] === h) return;
                        setTurns((prev) => prev.map((t) =>
                          t.id === turn.id
                            ? { ...t, measured_heights: { ...t.measured_heights, [block.id]: h } }
                            : t
                        ));
                      }}
                    />
                  );
                })}
              </div>
            );
          })}
        </div>

        {turns.length === 0 && !isGenerating && (
          <div className="cx-empty">
            <div className="cx-empty-icon">◎</div>
            <div className="cx-empty-text">
              <strong>Watch your agent build a UI, not a chat reply.</strong>
              <span>
                Type a goal — Tilo turns the agent&apos;s output into structured, interactive blocks
                with a live trace, human confirmation, and durable memory.
              </span>
              <span className="cx-empty-hint">Try one of the quick-start samples below ↓</span>
            </div>
          </div>
        )}

        {/* Turn timeline navigator (left side) */}
        {turns.length > 0 && (
          <TurnNavigator
            turns={turns}
            activeTurnId={activeTurnId ?? turns[turns.length - 1]?.id ?? null}
            onSelect={(id) => setActiveTurnId(id)}
          />
        )}

        {streamLines.length > 0 && (
          <div className={`cx-stream ${streamCollapsed ? "collapsed" : ""}`}>
            <div className="cx-stream-head" onClick={() => setStreamCollapsed(!streamCollapsed)}>
              <span className={`cx-stream-dot ${isGenerating ? "live" : ""}`} />
              <span className="cx-stream-title">AGENT TRACE</span>
              <span className="cx-stream-meta">
                {isGenerating ? `● streaming · ${elapsedSec}s` : `◆ ${streamLines.length} events`}
              </span>
              <span className="cx-stream-toggle">{streamCollapsed ? "▴" : "▾"}</span>
            </div>
            {!streamCollapsed && (
              <div className="cx-stream-body" ref={streamRef}>
                {streamLines.map((line) => (
                  <div key={line.id} className={`cx-stream-line ${line.kind}`}>
                    {line.text}
                  </div>
                ))}
                {isGenerating && (
                  <div className="cx-stream-heartbeat">
                    <HeartbeatIndicator text={heartbeatText} />
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <footer className="cx-footer">
        {followUps.length > 0 && (
          <div className="cx-followups">
            <span className="cx-followups-label">Suggested next:</span>
            {followUps.map((q) => (
              <button key={q} className="cx-chip" onClick={() => { setGoal(q); void generate(q); }} disabled={isGenerating}>
                {q}
              </button>
            ))}
          </div>
        )}
        <div className="cx-input-row">
          <span className="cx-prompt-glyph">{">"}</span>
          <input
            className="cx-input"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") void generate(goal); }}
            placeholder="Describe a task for the agent..."
            disabled={isGenerating}
          />
          <button
            className="cx-send"
            onClick={() => void generate(goal)}
            disabled={isGenerating || !goal.trim()}
          >
            {isGenerating ? `PROCESSING ${elapsedSec}s...` : "EXECUTE →"}
          </button>
        </div>
        <div className="cx-samples">
          <span className="cx-samples-label">
            Quick start:
            {llmAvailable === false && <span className="cx-offline-badge"> · offline mode (cached)</span>}
          </span>
          {SAMPLE_GOALS
            .filter((sample) => llmAvailable !== false || !sample.requiresLLM)
            .map((sample) => (
              <button
                key={sample.label}
                className="cx-sample"
                onClick={() => {
                  setGoal(sample.goal);
                  if (sample.fixturePath && llmAvailable === false) {
                    void runFixture(sample.goal, sample.fixturePath);
                  } else {
                    void generate(sample.goal);
                  }
                }}
                disabled={isGenerating}
                style={{ "--accent": sample.color } as React.CSSProperties}
              >
                <span className="cx-sample-icon">{sample.icon}</span>
                <span>{sample.label}</span>
              </button>
            ))}
        </div>
        {error && <div className="cx-error">⚠ {error}</div>}
      </footer>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────── //
// Panel — measures its own height with ResizeObserver and reports back        //
// so the masonry layout can pack columns without overlap                      //
// ─────────────────────────────────────────────────────────────────────────── //

function Panel({
  block,
  layout,
  hasMeasured,
  animationDelay,
  onMeasured,
}: {
  block: AIPBlock;
  layout: PanelLayout | undefined;
  hasMeasured: boolean;
  animationDelay: number;
  onMeasured: (height: number) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const h = entry.contentRect.height;
        if (h > 0) onMeasured(h);
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [onMeasured]);

  const x = layout?.x ?? 0;
  const y = layout?.y ?? 0;
  const z = layout?.z ?? 0;
  const w = layout?.width ?? panelWidthFor(block.type);

  return (
    <div
      ref={ref}
      className={`cx-panel ${hasMeasured ? "appear" : "measuring"}`}
      style={{
        transform: `translate3d(${x}px, ${y}px, ${z}px) translate(-50%, -50%)`,
        width: w,
        animationDelay: `${animationDelay}ms`,
      }}
    >
      <div className="cx-panel-head">
        <span className="cx-panel-type">{block.type}</span>
        <span className="cx-panel-title">{asString(block.title) || block.id}</span>
      </div>
      <div className="cx-panel-body">
        <BlockContent block={block} />
      </div>
      {block.actions && block.actions.length > 0 && (
        <div className="cx-panel-actions">
          {block.actions.map((action) => (
            <button key={action.id} className="cx-btn small">{action.label}</button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────── //
// TurnNavigator — left-side timeline letting the user jump between turns      //
// ─────────────────────────────────────────────────────────────────────────── //

function TurnNavigator({
  turns,
  activeTurnId,
  onSelect,
}: {
  turns: Turn[];
  activeTurnId: string | null;
  onSelect: (id: string) => void;
}) {
  if (turns.length <= 1) return null;
  return (
    <div className="cx-turns">
      <div className="cx-turns-label">TIMELINE</div>
      {turns.map((turn, i) => {
        const isActive = turn.id === activeTurnId;
        const time = new Date(turn.created_at).toLocaleTimeString("en-US", { hour12: false }).slice(0, 5);
        return (
          <button
            key={turn.id}
            className={`cx-turn-pill ${isActive ? "active" : ""}`}
            onClick={() => onSelect(turn.id)}
            title={turn.goal}
          >
            <span className="cx-turn-num">{i + 1}</span>
            <span className="cx-turn-text">
              <span className="cx-turn-title">{turn.spec_title || turn.goal.slice(0, 30)}</span>
              <span className="cx-turn-meta">{time} · {turn.blocks.length} blocks</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

function ShortcutsHint() {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="cx-hint-wrap"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <span className="cx-hint">⌨ shortcuts</span>
      {open && (
        <div className="cx-hint-popup">
          <div className="cx-hint-row"><kbd>two-finger swipe</kbd><span>pan</span></div>
          <div className="cx-hint-row"><kbd>pinch</kbd><span>zoom (around cursor)</span></div>
          <div className="cx-hint-row"><kbd>⌘</kbd>+<kbd>scroll</kbd><span>zoom</span></div>
          <div className="cx-hint-row"><kbd>drag</kbd><span>pan</span></div>
          <div className="cx-hint-row"><kbd>⇧</kbd>+<kbd>drag</kbd><span>3D orbit</span></div>
          <div className="cx-hint-row"><kbd>double-click</kbd><span>fit to view</span></div>
          <div className="cx-hint-row"><kbd>⌘</kbd>+<kbd>=</kbd>/<kbd>−</kbd><span>zoom in/out</span></div>
          <div className="cx-hint-row"><kbd>0</kbd><span>100%</span></div>
          <div className="cx-hint-row"><kbd>1</kbd><span>fit to view</span></div>
          <div className="cx-hint-row"><kbd>← ↑ → ↓</kbd><span>nudge pan</span></div>
        </div>
      )}
    </div>
  );
}

function HeartbeatIndicator({ text }: { text: string }) {
  const [dots, setDots] = useState(".");
  useEffect(() => {
    const id = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "." : prev + "."));
    }, 400);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="cx-heartbeat">
      <span className="cx-heartbeat-pulse" />
      <span className="cx-heartbeat-text">
        {text || "agent is working"}<span className="cx-heartbeat-dots">{dots}</span>
      </span>
    </div>
  );
}
