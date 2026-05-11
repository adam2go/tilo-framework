"use client";

import type { ArtifactBlock } from "../../lib/types";

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
  "confirmation_action"
] as const;

function MarkdownBlock({ block }: { block: ArtifactBlock }) {
  return <section className="text-block">{String(block.data.content || "")}</section>;
}

function CardBlock({ block }: { block: ArtifactBlock }) {
  return (
    <section className="card-block">
      <strong>{String(block.data.title || block.title || "Card")}</strong>
      <span>{String(block.data.content || "")}</span>
    </section>
  );
}

function RiskItemBlock({ block }: { block: ArtifactBlock }) {
  return (
    <section className="risk-block">
      <div>
        <strong>{String(block.data.clause || block.title || "Clause")}</strong>
        <span className={`risk-level ${String(block.data.risk_level || "medium")}`}>
          {String(block.data.risk_level || "medium")}
        </span>
      </div>
      <p>{String(block.data.issue || block.data.risk || "")}</p>
      <small>{String(block.data.suggested_revision || "")}</small>
    </section>
  );
}

function TableBlock({ block }: { block: ArtifactBlock }) {
  const columns = ((block.data.columns as Array<string | { key: string; label: string }>) || []).map((column) =>
    typeof column === "string" ? { key: column, label: column } : column
  );
  const rows = (block.data.rows as Array<Record<string, string> | string[]>) || [];
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
      <span>{String(block.data.label || block.title || "")}</span>
      <strong>{String(block.data.value || "")}</strong>
    </section>
  );
}

function ListBlock({ block }: { block: ArtifactBlock }) {
  const items = (block.data.items as string[]) || [];
  return (
    <ul className="artifact-list">
      {items.map((item) => <li key={item}>{item}</li>)}
    </ul>
  );
}

function FormBlock({ block }: { block: ArtifactBlock }) {
  const fields = (block.data.fields as Array<{ name?: string; label?: string; type?: string }>) || [];
  return (
    <section className="card-block">
      <strong>{String(block.title || block.data.title || "Form")}</strong>
      <div className="artifact-list">
        {fields.length ? fields.map((field, index) => (
          <span key={field.name || `${block.id}-field-${index}`}>{String(field.label || field.name || "Field")} · {String(field.type || "text")}</span>
        )) : <span>No fields declared.</span>}
      </div>
    </section>
  );
}

function RiskPanelBlock({ block }: { block: ArtifactBlock }) {
  const risks = (block.data.risks as Array<Record<string, unknown>>) || [];
  return (
    <section className="risk-block">
      <div>
        <strong>{String(block.title || block.data.title || "Risk panel")}</strong>
        <span className="risk-level high">{String(block.data.status || "review")}</span>
      </div>
      {block.data.summary ? <p>{String(block.data.summary)}</p> : null}
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

function KanbanBlock({ block }: { block: ArtifactBlock }) {
  const columns = (block.data.columns as Array<{ id: string; title: string; cards: Array<{ id?: string; title: string; description?: string }> }>) || [];
  return (
    <div className="kanban-block">
      {columns.map((column) => (
        <section key={column.id} className="kanban-column">
          <strong>{column.title}</strong>
          {(column.cards || []).map((card, index) => (
            <div className="kanban-card" key={card.id || `${column.id}-${index}`}>
              <span>{card.title}</span>
              {card.description ? <small>{card.description}</small> : null}
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}

function TimelineBlock({ block }: { block: ArtifactBlock }) {
  const items = (block.data.items as Array<{ time: string; title: string; description?: string }>) || [];
  return (
    <ol className="timeline-block">
      {items.map((item, index) => (
        <li key={`${item.time}-${index}`}>
          <time>{item.time}</time>
          <strong>{item.title}</strong>
          {item.description ? <span>{item.description}</span> : null}
        </li>
      ))}
    </ol>
  );
}

function ConfirmationActionBlock({ block }: { block: ArtifactBlock }) {
  const actions = (block.data.actions as string[]) || [];
  return (
    <section className="confirmation-block">
      <strong>{String(block.data.title || block.data.label || "Confirmation required")}</strong>
      <span>{actions.length ? actions.join(" / ") : String(block.data.risk_level || "review")}</span>
    </section>
  );
}

function ExtensionFallbackBlock({ block }: { block: ArtifactBlock }) {
  const summary = block.data.summary || block.data.content || block.data.description || block.title || "This extension block has no compact summary.";
  return (
    <section className="unsupported-block">
      <strong>{String(block.title || "Extension block")}</strong>
      <span>{block.type}</span>
      <small>{String(summary)}</small>
    </section>
  );
}

export const blockRenderers: Record<string, BlockRenderer> = {
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
  kanban: KanbanBlock,
  timeline: TimelineBlock,
  confirmation_action: ConfirmationActionBlock
};

export function renderArtifactBlock(block: ArtifactBlock) {
  const Renderer = blockRenderers[block.type] || ExtensionFallbackBlock;
  return <Renderer block={block} />;
}
