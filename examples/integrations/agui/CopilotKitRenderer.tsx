/**
 * AG-UI best practice #4 — render a Tilo surface inside a CopilotKit app.
 *
 * When your AG-UI agent emits a CUSTOM "tilo.surface" event (see emit_surface.py),
 * the payload is a Tilo AIP spec. Render its blocks with @adam2go/tilo-react —
 * no per-component wiring, the whole surface comes from data.
 *
 *   npm install @adam2go/tilo-react @copilotkit/react-core recharts lucide-react
 *
 * This is a reference component, not a full app — drop it into your Next/React
 * project that already has CopilotKit configured.
 */
"use client";

import { renderArtifactBlock } from "@adam2go/tilo-react";
import { useCopilotAction } from "@copilotkit/react-core";

type TiloSpec = {
  title: string;
  blocks: Array<{ id: string; type: string; props?: Record<string, unknown> }>;
  views?: Array<{ id: string; label: string; block_ids: string[] }>;
};

/** Render a Tilo spec: tabbed views + blocks, all from data. */
export function TiloSurface({ spec }: { spec: TiloSpec }) {
  const byId = Object.fromEntries(spec.blocks.map((b) => [b.id, b]));
  const views = spec.views?.length ? spec.views : [{ id: "all", label: "Result", block_ids: spec.blocks.map((b) => b.id) }];

  return (
    <div className="tilo-surface">
      <h3>{spec.title}</h3>
      {views.map((view) => (
        <section key={view.id}>
          {view.label && <h4>{view.label}</h4>}
          {view.block_ids.map((id) => byId[id]).filter(Boolean).map((block) => (
            <div key={block.id}>{renderArtifactBlock(block as never)}</div>
          ))}
        </section>
      ))}
    </div>
  );
}

/**
 * Wire the CUSTOM "tilo.surface" event into CopilotKit. CopilotKit surfaces
 * AG-UI custom events as actions / render hooks; the exact hook name may vary
 * by CopilotKit version — the key idea is: receive the event `value` (a Tilo
 * spec) and render it with <TiloSurface>.
 */
export function useTiloSurfaceAction() {
  useCopilotAction({
    name: "tilo.surface",
    available: "frontend",
    render: ({ args }: { args: { value: TiloSpec } }) => <TiloSurface spec={args.value} />,
  });
}
