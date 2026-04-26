"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Bot, Check, Code2, Database, FileText, GitBranch, MessageCircle, Play, RadioTower, Send, ShieldCheck } from "lucide-react";
import { renderInteractionComponent } from "../interaction/registry";
import { apiFetch, getBootstrap, sendMessage } from "../../lib/api";
import type { Agent, Artifact, ArtifactAction, ArtifactBlock, Confirmation, Memory, Project, RuntimeCapabilities, TraceStep, UIInteractionEvent, Workspace } from "../../lib/types";

const demoGoal = "Review this contract for payment, liability, and termination risks.";
type ChatMessage = { id: string; role: "bot" | "user"; text: string; status?: string };
type DemoStage = "Intent" | "Risk Review" | "Approval" | "Revision Draft" | "Memory";
type LiveEvent = { id: string; label: string; detail: string; status?: "done" | "active" | "pending" };

const initialLiveEvents: LiveEvent[] = [
  { id: "channel.message.received", label: "channel.message.received", detail: "Waiting for user goal", status: "pending" },
  { id: "artifact.rendered", label: "artifact.rendered", detail: "Rich surface not rendered yet", status: "pending" },
  { id: "artifact.action.clicked", label: "artifact.action.clicked", detail: "No action observed yet", status: "pending" },
  { id: "confirmation.approved", label: "confirmation.approved", detail: "No approval yet", status: "pending" },
  { id: "memory.candidate.created", label: "memory.candidate.created", detail: "Memory not created yet", status: "pending" }
];

