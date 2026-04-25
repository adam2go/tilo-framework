"use client";

import type { Artifact, ArtifactSchema } from "../lib/types";

export function ArtifactRenderer({ artifact }: { artifact: Artifact | null }) {
  if (!artifact) {
    return <div className="artifact-placeholder">Send a message to generate an artifact.</div>;
  }
  return (
    <article className="artifact">
      <header className="section-header">
        <div>
          <span className="eyebrow">{artifact.type}</span>
          <h2>{artifact.title}</h2>
        </div>
        <span className="status-pill">v1</span>
      </header>
      <ArtifactSchemaRenderer schema={artifact.schema_json} />
    </article>
  );
}

export function ArtifactSchemaRenderer({ schema }: { schema: ArtifactSchema }) {
  return (
    <div className="artifact-blocks">
      {schema.blocks.map((block) => {
        if (block.type === "markdown") {
          return (
            <section className="text-block" key={block.id}>
              {String(block.data.content || "")}
            </section>
          );
        }
        if (block.type === "card") {
          return (
            <section className="card-block" key={block.id}>
              <strong>{String(block.data.title || "Card")}</strong>
              <span>{String(block.data.content || "")}</span>
            </section>
          );
        }
        if (block.type === "risk_item") {
          return (
            <section className="risk-block" key={block.id}>
              <div>
                <strong>{String(block.data.clause || "Clause")}</strong>
                <span className={`risk-level ${String(block.data.risk_level || "medium")}`}>
                  {String(block.data.risk_level || "medium")}
                </span>
              </div>
              <p>{String(block.data.issue || block.data.risk || "")}</p>
              <small>{String(block.data.suggested_revision || "")}</small>
            </section>
          );
        }
        if (block.type === "table") {
          const columns = ((block.data.columns as Array<string | { key: string; label: string }>) || []).map((column) =>
            typeof column === "string" ? { key: column, label: column } : column
          );
          const rows = (block.data.rows as Array<Record<string, string> | string[]>) || [];
          return (
            <div className="table-wrap" key={block.id}>
              <table>
                <thead>
                  <tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={index}>
                      {columns.map((column, cellIndex) => (
                        <td key={column.key}>
                          {Array.isArray(row) ? row[cellIndex] : row[column.key]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        if (block.type === "metric") {
          return (
            <section className="metric-block" key={block.id}>
              <span>{String(block.data.label || "")}</span>
              <strong>{String(block.data.value || "")}</strong>
            </section>
          );
        }
        if (block.type === "list") {
          const items = (block.data.items as string[]) || [];
          return (
            <ul className="artifact-list" key={block.id}>
              {items.map((item) => <li key={item}>{item}</li>)}
            </ul>
          );
        }
        if (block.type === "confirmation_action") {
          const actions = (block.data.actions as string[]) || [];
          return (
            <section className="confirmation-block" key={block.id}>
              <strong>{String(block.data.title || block.data.label || "Confirmation required")}</strong>
              <span>{actions.length ? actions.join(" / ") : String(block.data.risk_level || "review")}</span>
            </section>
          );
        }
        if (block.type === "kanban") {
          const columns = (block.data.columns as Array<{ id: string; title: string; cards: Array<{ id?: string; title: string; description?: string }> }>) || [];
          return (
            <div className="kanban-block" key={block.id}>
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
        if (block.type === "timeline") {
          const items = (block.data.items as Array<{ time: string; title: string; description?: string }>) || [];
          return (
            <ol className="timeline-block" key={block.id}>
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
        return (
          <section className="unsupported-block" key={block.id}>
            <strong>Unsupported block</strong>
            <span>{block.type}</span>
          </section>
        );
      })}
    </div>
  );
}
