"use client";

import {
  Bar, BarChart, Cell, Legend, Line, LineChart,
  Pie, PieChart, RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { ArtifactBlock } from "./artifact-types";
import { blockData } from "./artifact-types";

type BlockRenderer = (props: { block: ArtifactBlock }) => JSX.Element;

const CHART_COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#a855f7", "#ec4899"];

// ---------- chart ---------------------------------------------------------- //

function ChartBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const chartType = String(data.chart_type || "bar").toLowerCase();
  const labels = (data.labels as string[]) || [];
  const datasets = (data.datasets as Array<{ label: string; data: number[]; color?: string }>) || [];
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
            <Tooltip /><Legend />
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
            <PolarGrid /><PolarAngleAxis dataKey="name" tick={{ fontSize: 11 }} />
            {datasets.map((d, i) => <Radar key={d.label} name={d.label} dataKey={d.label} stroke={d.color || CHART_COLORS[i]} fill={d.color || CHART_COLORS[i]} fillOpacity={0.25} />)}
            <Tooltip />{datasets.length > 1 && <Legend />}
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
            <XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} width={36} />
            <Tooltip />{datasets.length > 1 && <Legend />}
            {datasets.map((d, i) => <Line key={d.label} type="monotone" dataKey={d.label} stroke={d.color || CHART_COLORS[i]} strokeWidth={2} dot={false} />)}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="w-full h-52">
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
          <XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} width={36} />
          <Tooltip />{datasets.length > 1 && <Legend />}
          {datasets.map((d, i) => <Bar key={d.label} dataKey={d.label} fill={d.color || CHART_COLORS[i]} radius={[3, 3, 0, 0]} />)}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------- diff ----------------------------------------------------------- //

function DiffBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const rawDiff = data.diff as string | undefined;
  const before = data.before as string | undefined;
  const after = data.after as string | undefined;

  if (rawDiff) {
    return (
      <div className="font-mono text-xs overflow-x-auto rounded-md border border-slate-200 bg-slate-50">
        {rawDiff.split("\n").map((line, i) => {
          let cls = "px-3 py-px whitespace-pre ";
          if (line.startsWith("+++") || line.startsWith("---")) cls += "text-slate-500 bg-slate-100";
          else if (line.startsWith("+")) cls += "bg-emerald-50 text-emerald-800";
          else if (line.startsWith("-")) cls += "bg-red-50 text-red-800";
          else if (line.startsWith("@@")) cls += "bg-indigo-50 text-indigo-600";
          else cls += "text-slate-700";
          return <div key={i} className={cls}>{line || " "}</div>;
        })}
      </div>
    );
  }

  if (before !== undefined || after !== undefined) {
    return (
      <div className="grid grid-cols-2 gap-2 font-mono text-xs">
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

  return <FallbackArtifactBlock block={block} />;
}

// ---------- code ----------------------------------------------------------- //

function CodeBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const language = String(data.language || data.lang || "text");
  const code = String(data.code || data.content || "");
  return (
    <div className="rounded-md overflow-hidden border border-slate-200 text-xs">
      <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5">
        <span className="font-mono text-slate-400">{language}</span>
      </div>
      <pre className="bg-slate-900 text-slate-100 font-mono p-4 overflow-x-auto whitespace-pre"><code>{code}</code></pre>
    </div>
  );
}

// ---------- timeline ------------------------------------------------------- //

function TimelineBlock({ block }: { block: ArtifactBlock }) {
  const items = (blockData(block).items as Array<{ time: string; title: string; description?: string }>) || [];
  return (
    <ol className="relative ml-3 border-l border-slate-200 space-y-5">
      {items.map((item, i) => (
        <li key={`${item.time}-${i}`} className="ml-4">
          <div className="absolute -left-[7px] mt-1 h-3.5 w-3.5 rounded-full border-2 border-white bg-indigo-500" />
          <time className="text-xs text-slate-500">{item.time}</time>
          <p className="text-sm font-medium text-slate-900 mt-0.5">{item.title}</p>
          {item.description && <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>}
        </li>
      ))}
    </ol>
  );
}

// ---------- kanban --------------------------------------------------------- //

function KanbanBlock({ block }: { block: ArtifactBlock }) {
  const columns = (blockData(block).columns as Array<{ id: string; title: string; cards: Array<{ id?: string; title: string; description?: string }> }>) || [];
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {columns.map((col) => (
        <div key={col.id} className="min-w-[160px] flex-shrink-0 flex-1 rounded-lg bg-slate-50 border border-slate-200 p-3">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">{col.title}</h4>
          <div className="space-y-2">
            {(col.cards || []).map((card, i) => (
              <div key={card.id || `${col.id}-${i}`} className="rounded-md bg-white border border-slate-200 p-2 shadow-sm">
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

// ---------- tool_preview --------------------------------------------------- //

function ToolPreviewBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const status = String(data.status || "success");
  const isError = status === "error";
  return (
    <section className={`rounded-md border p-3 ${isError ? "border-red-200 bg-red-50" : "border-slate-200 bg-slate-50"}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-semibold text-slate-700">{String(data.tool_name || block.title || "Tool")}</span>
        <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${isError ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"}`}>{status}</span>
      </div>
      {data.output != null && <pre className="mt-1 text-xs text-slate-700 font-mono whitespace-pre-wrap overflow-x-auto">{String(data.output)}</pre>}
    </section>
  );
}

// ---------- memory_card ---------------------------------------------------- //

function MemoryCardBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const content = String(data.content || data.summary || data.text || "");
  const salience = data.salience != null ? Number(data.salience) : null;
  return (
    <section className="rounded-md border border-indigo-200 bg-indigo-50 p-3">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-semibold text-indigo-700">Memory candidate</span>
        {salience !== null && <span className="text-xs text-indigo-400">salience {Math.round(salience * 100)}%</span>}
      </div>
      <p className="text-sm text-indigo-900">{content}</p>
    </section>
  );
}

// ---------- fallback ------------------------------------------------------- //

function FallbackArtifactBlock({ block }: { block: ArtifactBlock }) {
  const data = blockData(block);
  const summary = data.summary || data.content || data.description || block.title || "No preview available.";
  return (
    <section className="rounded-md border border-dashed border-slate-300 bg-slate-50 p-3">
      {block.title && <p className="text-xs font-semibold text-slate-600 mb-0.5">{block.title}</p>}
      <p className="text-xs text-slate-500">{String(summary)}</p>
    </section>
  );
}

// ---------- registry ------------------------------------------------------- //

export const blockRenderers: Record<string, BlockRenderer> = {
  chart: ChartBlock,
  diff: DiffBlock,
  code: CodeBlock,
  timeline: TimelineBlock,
  kanban: KanbanBlock,
  tool_preview: ToolPreviewBlock,
  tool_call_preview: ToolPreviewBlock,
  memory_card: MemoryCardBlock,
  memory_candidate_card: MemoryCardBlock,
};

export function renderArtifactBlock(block: ArtifactBlock): JSX.Element {
  const Renderer = blockRenderers[block.type] || FallbackArtifactBlock;
  return <Renderer block={block} />;
}
