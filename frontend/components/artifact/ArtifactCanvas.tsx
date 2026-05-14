"use client";

/**
 * ArtifactCanvas — the generic, artifact-driven Canvas panel.
 *
 * It renders the right-hand workbench for ANY agent's artifact. The tabs,
 * their labels, icons, and block subsets are ALL declared by the artifact
 * itself via `artifact.schema_json.views`. When the artifact has no
 * `views`, all blocks render under a single "Result" tab.
 *
 * There is ZERO business-specific code here. Contract review, sales
 * follow-up, competitive analysis, NDA audit, compliance report — they
 * all render through the same Canvas just by declaring different views
 * and emitting different block types in their ArtifactSpecBuilder.
 *
 * The only "specialised" renderers live in ArtifactBlocks.tsx as
 * block-type registrations (just like SurfaceBlocks). The Canvas doesn't
 * know what a `clause_reader` is — it just asks ArtifactBlockRenderer to
 * render it. If a block type is unknown, a clean JSON fallback shows.
 */

import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Brain,
  Gauge,
  Highlighter,
  Layers,
  ListChecks,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { listArtifactsForRun, type Artifact } from "../../lib/api";
import type { ArtifactBlock as ArtifactBlockType, Memory, Run } from "../../lib/types";
import type { SurfaceTurn } from "../../lib/surface";
import { ArtifactBlockRenderer } from "./ArtifactBlocks";

// --------------------------------------------------------------------------- //
// Types                                                                       //
// --------------------------------------------------------------------------- //

export interface ArtifactView {
  id: string;
  label: string;
  icon?: string | null;
  description?: string | null;
  block_ids: string[];
  renderer?: string | null;
}

export interface ArtifactCanvasProps {
  workspaceId: string | null;
  run: Run | null;
  turns: SurfaceTurn[];
  memories: Memory[];
  modeLabel: string;
  /** External tab hint from the chat panel (e.g. clicking "Open in Canvas"). */
  activeTabHint?: string | null;
}

// --------------------------------------------------------------------------- //
// Component                                                                   //
// --------------------------------------------------------------------------- //

