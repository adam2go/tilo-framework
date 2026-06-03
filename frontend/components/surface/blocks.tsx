"use client";

import { useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  CheckCircle2,
  Circle,
  ExternalLink,
  FileText,
  ListChecks,
  Loader2,
  Pencil,
  X,
} from "lucide-react";
import type { BlockProps } from "./types";
import type { ProgressState, Severity } from "../../lib/surface";

// --------------------------------------------------------------------------- //
// Severity → tailwind class helper                                             //
// --------------------------------------------------------------------------- //

function severityClass(severity?: Severity | null): string {
  switch (severity) {
    case "high":
      return "border-red-300 bg-red-50 text-red-900";
    case "medium":
      return "border-amber-300 bg-amber-50 text-amber-900";
    case "low":
      return "border-emerald-300 bg-emerald-50 text-emerald-900";
    case "info":
    default:
      return "border-slate-200 bg-white text-slate-800";
  }
}

function severityIcon(severity?: Severity | null) {
  if (severity === "high") return <AlertTriangle size={16} className="text-red-600" />;
  if (severity === "medium") return <AlertTriangle size={16} className="text-amber-600" />;
  if (severity === "low") return <CheckCircle2 size={16} className="text-emerald-600" />;
  return null;
}

// --------------------------------------------------------------------------- //
// Heading                                                                      //
// --------------------------------------------------------------------------- //

export function HeadingBlock({ block }: BlockProps<"heading">): JSX.Element {
  const { text, severity } = block.data;
  return (
    <header className={`flex items-center gap-2 rounded-md border px-3 py-2 ${severityClass(severity)}`}>
      {severityIcon(severity)}
      <h3 className="text-base font-semibold leading-tight">{text}</h3>
    </header>
  );
}

// --------------------------------------------------------------------------- //
// Text                                                                         //
// --------------------------------------------------------------------------- //

export function TextBlock({ block }: BlockProps<"text">): JSX.Element {
  return (
    <p className="px-1 text-sm leading-relaxed text-slate-700 whitespace-pre-wrap">
      {block.data.content}
    </p>
  );
}

// --------------------------------------------------------------------------- //
// Evidence                                                                     //
// --------------------------------------------------------------------------- //

export function EvidenceBlock({ block }: BlockProps<"evidence">): JSX.Element {
  const { excerpt, source_label, source_ref } = block.data;
  return (
    <figure className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
      <blockquote className="text-sm italic leading-relaxed text-slate-700">
        “{excerpt}”
      </blockquote>
      <figcaption className="mt-1 flex items-center gap-1 text-xs text-slate-500">
        <FileText size={12} />
        {source_label || source_ref}
      </figcaption>
    </figure>
  );
}

// --------------------------------------------------------------------------- //
// Comparison                                                                   //
// --------------------------------------------------------------------------- //

