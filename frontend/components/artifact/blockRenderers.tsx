"use client";

import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ArtifactBlock } from "../../lib/types";
import { blockData } from "../../lib/types";

type BlockRenderer = (props: { block: ArtifactBlock }) => JSX.Element;

export const CORE_ARTIFACT_BLOCK_TYPES = ["markdown", "table", "form", "approval_card", "risk_panel", "metric", "list"] as const;

export const EXTENSION_ARTIFACT_BLOCK_TYPES = [
  "rich_text",
  "card",
  "risk_summary",
  "risk_review_panel",
  "metric_dashboard",
  "memory_candidate_card",
  "tool_call_preview",
  "action_queue",
  "editable_document_preview",
  "editable_document_placeholder",
  "timeline",
  "kanban",
  "risk_item",
  "citation",
  "comparison_matrix",
  "confirmation_action",
  "chart",
  "diff",
  "code",
  "tool_preview",
  "memory_card",
  "confirmation",
] as const;

// --------------------------------------------------------------------------- //
// Palette                                                                      //
// --------------------------------------------------------------------------- //

const CHART_COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#a855f7", "#ec4899"];

// --------------------------------------------------------------------------- //
// Existing blocks (unchanged)                                                  //
// --------------------------------------------------------------------------- //

function MarkdownBlock({ block }: { block: ArtifactBlock }) {
  return <section className="text-block">{String(blockData(block).content || "")}</section>;
}

function CardBlock({ block }: { block: ArtifactBlock }) {
  return (
    <section className="card-block">
      <strong>{String(blockData(block).title || block.title || "Card")}</strong>
      <span>{String(blockData(block).content || "")}</span>
    </section>
  );
}

function RiskItemBlock({ block }: { block: ArtifactBlock }) {
  return (
    <section className="risk-block">
      <div>
        <strong>{String(blockData(block).clause || block.title || "Clause")}</strong>
        <span className={`risk-level ${String(blockData(block).risk_level || "medium")}`}>
          {String(blockData(block).risk_level || "medium")}
        </span>
      </div>
      <p>{String(blockData(block).issue || blockData(block).risk || "")}</p>
      <small>{String(blockData(block).suggested_revision || "")}</small>
    </section>
  );
}