export function ArtifactCanvas({
  workspaceId,
  run,
  turns,
  memories,
  modeLabel,
  activeTabHint,
}: ArtifactCanvasProps) {
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [activeTab, setActiveTab] = useState<string>("__system");

  // Fetch artifact when run completes.
  useEffect(() => {
    if (!workspaceId || !run || run.status !== "completed" || !run.task_id) return;
    let alive = true;
    listArtifactsForRun(workspaceId, run.task_id)
      .then((list) => { if (alive) setArtifact(list[0] ?? null); })
      .catch(() => { if (alive) setArtifact(null); });
    return () => { alive = false; };
  }, [workspaceId, run]);

  // Compute views from artifact.
  const views: ArtifactView[] = useMemo(() => {
    if (!artifact) return [];
    const spec = artifact.schema_json as unknown as { views?: ArtifactView[] };
    if (spec.views && spec.views.length > 0) return spec.views;
    // Fallback: no declared views → create one "Result" tab with all blocks.
    return [{ id: "__all", label: "Result", block_ids: [] }];
  }, [artifact]);

  // When views appear, default to first one.
  useEffect(() => {
    if (views.length > 0 && activeTab === "__system") {
      setActiveTab(views[0].id);
    }
  }, [views]);

  // External hint can drive the tab.
  useEffect(() => {
    if (activeTabHint && views.find((v) => v.id === activeTabHint)) {
      setActiveTab(activeTabHint);
    }
  }, [activeTabHint, views]);

  // All artifact blocks indexed by id.
  const blockMap: Record<string, ArtifactBlockType> = useMemo(() => {
    if (!artifact) return {};
    const spec = artifact.schema_json as unknown as { blocks: ArtifactBlockType[] };
    return Object.fromEntries((spec.blocks ?? []).map((b) => [b.id, b]));
  }, [artifact]);

  // Blocks for the current tab.
  const currentBlocks: ArtifactBlockType[] = useMemo(() => {
    const view = views.find((v) => v.id === activeTab);
    if (!view) return [];
    if (!view.block_ids.length) return Object.values(blockMap);
    return view.block_ids.map((id) => blockMap[id]).filter(Boolean);
  }, [activeTab, views, blockMap]);

  const hasArtifact = Boolean(artifact);
  const hasRun = Boolean(run);

  // All tabs = artifact views + always-present System tab.
  const allTabs = useMemo(() => [
    ...views.map((v) => ({ id: v.id, label: v.label, icon: v.icon })),
    { id: "__system", label: "System", icon: "layers" },
  ], [views]);

  return (
    <div className="canvas-root">
      <div className="canvas-tabs">
        {allTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`canvas-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <TabIcon name={tab.icon} />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {activeTab === "__system" ? (
        <SystemPanel turns={turns} run={run} memories={memories} modeLabel={modeLabel} />
      ) : !hasRun ? (
        <CanvasEmpty title="Awaiting agent output" detail="Run a task from the chat panel. The Canvas will populate once the agent produces an artifact." />
      ) : !hasArtifact ? (
        <CanvasEmpty title="Processing…" detail="The run completed but the artifact is still being assembled." />
      ) : currentBlocks.length === 0 ? (
        <CanvasEmpty title="Empty view" detail="This view has no blocks assigned." />
      ) : (
        <div className="canvas-body">
          {currentBlocks.map((block) => (
            <ArtifactBlockRenderer key={block.id} block={block} />
          ))}
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Icon mapper                                                                 //
// --------------------------------------------------------------------------- //

function TabIcon({ name }: { name?: string | null }) {
  switch (name) {
    case "shield-alert": return <ShieldAlert size={13} />;
    case "book-open": return <BookOpen size={13} />;
    case "highlighter": return <Highlighter size={13} />;
    case "brain": return <Brain size={13} />;
    case "layers": return <Layers size={13} />;
    case "gauge": return <Gauge size={13} />;
    case "list-checks": return <ListChecks size={13} />;
    default: return <Sparkles size={13} />;
  }
}

// --------------------------------------------------------------------------- //
// System panel (runtime internals for developers)                             //
// --------------------------------------------------------------------------- //

function SystemPanel({ turns, run, memories, modeLabel }: { turns: SurfaceTurn[]; run: Run | null; memories: Memory[]; modeLabel: string }) {
  return (
    <div className="canvas-body">
      <section className="system-group">
        <div className="section-label"><Sparkles size={12} /> Surfaces · {turns.length}</div>
        <small className="system-note">{modeLabel}</small>
        <div className="system-list">
          {turns.length === 0 ? <p className="muted">No surfaces yet.</p> : null}
          {turns.map((turn) => (
            <div key={turn.id} className="system-card">
              <div className="row"><span className="intent-pill">{turn.intent.replace(/_/g, " ")}</span><small>#{turn.ordinal}</small></div>
              <code>{turn.surface_spec_json.surface_id}</code>
              <small>{turn.surface_spec_json.blocks.length} blocks · composer={turn.composer_mode}</small>
            </div>
          ))}
        </div>
      </section>
      <section className="system-group">
        <div className="section-label"><Brain size={12} /> Memory · {memories.length}</div>
        <div className="system-list">
          {memories.filter((m) => m.status === "candidate").map((m) => (
            <div key={m.id} className="system-card candidate"><small>{m.type}</small><p>{m.content}</p></div>
          ))}
          {memories.filter((m) => m.status === "confirmed").map((m) => (
            <div key={m.id} className="system-card confirmed"><small>{m.type}</small><p>{m.content}</p></div>
          ))}
          {memories.length === 0 ? <p className="muted">No memories yet.</p> : null}
        </div>
      </section>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Empty state                                                                 //
// --------------------------------------------------------------------------- //

function CanvasEmpty({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="canvas-empty">
      <div className="canvas-empty-icon"><Sparkles size={20} /></div>
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}