export function TelegramDemoPage() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [capabilities, setCapabilities] = useState<RuntimeCapabilities | null>(null);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [confirmations, setConfirmations] = useState<Confirmation[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [interactions, setInteractions] = useState<UIInteractionEvent[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: "welcome", role: "bot", text: "Welcome to Tilo. Send me a goal, or run a demo." }
  ]);
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>(initialLiveEvents);
  const [composer, setComposer] = useState(demoGoal);
  const [stage, setStage] = useState<DemoStage>("Intent");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void boot();
  }, []);

  async function boot() {
    const [bootstrap, runtime] = await Promise.all([
      getBootstrap(),
      apiFetch<RuntimeCapabilities>("/api/runtime/capabilities")
    ]);
    setWorkspace(bootstrap.workspace);
    setProject(bootstrap.projects[0] || null);
    setAgent(bootstrap.agents[0] || null);
    setCapabilities(runtime);
    if (bootstrap.workspace) {
      setMemories(await apiFetch<Memory[]>(`/api/memories?workspace_id=${bootstrap.workspace.id}`));
      setInteractions(await apiFetch<UIInteractionEvent[]>(`/api/interactions?workspace_id=${bootstrap.workspace.id}`));
      setConfirmations(await apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${bootstrap.workspace.id}&status=pending`));
    }
  }

  async function runDemo(content = demoGoal) {
    if (!workspace) return;
    setBusy(true);
    setError(null);
    setLiveEvents((items) => advanceLiveEvent(items, "channel.message.received", "Goal received from Telegram-like chat"));
    setMessages((items) => [
      ...items,
      { id: `user-${Date.now()}`, role: "user", text: content },
      { id: `bot-loading-${Date.now()}`, role: "bot", text: "Tilo is rendering a contract review workflow...", status: "rendering" }
    ]);
    try {
      const response = await sendMessage({
        workspace_id: workspace.id,
        project_id: project?.id,
        agent_id: agent?.id,
        content
      });
      const [artifacts, inbox, memoryList, traceList, eventList] = await Promise.all([
        apiFetch<Artifact[]>(`/api/artifacts?workspace_id=${workspace.id}&task_id=${response.task_id}`),
        apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${workspace.id}&status=pending`),
        apiFetch<Memory[]>(`/api/memories?workspace_id=${workspace.id}`),
        apiFetch<TraceStep[]>(`/api/runs/${response.run_id}/trace`),
        apiFetch<UIInteractionEvent[]>(`/api/interactions?workspace_id=${workspace.id}&run_id=${response.run_id}`)
      ]);
      const nextArtifact = artifacts[0] || null;
      setArtifact(nextArtifact);
      setConfirmations(inbox);
      setMemories(memoryList);
      setTrace(traceList);
      setInteractions(eventList);
      setStage("Risk Review");
      const riskCount = riskSummary(nextArtifact);
      setLiveEvents((items) => advanceLiveEvent(items, "artifact.rendered", "Contract Review surface rendered"));
      setMessages((items) => [
        ...items.filter((item) => item.status !== "rendering"),
        { id: `bot-ready-${Date.now()}`, role: "bot", text: `Contract Review is ready. ${riskCount} high-risk clause${riskCount === 1 ? "" : "s"} found. I opened the rich review surface.` }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run Telegram-like demo");
    } finally {
      setBusy(false);
    }
  }

  async function openSurface() {
    if (!workspace || !artifact) return;
    const event = await apiFetch<UIInteractionEvent>("/api/interactions", {
      method: "POST",
      body: JSON.stringify({
        workspace_id: workspace.id,
        project_id: project?.id || null,
        artifact_id: artifact.id,
        run_id: artifact.run_id,
        event_type: "channel.telegram_demo.open_surface",
        payload: { channel: "telegram-demo", surface: "rich_artifact" }
      })
    });
    setInteractions((items) => [event, ...items]);
    setStage("Risk Review");
    setMessages((items) => [...items, { id: `user-open-${Date.now()}`, role: "user", text: "Open Review Surface" }]);
  }

  async function approveRevision() {
    if (!workspace || !artifact) return;
    const action = findApprovalAction(artifact);
    const block = findBlock(artifact, "summary");
    const event = await apiFetch<UIInteractionEvent>("/api/interactions", {
      method: "POST",
      body: JSON.stringify({
        workspace_id: workspace.id,
        project_id: project?.id || null,
        artifact_id: artifact.id,
        block_id: block?.id || null,
        action_id: action?.id || "approve_revision",
        run_id: artifact.run_id,
        event_type: "channel.telegram_demo.approve_revision",
        payload: { channel: "telegram-demo", confirmation_id: action?.confirmation_id || null }
      })
    });
    if (action?.confirmation_id) {
      const updated = await apiFetch<Confirmation>(`/api/confirmations/${action.confirmation_id}/approve`, {
        method: "POST",
        body: JSON.stringify({ decision: { source: "telegram_like_web_demo" } })
      });
      setConfirmations((items) => items.map((item) => (item.id === updated.id ? updated : item)).filter((item) => item.status === "pending"));
    }
    setInteractions((items) => [event, ...items]);
    setStage("Revision Draft");
    setLiveEvents((items) =>
      advanceLiveEvent(
        advanceLiveEvent(items, "artifact.action.clicked", "Approve Revision clicked from chat/surface"),
        "confirmation.approved",
        "Linked Confirmation approved"
      )
    );
    setMessages((items) => [
      ...items,
      { id: `user-approved-${Date.now()}`, role: "user", text: "Approve Revision" },
      { id: `bot-approved-${Date.now()}`, role: "bot", text: "Approved. Tilo is generating a conservative revision draft." },
      { id: `bot-memory-ready-${Date.now()}`, role: "bot", text: "Memory candidate ready. Should Tilo remember this review preference?" }
    ]);
  }

  async function rememberPreference() {
    if (!workspace || !artifact) return;
    const block = findBlock(artifact, "memory_candidate");
    const event = await apiFetch<UIInteractionEvent>("/api/interactions", {
      method: "POST",
      body: JSON.stringify({
        workspace_id: workspace.id,
        project_id: project?.id || null,
        artifact_id: artifact.id,
        block_id: block?.id || null,
        run_id: artifact.run_id,
        event_type: "channel.telegram_demo.remember_preference",
        payload: { channel: "telegram-demo" }
      })
    });
    setInteractions((items) => [event, ...items]);
    if (block) {
      const memory = await apiFetch<Memory>("/api/memories", {
        method: "POST",
        body: JSON.stringify({
          workspace_id: workspace.id,
          project_id: project?.id || null,
          source_run_id: artifact.run_id,
          source_type: "telegram_like_demo",
          source_id: artifact.id,
          type: String(block.data.memory_type || "preference"),
          content: String(block.data.content || "User prefers conservative contract review with actionable revision suggestions."),
          confidence: Number(block.data.confidence || 0.75),
          status: "confirmed",
          is_confirmed: true,
          structured_payload: { artifact_id: artifact.id, block_id: block.id, channel: "telegram-demo" }
        })
      });
      setMemories((items) => [memory, ...items]);
    }
    setStage("Memory");
    setLiveEvents((items) => advanceLiveEvent(items, "memory.candidate.created", "Confirmed preference persisted to memory"));
    setMessages((items) => [
      ...items,
      { id: `user-remember-${Date.now()}`, role: "user", text: "Remember this preference" },
      { id: `bot-memory-${Date.now()}`, role: "bot", text: "Remembered. Future contract reviews will use this preference." }
    ]);
  }

  const modeLabel = capabilities?.llm_enabled ? `LLM mode: ${capabilities.llm_provider} · ${capabilities.default_model}` : "Demo mode: deterministic artifact generation";
  const activeBlocks = useMemo(() => selectBlocksForStage(artifact, stage), [artifact, stage]);

  return (
    <main className="telegram-demo-page">
      <header className="telegram-demo-header">
        <div>
          <span className="eyebrow">Tilo Telegram-like Demo · ROAM Loop</span>
          <h1>Chat is the entry. Surface is the workspace. Interaction becomes memory.</h1>
        </div>
        <nav>
          <a href="/workspace?mode=developer">Developer Console</a>
          <a href="https://github.com/adam2go/tilo-framework" target="_blank" rel="noreferrer">GitHub</a>
        </nav>
      </header>

      <section className="telegram-demo-grid">
        <ChatSimulator
          artifact={artifact}
          busy={busy}
          composer={composer}
          messages={messages}
          onApprove={approveRevision}
          onChangeComposer={setComposer}
          onOpenSurface={openSurface}
          onRemember={rememberPreference}
          onRun={() => void runDemo(composer || demoGoal)}
        />
        <RichSurfacePreview
          activeBlocks={activeBlocks}
          artifact={artifact}
          busy={busy}
          error={error}
          modeLabel={modeLabel}
          onApprove={approveRevision}
          onRemember={rememberPreference}
          stage={stage}
        />
        <DeveloperInspector
          capabilities={capabilities}
          confirmations={confirmations}
          interactions={interactions}
          liveEvents={liveEvents}
          memories={memories}
          modeLabel={modeLabel}
          trace={trace}
        />
      </section>
    </main>
  );
}