function TableBlock({ block }: { block: ArtifactBlock }) {
  const columns = ((blockData(block).columns as Array<string | { key: string; label: string }>) || []).map((column) =>
    typeof column === "string" ? { key: column, label: column } : column
  );
  const rows = (blockData(block).rows as Array<Record<string, string> | string[]>) || [];
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column, cellIndex) => (
                <td key={column.key}>{Array.isArray(row) ? row[cellIndex] : row[column.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MetricBlock({ block }: { block: ArtifactBlock }) {
  return (
    <section className="metric-block">
      <span>{String(blockData(block).label || block.title || "")}</span>
      <strong>{String(blockData(block).value || "")}</strong>
    </section>
  );
}

function ListBlock({ block }: { block: ArtifactBlock }) {
  const items = (blockData(block).items as string[]) || [];
  return (
    <ul className="artifact-list">
      {items.map((item) => <li key={item}>{item}</li>)}
    </ul>
  );
}

function FormBlock({ block }: { block: ArtifactBlock }) {
  const fields = (blockData(block).fields as Array<{ name?: string; label?: string; type?: string }>) || [];
  return (
    <section className="card-block">
      <strong>{String(block.title || blockData(block).title || "Form")}</strong>
      <div className="artifact-list">
        {fields.length ? fields.map((field, index) => (
          <span key={field.name || `${block.id}-field-${index}`}>{String(field.label || field.name || "Field")} · {String(field.type || "text")}</span>
        )) : <span>No fields declared.</span>}
      </div>
    </section>
  );
}

function RiskPanelBlock({ block }: { block: ArtifactBlock }) {
  const risks = (blockData(block).risks as Array<Record<string, unknown>>) || [];
  return (
    <section className="risk-block">
      <div>
        <strong>{String(block.title || blockData(block).title || "Risk panel")}</strong>
        <span className="risk-level high">{String(blockData(block).status || "review")}</span>
      </div>
      {blockData(block).summary ? <p>{String(blockData(block).summary)}</p> : null}
      {risks.length ? (
        <ul className="artifact-list">
          {risks.slice(0, 4).map((risk, index) => (
            <li key={String(risk.id || index)}>{String(risk.clause || risk.title || "Risk")}: {String(risk.issue || risk.summary || "")}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function ConfirmationActionBlock({ block }: { block: ArtifactBlock }) {
  const actions = (blockData(block).actions as string[]) || [];
  return (
    <section className="confirmation-block">
      <strong>{String(blockData(block).title || blockData(block).label || "Confirmation required")}</strong>
      <span>{actions.length ? actions.join(" / ") : String(blockData(block).risk_level || "review")}</span>
    </section>
  );
}

// --------------------------------------------------------------------------- //
// Chart block — Recharts-powered                                               //
// --------------------------------------------------------------------------- //

function ChartBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const chartType = String(data.chart_type || "bar").toLowerCase();
  const labels = (data.labels as string[]) || [];
  const datasets = (data.datasets as Array<{ label: string; data: number[]; color?: string }>) || [];

  // Normalise to recharts row format: [{name, series1, series2, …}]
  const chartData = labels.map((label, i) => ({
    name: label,
    ...Object.fromEntries(datasets.map((d) => [d.label, d.data[i] ?? 0])),
  }));

  if (chartType === "pie" && datasets.length > 0) {
    const pieData = labels.map((label, i) => ({ name: label, value: datasets[0].data[i] ?? 0 }));
    return (
      <div className="w-full h-52">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name }) => name}>
              {pieData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === "radar" && datasets.length > 0) {
    return (
      <div className="w-full h-52">
        <ResponsiveContainer>
          <RadarChart data={chartData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="name" tick={{ fontSize: 11 }} />
            {datasets.map((d, i) => (
              <Radar key={d.label} name={d.label} dataKey={d.label} stroke={d.color || CHART_COLORS[i]} fill={d.color || CHART_COLORS[i]} fillOpacity={0.25} />
            ))}
            <Tooltip />
            {datasets.length > 1 && <Legend />}
          </RadarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === "line") {
    return (
      <div className="w-full h-52">
        <ResponsiveContainer>
          <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} width={36} />
            <Tooltip />
            {datasets.length > 1 && <Legend />}
            {datasets.map((d, i) => (
              <Line key={d.label} type="monotone" dataKey={d.label} stroke={d.color || CHART_COLORS[i]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Default: bar
  return (
    <div className="w-full h-52">
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} width={36} />
          <Tooltip />
          {datasets.length > 1 && <Legend />}
          {datasets.map((d, i) => (
            <Bar key={d.label} dataKey={d.label} fill={d.color || CHART_COLORS[i]} radius={[3, 3, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Diff block — unified diff or before/after                                    //
// --------------------------------------------------------------------------- //

function DiffBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const rawDiff = data.diff as string | undefined;
  const before = data.before as string | undefined;
  const after = data.after as string | undefined;

  if (rawDiff) {
    const lines = rawDiff.split("\n");
    return (
      <div className="font-mono text-xs overflow-x-auto rounded-md border border-slate-200 bg-slate-50">
        {lines.map((line, i) => {
          let cls = "px-3 py-px whitespace-pre ";
          if (line.startsWith("+++") || line.startsWith("---")) cls += "text-slate-500 bg-slate-100";
          else if (line.startsWith("+")) cls += "bg-emerald-50 text-emerald-800";
          else if (line.startsWith("-")) cls += "bg-red-50 text-red-800";
          else if (line.startsWith("@@")) cls += "bg-indigo-50 text-indigo-600";
          else cls += "text-slate-700";
          return <div key={i} className={cls}>{line || " "}</div>;
        })}
      </div>
    );
  }

  if (before !== undefined || after !== undefined) {
    return (
      <div className="grid grid-cols-2 gap-2 font-mono text-xs overflow-x-auto">
        <div className="rounded-md border border-red-200 overflow-hidden">
          <div className="px-3 py-1 bg-red-100 text-red-700 font-semibold border-b border-red-200">Before</div>
          <pre className="p-3 bg-red-50 text-red-900 overflow-x-auto whitespace-pre-wrap">{String(before ?? "")}</pre>
        </div>
        <div className="rounded-md border border-emerald-200 overflow-hidden">
          <div className="px-3 py-1 bg-emerald-100 text-emerald-700 font-semibold border-b border-emerald-200">After</div>
          <pre className="p-3 bg-emerald-50 text-emerald-900 overflow-x-auto whitespace-pre-wrap">{String(after ?? "")}</pre>
        </div>
      </div>
    );
  }

  return <ExtensionFallbackBlock block={block} />;
}

// --------------------------------------------------------------------------- //
// Code block — syntax-highlighted (language label + monospace)                 //
// --------------------------------------------------------------------------- //

function CodeBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const language = String(data.language || data.lang || "text");
  const code = String(data.code || data.content || "");
  return (
    <div className="rounded-md overflow-hidden border border-slate-200 text-xs">
      <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5">
        <span className="font-mono text-slate-400">{language}</span>
      </div>
      <pre className="bg-slate-900 text-slate-100 font-mono p-4 overflow-x-auto whitespace-pre">
        <code>{code}</code>
      </pre>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Timeline block — vertical with dots                                          //
// --------------------------------------------------------------------------- //

function TimelineBlock({ block }: { block: ArtifactBlock }) {
  const items = (blockData(block).items as Array<{ time: string; title: string; description?: string; status?: string }>) || [];
  return (
    <ol className="relative ml-3 border-l border-slate-200 space-y-5">
      {items.map((item, index) => (
        <li key={`${item.time}-${index}`} className="ml-4">
          <div className="absolute -left-[7px] mt-1 h-3.5 w-3.5 rounded-full border-2 border-white bg-indigo-500" />
          <time className="text-xs text-slate-500">{item.time}</time>
          <p className="text-sm font-medium text-slate-900 mt-0.5">{item.title}</p>
          {item.description && <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>}
        </li>
      ))}
    </ol>
  );
}

// --------------------------------------------------------------------------- //
// Kanban block — horizontal columns                                            //
// --------------------------------------------------------------------------- //

function KanbanBlock({ block }: { block: ArtifactBlock }) {
  const columns = (blockData(block).columns as Array<{ id: string; title: string; cards: Array<{ id?: string; title: string; description?: string }> }>) || [];
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {columns.map((column) => (
        <div key={column.id} className="min-w-[160px] flex-shrink-0 flex-1 rounded-lg bg-slate-50 border border-slate-200 p-3">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">{column.title}</h4>
          <div className="space-y-2">
            {(column.cards || []).map((card, i) => (
              <div key={card.id || `${column.id}-${i}`} className="rounded-md bg-white border border-slate-200 p-2 shadow-sm">
                <p className="text-xs font-medium text-slate-800">{card.title}</p>
                {card.description && <p className="text-xs text-slate-500 mt-0.5">{card.description}</p>}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Tool preview block                                                           //
// --------------------------------------------------------------------------- //

function ToolPreviewBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const status = String(data.status || "success");
  const isError = status === "error";
  return (
    <section className={`rounded-md border p-3 ${isError ? "border-red-200 bg-red-50" : "border-slate-200 bg-slate-50"}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-semibold text-slate-700">{String(data.tool_name || block.title || "Tool")}</span>
        <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${isError ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"}`}>
          {status}
        </span>
      </div>
      {data.output != null && (
        <pre className="mt-1 text-xs text-slate-700 font-mono whitespace-pre-wrap overflow-x-auto">{String(data.output)}</pre>
      )}
    </section>
  );
}

// --------------------------------------------------------------------------- //
// Memory card block                                                            //
// --------------------------------------------------------------------------- //

function MemoryCardBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const content = String(data.content || data.summary || data.text || "");
  const salience = data.salience != null ? Number(data.salience) : null;
  return (
    <section className="rounded-md border border-indigo-200 bg-indigo-50 p-3">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-semibold text-indigo-700">Memory candidate</span>
        {salience !== null && (
          <span className="text-xs text-indigo-400">salience {Math.round(salience * 100)}%</span>
        )}
      </div>
      <p className="text-sm text-indigo-900">{content}</p>
    </section>
  );
}

// --------------------------------------------------------------------------- //
// Fallback                                                                     //
// --------------------------------------------------------------------------- //

function ExtensionFallbackBlock({ block }: { block: ArtifactBlock }) {
  const summary = blockData(block).summary || blockData(block).content || blockData(block).description || block.title || "This extension block has no compact summary.";
  return (
    <section className="unsupported-block">
      <strong>{String(block.title || "Extension block")}</strong>
      <span>{block.type}</span>
      <small>{String(summary)}</small>
    </section>
  );
}

// --------------------------------------------------------------------------- //
// Registry                                                                     //
// --------------------------------------------------------------------------- //

export const blockRenderers: Record<string, BlockRenderer> = {
  // Core text & data
  markdown: MarkdownBlock,
  rich_text: MarkdownBlock,
  card: CardBlock,
  approval_card: CardBlock,
  form: FormBlock,
  risk_panel: RiskPanelBlock,
  risk_item: RiskItemBlock,
  table: TableBlock,
  comparison_matrix: TableBlock,
  metric: MetricBlock,
  list: ListBlock,
  // New rich blocks
  chart: ChartBlock,
  diff: DiffBlock,
  code: CodeBlock,
  timeline: TimelineBlock,
  kanban: KanbanBlock,
  tool_preview: ToolPreviewBlock,
  tool_call_preview: ToolPreviewBlock,
  memory_card: MemoryCardBlock,
  memory_candidate_card: MemoryCardBlock,
  // Confirmations
  confirmation: ConfirmationActionBlock,
  confirmation_action: ConfirmationActionBlock,
};

export function renderArtifactBlock(block: ArtifactBlock) {
  const Renderer = blockRenderers[block.type] || ExtensionFallbackBlock;
  return <Renderer block={block} />;
}