export function ComparisonBlock({ block }: BlockProps<"comparison">): JSX.Element {
  const data = block.data;
  if (data.shape === "side_by_side" && data.left && data.right) {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div className={`rounded-md border px-3 py-2 ${severityClass(data.left.severity)}`}>
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {data.left.label}
          </div>
          <div className="mt-1 text-sm font-semibold">{data.left.value}</div>
        </div>
        <div className={`rounded-md border px-3 py-2 ${severityClass(data.right.severity)}`}>
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {data.right.label}
          </div>
          <div className="mt-1 text-sm font-semibold">{data.right.value}</div>
        </div>
      </div>
    );
  }
  return (
    <table className="w-full overflow-hidden rounded-md border border-slate-200 text-sm">
      <thead className="bg-slate-100 text-slate-600">
        <tr>
          <th className="px-3 py-1.5 text-left font-medium"></th>
          <th className="px-3 py-1.5 text-left font-medium">Left</th>
          <th className="px-3 py-1.5 text-left font-medium">Right</th>
        </tr>
      </thead>
      <tbody>
        {data.rows.map((row) => (
          <tr key={row.label} className={severityClass(row.severity)}>
            <td className="px-3 py-1.5 font-medium">{row.label}</td>
            <td className="px-3 py-1.5">{row.left}</td>
            <td className="px-3 py-1.5">{row.right}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// --------------------------------------------------------------------------- //
// Decision                                                                     //
// --------------------------------------------------------------------------- //

export function DecisionBlock({ block, fire }: BlockProps<"decision">): JSX.Element {
  const [pending, setPending] = useState<string | null>(null);
  const { prompt, options, mode } = block.data;
  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2">
      {prompt ? <p className="text-sm text-slate-700">{prompt}</p> : null}
      <div className="mt-2 flex flex-wrap gap-2">
        {options.map((option) => {
          const action = (block.actions || []).find((a) => a.id === option.action_id);
          const disabled = !action || pending !== null;
          const isPrimary = option.severity === "high" || mode === "single";
          return (
            <button
              key={option.id}
              type="button"
              disabled={disabled}
              onClick={async () => {
                setPending(option.id);
                try {
                  await fire(option.action_id, { option_id: option.id, value: option.value });
                } finally {
                  setPending(null);
                }
              }}
              className={[
                "inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition",
                disabled ? "cursor-not-allowed opacity-50" : "hover:bg-slate-100",
                isPrimary
                  ? "border-slate-900 bg-slate-900 text-white hover:bg-slate-800"
                  : "border-slate-200 bg-white text-slate-800",
              ].join(" ")}
            >
              {pending === option.id ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Form                                                                         //
// --------------------------------------------------------------------------- //

export function FormBlock({ block, fire }: BlockProps<"form">): JSX.Element {
  const { fields, submit_action_id } = block.data;
  const [values, setValues] = useState<Record<string, unknown>>(() =>
    Object.fromEntries(fields.map((f) => [f.name, f.default ?? ""])),
  );
  const [submitting, setSubmitting] = useState(false);

  const update = (name: string, value: unknown) =>
    setValues((current) => ({ ...current, [name]: value }));

  const canSubmit =
    !submitting && fields.every((f) => !f.required || (values[f.name] !== "" && values[f.name] != null));

  return (
    <form
      className="space-y-2 rounded-md border border-slate-200 bg-white px-3 py-2"
      onSubmit={async (event) => {
        event.preventDefault();
        if (!canSubmit) return;
        setSubmitting(true);
        try {
          await fire(submit_action_id, { values });
        } finally {
          setSubmitting(false);
        }
      }}
    >
      {fields.map((field) => (
        <label key={field.name} className="block">
          <span className="text-xs font-medium text-slate-600">
            {field.label}
            {field.required ? <span className="text-red-500"> *</span> : null}
          </span>
          {field.kind === "textarea" ? (
            <textarea
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
              placeholder={field.placeholder ?? undefined}
              required={field.required}
              value={String(values[field.name] ?? "")}
              onChange={(e) => update(field.name, e.target.value)}
            />
          ) : field.kind === "select" ? (
            <select
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
              required={field.required}
              value={String(values[field.name] ?? "")}
              onChange={(e) => update(field.name, e.target.value)}
            >
              <option value="">—</option>
              {field.options.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          ) : field.kind === "toggle" ? (
            <input
              type="checkbox"
              className="mt-1"
              checked={Boolean(values[field.name])}
              onChange={(e) => update(field.name, e.target.checked)}
            />
          ) : (
            <input
              type={field.kind === "number" ? "number" : field.kind === "date" ? "date" : "text"}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
              placeholder={field.placeholder ?? undefined}
              required={field.required}
              min={field.min ?? undefined}
              max={field.max ?? undefined}
              step={field.step ?? undefined}
              value={String(values[field.name] ?? "")}
              onChange={(e) =>
                update(field.name, field.kind === "number" ? Number(e.target.value) : e.target.value)
              }
            />
          )}
        </label>
      ))}
      <button
        type="submit"
        disabled={!canSubmit}
        className="mt-1 inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
        Submit
      </button>
    </form>
  );
}

// --------------------------------------------------------------------------- //
// Progress                                                                     //
// --------------------------------------------------------------------------- //

const stepIcon: Record<ProgressState, JSX.Element> = {
  pending: <Circle size={14} className="text-slate-400" />,
  running: <Loader2 size={14} className="animate-spin text-slate-700" />,
  done: <CheckCircle2 size={14} className="text-emerald-600" />,
  failed: <X size={14} className="text-red-600" />,
  skipped: <Circle size={14} className="text-slate-300" />,
};

export function ProgressBlock({ block }: BlockProps<"progress">): JSX.Element {
  const data = block.data;
  if (data.shape === "steps") {
    return (
      <ul className="space-y-1">
        {data.steps.map((s) => (
          <li key={s.id} className="flex items-center gap-2 text-sm text-slate-700">
            {stepIcon[s.state]}
            <span className={s.state === "done" ? "text-slate-500 line-through" : ""}>{s.label}</span>
          </li>
        ))}
      </ul>
    );
  }
  if (data.shape === "percent") {
    const pct = Math.max(0, Math.min(100, data.percent ?? 0));
    return (
      <div className="px-1">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
          <div className="h-full rounded-full bg-slate-900 transition-all" style={{ width: `${pct}%` }} />
        </div>
        <div className="mt-1 text-xs text-slate-500">{pct}%</div>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 px-1 text-sm text-slate-700">
      <Loader2 size={14} className="animate-spin" />
      {data.status}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// List                                                                         //
// --------------------------------------------------------------------------- //

export function ListBlock({ block }: BlockProps<"list">): JSX.Element {
  const Tag: "ol" | "ul" = block.data.ordered ? "ol" : "ul";
  return (
    <Tag className={`space-y-1 px-1 text-sm text-slate-700 ${block.data.ordered ? "list-decimal pl-5" : "list-none"}`}>
      {block.data.items.map((item, i) => (
        <li key={i} className="flex items-start gap-2">
          {!block.data.ordered ? <ListChecks size={12} className="mt-1 flex-none text-slate-400" /> : null}
          <span className={item.severity === "high" ? "font-medium text-red-700" : ""}>{item.text}</span>
        </li>
      ))}
    </Tag>
  );
}

// --------------------------------------------------------------------------- //
// Link                                                                         //
// --------------------------------------------------------------------------- //

export function LinkBlock({ block }: BlockProps<"link">): JSX.Element {
  const { label, url, target } = block.data;
  return (
    <a
      href={url}
      target={target === "external" ? "_blank" : undefined}
      rel={target === "external" ? "noreferrer" : undefined}
      className="inline-flex items-center gap-1 text-sm font-medium text-slate-900 underline-offset-2 hover:underline"
    >
      <ExternalLink size={14} />
      {label}
    </a>
  );
}

// --------------------------------------------------------------------------- //
// Editable                                                                     //
// --------------------------------------------------------------------------- //

export function EditableBlock({ block, fire }: BlockProps<"editable">): JSX.Element {
  const [value, setValue] = useState(block.data.value);
  const [submitting, setSubmitting] = useState(false);
  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2">
      <div className="mb-1 flex items-center gap-1 text-xs text-slate-500">
        <Pencil size={12} />
        Editable
      </div>
      <textarea
        className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
        rows={Math.min(8, Math.max(3, value.split("\n").length))}
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      {block.data.highlights.length ? (
        <ul className="mt-1 space-y-0.5">
          {block.data.highlights.map((h) => (
            <li key={h} className="text-xs text-slate-500">· {h}</li>
          ))}
        </ul>
      ) : null}
      <button
        type="button"
        disabled={submitting}
        onClick={async () => {
          setSubmitting(true);
          try {
            await fire(block.data.submit_action_id, { value });
          } finally {
            setSubmitting(false);
          }
        }}
        className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
        Save
      </button>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Artifact link                                                                //
// --------------------------------------------------------------------------- //

export function ArtifactLinkBlock({ block, fire }: BlockProps<"artifact_link">): JSX.Element {
  const { title, summary, open_action_id } = block.data;
  return (
    <button
      type="button"
      onClick={() => void fire(open_action_id)}
      className="group flex w-full items-start justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-left transition hover:border-slate-300 hover:bg-slate-50"
    >
      <div className="min-w-0">
        <div className="text-sm font-semibold text-slate-900">{title}</div>
        {summary ? <div className="mt-0.5 text-xs text-slate-600">{summary}</div> : null}
      </div>
      <ArrowUpRight size={16} className="mt-0.5 flex-none text-slate-500 transition group-hover:text-slate-900" />
    </button>
  );
}

// --------------------------------------------------------------------------- //
// Fallback                                                                     //
// --------------------------------------------------------------------------- //

export function FallbackBlock({ block }: BlockProps<"fallback">): JSX.Element {
  return (
    <p className="rounded-md border border-dashed border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
      {block.data.content}
    </p>
  );
}