function ChatSimulator({
  artifact,
  busy,
  composer,
  messages,
  onApprove,
  onChangeComposer,
  onOpenSurface,
  onRemember,
  onRun
}: {
  artifact: Artifact | null;
  busy: boolean;
  composer: string;
  messages: ChatMessage[];
  onApprove: () => Promise<void>;
  onChangeComposer: (value: string) => void;
  onOpenSurface: () => Promise<void>;
  onRemember: () => Promise<void>;
  onRun: () => void;
}) {
  return (
    <aside className="telegram-phone">
      <header>
        <div className="telegram-avatar"><Bot size={18} /></div>
        <div>
          <strong>Tilo Bot</strong>
          <span>{busy ? "rendering workflow" : "online"}</span>
        </div>
      </header>
      <div className="telegram-thread">
        {messages.map((message) => (
          <div className={`telegram-bubble ${message.role}`} key={message.id}>
            {message.text}
          </div>
        ))}
        <div className="telegram-inline-actions">
          <button onClick={onRun} disabled={busy}><Play size={14} /> Run Contract Review Demo</button>
          <button onClick={() => void onOpenSurface()} disabled={!artifact}><ArrowUpRight size={14} /> Open Review Surface</button>
          <button onClick={() => void onApprove()} disabled={!artifact}><Check size={14} /> Approve Revision</button>
          <button onClick={() => void onRemember()} disabled={!artifact}><Database size={14} /> Remember</button>
        </div>
      </div>
      {artifact ? <a className="telegram-artifact-link" href={`/artifacts/${artifact.id}?channel=telegram-demo`}>Open artifact page</a> : null}
      <footer className="telegram-composer">
        <input value={composer} onChange={(event) => onChangeComposer(event.target.value)} />
        <button onClick={onRun} disabled={busy}><Send size={16} /></button>
      </footer>
    </aside>
  );
}

function RichSurfacePreview({
  activeBlocks,
  artifact,
  busy,
  error,
  modeLabel,
  onApprove,
  onRemember,
  stage
}: {
  activeBlocks: ArtifactBlock[];
  artifact: Artifact | null;
  busy: boolean;
  error: string | null;
  modeLabel: string;
  onApprove: () => Promise<void>;
  onRemember: () => Promise<void>;
  stage: DemoStage;
}) {
  return (
    <section className="telegram-rich-surface">
      <div className="surface-topline">
        <div>
          <span className="eyebrow">Dynamic ROAM Surface</span>
          <h2>{artifact?.title || "Contract Review Surface"}</h2>
        </div>
        <span className={modeLabel.startsWith("LLM") ? "runtime-badge llm" : "runtime-badge"}>{modeLabel}</span>
      </div>
      <div className="roam-mini-strip">
        {["Render", "Observe", "Act", "Memorize"].map((item) => <span key={item}>{item}</span>)}
      </div>
      {busy ? (
        <div className="telegram-empty-surface loading">
          <MessageCircle size={28} />
          <strong>Rendering contract review workflow...</strong>
          <span>Tilo is creating Task, Run, TraceStep, Artifact, Confirmation, and Memory candidates.</span>
        </div>
      ) : null}
      {!busy && !artifact ? (
        <InitialSurfacePreview />
      ) : null}
      {error ? <div className="error-box">{error}</div> : null}
      {artifact ? (
        <div className="telegram-surface-blocks">
          <div className="stage-context">
            <span>{stage}</span>
            <p>{stageCopy(stage)}</p>
          </div>
          <FocusedContractSurface artifact={artifact} blocks={activeBlocks} stage={stage} />
          <div className="surface-primary-actions">
            <button className="primary-button" onClick={() => void onApprove()} disabled={stage === "Revision Draft" || stage === "Memory"}>Approve Revision</button>
            <button className="secondary-action" onClick={() => void onRemember()}>Remember Preference</button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function InitialSurfacePreview() {
  const steps = [
    { icon: <MessageCircle size={16} />, title: "Chat entry", detail: "User sends a contract review goal." },
    { icon: <FileText size={16} />, title: "Rich Surface", detail: "Tilo opens the review where dense UI belongs." },
    { icon: <ShieldCheck size={16} />, title: "Approval", detail: "Human decision becomes a durable confirmation." },
    { icon: <GitBranch size={16} />, title: "Revision", detail: "Approved action generates a focused draft." },
    { icon: <Database size={16} />, title: "Memory", detail: "Confirmed preference improves future work." }
  ];
  return (
    <div className="telegram-preview-surface">
      <div className="preview-hero-card">
        <span className="eyebrow">Preview Flow</span>
        <h3>Chat starts the task. Tilo renders the workspace.</h3>
        <p>A lightweight message launches a full ROAM surface for review, approval, revision, and memory.</p>
      </div>
      <div className="preview-flow-grid">
        {steps.map((step, index) => (
          <article key={step.title}>
            <div>{step.icon}</div>
            <span>{index + 1}</span>
            <strong>{step.title}</strong>
            <p>{step.detail}</p>
          </article>
        ))}
      </div>
      <div className="preview-contract-card">
        <div>
          <strong>Contract Review Surface</strong>
          <span>RiskReviewPanel is too rich for chat, so it opens here.</span>
        </div>
        <div className="preview-risk-node">
          <b>Liability</b>
          <em>high risk</em>
        </div>
      </div>
    </div>
  );
}

function FocusedContractSurface({ artifact, blocks, stage }: { artifact: Artifact; blocks: ArtifactBlock[]; stage: DemoStage }) {
  const riskSummaryBlock = blocks.find((block) => block.type === "risk_summary");
  const approvalBlock = blocks.find((block) => block.type === "approval_card");
  const riskBlock = blocks.find((block) => block.type === "risk_review_panel");
  const revisionBlock = blocks.find((block) => block.type === "editable_document_preview");
  const memoryBlock = blocks.find((block) => block.type === "memory_candidate_card");
  const risks = ((riskBlock?.data.risks as Array<Record<string, unknown>>) || []);
  const activeRisk = risks.find((risk) => String(risk.risk_level) === "high") || risks[0];
  const secondaryRisks = risks.filter((risk) => risk !== activeRisk).slice(0, 4);

  if (stage === "Revision Draft" && revisionBlock) {
    return <div className="focused-single-block">{renderInteractionComponent(artifact, revisionBlock)}</div>;
  }
  if (stage === "Memory" && memoryBlock) {
    return <div className="focused-single-block">{renderInteractionComponent(artifact, memoryBlock)}</div>;
  }

  return (
    <div className="focused-contract-surface">
      {riskSummaryBlock ? (
        <div className="compact-risk-summary">
          <div>
            <strong>{String(riskSummaryBlock.data.high_count || 0)}</strong>
            <span>High</span>
          </div>
          <div>
            <strong>{String(riskSummaryBlock.data.medium_count || 0)}</strong>
            <span>Medium</span>
          </div>
          <div>
            <strong>{String(riskSummaryBlock.data.low_count || 0)}</strong>
            <span>Low</span>
          </div>
          <p>{String(riskSummaryBlock.data.summary || "")}</p>
        </div>
      ) : null}

      {activeRisk ? (
        <article className="active-risk-node">
          <div className="active-risk-heading">
            <div>
              <span className="eyebrow">Active Risk Node</span>
              <h3>{String(activeRisk.clause || "Contract risk")}</h3>
            </div>
            <em>{String(activeRisk.risk_level || "medium")}</em>
          </div>
          <p>{String(activeRisk.issue || "")}</p>
          <div className="revision-callout">
            <strong>Recommended revision</strong>
            <span>{String(activeRisk.suggested_revision || "")}</span>
          </div>
          {activeRisk.evidence ? <small>Evidence: {String(activeRisk.evidence)}</small> : null}
        </article>
      ) : null}

      {secondaryRisks.length ? (
        <div className="secondary-risk-strip">
          {secondaryRisks.map((risk) => (
            <div key={String(risk.id || risk.clause)}>
              <strong>{String(risk.clause || "Risk")}</strong>
              <span>{String(risk.risk_level || "medium")}</span>
            </div>
          ))}
        </div>
      ) : null}

      {approvalBlock ? <div className="focused-decision-card">{renderInteractionComponent(artifact, approvalBlock)}</div> : null}
    </div>
  );
}

function DeveloperInspector({
  capabilities,
  confirmations,
  interactions,
  liveEvents,
  memories,
  modeLabel,
  trace
}: {
  capabilities: RuntimeCapabilities | null;
  confirmations: Confirmation[];
  interactions: UIInteractionEvent[];
  liveEvents: LiveEvent[];
  memories: Memory[];
  modeLabel: string;
  trace: TraceStep[];
}) {
  return (
    <aside className="telegram-dev-inspector">
      <InspectorCard icon={<Code2 size={16} />} title="Interaction Contract">
        <code>when: risk.detected</code>
        <code>condition: risk_level == high</code>
        <code>render: RiskReviewPanel</code>
        <code>observe: approve_revision</code>
        <code>act: generate_revised_clause</code>
        <code>memorize: user_preference</code>
      </InspectorCard>
      <InspectorCard icon={<RadioTower size={16} />} title="Channel -> Surface Routing">
        <span>ApprovalCard to Telegram buttons</span>
        <span>RiskReviewPanel to Open rich surface</span>
        <span>EditableDocument to Open artifact page</span>
        <span>MemoryCandidate to Chat or surface</span>
      </InspectorCard>
      <InspectorCard icon={<GitBranch size={16} />} title="Renderer Decision">
        <span>RiskReviewPanel routes rich review into the Rich Surface</span>
        <span>ApprovalCard renders as chat buttons</span>
        <span>MemoryCandidateCard can render in chat or surface</span>
      </InspectorCard>
      <InspectorCard icon={<MessageCircle size={16} />} title="Live Events">
        {liveEvents.map((event) => (
          <span className={`live-event ${event.status || "pending"}`} key={event.id}>
            {event.label}: {event.detail}
          </span>
        ))}
      </InspectorCard>
      <InspectorCard icon={<ShieldCheck size={16} />} title="Runtime Mode">
        <strong>{modeLabel}</strong>
        <span>Provider family: {capabilities?.llm_provider_family || "openai_compatible"}</span>
        <span>Telegram live bot: {capabilities?.telegram_enabled ? "configured" : "not configured"}</span>
        <span>Model exposed to frontend: no API key, mode only</span>
      </InspectorCard>
      <InspectorCard icon={<Database size={16} />} title="Durable Observations">
        {interactions.slice(0, 5).map((event) => <span key={event.id}>{event.event_type}</span>)}
        {!interactions.length ? <span>channel.message.received</span> : null}
        <span>pending confirmations: {confirmations.length}</span>
        <span>memories: {memories.length}</span>
        <span>trace steps: {trace.length}</span>
      </InspectorCard>
    </aside>
  );
}

function InspectorCard({ children, icon, title }: { children: ReactNode; icon: ReactNode; title: string }) {
  return (
    <section className="inspector-card">
      <header>{icon}<strong>{title}</strong></header>
      <div>{children}</div>
    </section>
  );
}

function selectBlocksForStage(artifact: Artifact | null, stage: DemoStage) {
  if (!artifact) return [];
  const blocks = artifact.schema_json.blocks;
  const by = (idOrType: string) => blocks.find((block) => block.id === idOrType || block.type === idOrType);
  if (stage === "Revision Draft") return [by("editable_revision")].filter(Boolean) as ArtifactBlock[];
  if (stage === "Memory") return [by("memory_candidate")].filter(Boolean) as ArtifactBlock[];
  if (stage === "Approval") return [by("risk_summary"), by("summary"), by("risk_review")].filter(Boolean) as ArtifactBlock[];
  return [by("risk_summary"), by("risk_review"), by("summary")].filter(Boolean) as ArtifactBlock[];
}

function findBlock(artifact: Artifact, idOrType: string) {
  return artifact.schema_json.blocks.find((block) => block.id === idOrType || block.type === idOrType);
}

function findApprovalAction(artifact: Artifact): ArtifactAction | undefined {
  return artifact.schema_json.actions.find((action) => action.confirmation_id) || findBlock(artifact, "summary")?.actions?.find((action) => action.confirmation_id);
}

function riskSummary(artifact: Artifact | null) {
  const block = artifact?.schema_json.blocks.find((item) => item.id === "risk_summary");
  return Number(block?.data.high_count || 3);
}

function stageCopy(stage: DemoStage) {
  const copy: Record<DemoStage, string> = {
    Intent: "The chat-like entry captures user intent.",
    "Risk Review": "Rich contract review opens in the ROAM surface, not inside the chat thread.",
    Approval: "A lightweight approval can happen from chat or the rich surface.",
    "Revision Draft": "After approval, Tilo acts and renders the conservative revision draft.",
    Memory: "Confirmed preference becomes inspectable long-term memory."
  };
  return copy[stage];
}

function advanceLiveEvent(items: LiveEvent[], eventId: string, detail: string): LiveEvent[] {
  return items.map((event) => event.id === eventId ? { ...event, detail, status: "done" as const } : event);
}
