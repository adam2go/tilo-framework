"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Play, RefreshCcw, Send } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { AppShell, EmptyState } from "./AppShell";
import { WorkflowSurface } from "./roam/WorkflowSurface";
import { renderInteractionComponent } from "./interaction/registry";
import { apiFetch, getBootstrap, sendMessage } from "../lib/api";
import type { Agent, Artifact, ArtifactAction, ArtifactBlock, Confirmation, Memory, Project, Skill, SkillCandidate, TraceStep, UIInteractionEvent, Workspace } from "../lib/types";

const demoPrompts = [
  {
    id: "contract",
    label: "Contract Review",
    prompt: "Contract ROAM: review this contract, show risks, request approval, and suggest a memory."
  },
  {
    id: "sales",
    label: "Sales Follow-up",
    prompt: "Sales ROAM: rank follow-ups, show pipeline metrics, queue actions, and ask for approval."
  },
  {
    id: "competitive",
    label: "Competitive Analysis",
    prompt: "Competitive ROAM: compare AI agent frameworks, select positioning, and continue next steps."
  }
];

const roamStages = ["Render", "Observe", "Act", "Memorize"];
const dynamicStages = ["Intent", "Contract Intake", "Risk Review", "Approval", "Revision Draft", "Memory"] as const;
type DynamicStage = (typeof dynamicStages)[number];
type DetailDrawer = "trace" | "memory" | "inbox" | "skills" | "observations" | null;

export function Console() {
  const searchParams = useSearchParams();
  const autoRunStarted = useRef(false);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [content, setContent] = useState(demoPrompts[0].prompt);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [confirmations, setConfirmations] = useState<Confirmation[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [skillCandidates, setSkillCandidates] = useState<SkillCandidate[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [interactions, setInteractions] = useState<UIInteractionEvent[]>([]);
  const [activeContext, setActiveContext] = useState<"trace" | "memory" | "inbox" | "skills" | "observations">("trace");
  const [dynamicStage, setDynamicStage] = useState<DynamicStage>("Intent");
  const [detailDrawer, setDetailDrawer] = useState<DetailDrawer>(null);
  const canSend = Boolean(workspace && content.trim() && !busy);
  const mode = searchParams.get("mode") === "developer" ? "developer" : "showcase";

  useEffect(() => {
    void boot();
  }, []);

  useEffect(() => {
    if (!workspace || autoRunStarted.current || searchParams.get("autorun") !== "1") return;
    const demo = demoPrompts.find((item) => item.id === searchParams.get("demo")) || demoPrompts[0];
    autoRunStarted.current = true;
    setContent(demo.prompt);
    void submit(demo.prompt);
  }, [workspace, searchParams]);

  async function boot() {
    const data = await getBootstrap();
    setWorkspace(data.workspace);
    setProject(data.projects[0] || null);
    setAgent(data.agents[0] || null);
    if (data.workspace) {
      const existing = await apiFetch<Memory[]>(`/api/memories?workspace_id=${data.workspace.id}`);
      setMemories(existing);
      const inbox = await apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${data.workspace.id}&status=pending`);
      setConfirmations(inbox);
      setSkills(await apiFetch<Skill[]>(`/api/skills?workspace_id=${data.workspace.id}`));
      setSkillCandidates(await apiFetch<SkillCandidate[]>(`/api/skills/candidates?workspace_id=${data.workspace.id}`));
      setInteractions(await apiFetch<UIInteractionEvent[]>(`/api/interactions?workspace_id=${data.workspace.id}`));
    }
  }

  async function submit(nextContent = content) {
    if (!workspace) return;
    setBusy(true);
    setError(null);
    setDynamicStage("Contract Intake");
    try {
      const response = await sendMessage({
        workspace_id: workspace.id,
        project_id: project?.id,
        agent_id: agent?.id,
        content: nextContent
      });
      const [artifacts, inbox, updatedMemories, steps, updatedSkills, candidates, updatedInteractions] = await Promise.all([
        apiFetch<Artifact[]>(`/api/artifacts?workspace_id=${workspace.id}&task_id=${response.task_id}`),
        apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${workspace.id}&status=pending`),
        apiFetch<Memory[]>(`/api/memories?workspace_id=${workspace.id}`),
        apiFetch<TraceStep[]>(`/api/runs/${response.run_id}/trace`),
        apiFetch<Skill[]>(`/api/skills?workspace_id=${workspace.id}`),
        apiFetch<SkillCandidate[]>(`/api/skills/candidates?workspace_id=${workspace.id}`),
        apiFetch<UIInteractionEvent[]>(`/api/interactions?workspace_id=${workspace.id}&run_id=${response.run_id}`)
      ]);
      setArtifact(artifacts[0] || null);
      setConfirmations(inbox);
      setMemories(updatedMemories);
      setTrace(steps);
      setSkills(updatedSkills);
      setSkillCandidates(candidates);
      setInteractions(updatedInteractions);
      setDynamicStage("Risk Review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function recordShowcaseInteraction(eventType: string, payload: Record<string, unknown> = {}, block?: ArtifactBlock, action?: ArtifactAction) {
    if (!workspace) return null;
    const event = await apiFetch<UIInteractionEvent>("/api/interactions", {
      method: "POST",
      body: JSON.stringify({
        workspace_id: workspace.id,
        project_id: project?.id || null,
        artifact_id: artifact?.id || null,
        block_id: block?.id || null,
        action_id: action?.id || null,
        run_id: artifact?.run_id || null,
        event_type: eventType,
        payload
      })
    });
    setInteractions((items) => [event, ...items]);
    return event;
  }

  async function approveShowcaseRevision() {
    const approvalAction = artifact?.schema_json.actions.find((action) => action.confirmation_id) || findBlock("summary")?.actions?.find((action) => action.confirmation_id);
    await recordShowcaseInteraction("artifact.action.approved", { stage: "Approval", action: "generate_revision" }, findBlock("summary"), approvalAction);
    if (approvalAction?.confirmation_id) {
      const updated = await apiFetch<Confirmation>(`/api/confirmations/${approvalAction.confirmation_id}/approve`, {
        method: "POST",
        body: JSON.stringify({ decision: { approved_from: "dynamic_showcase" } })
      });
      setConfirmations((items) => items.map((item) => (item.id === updated.id ? updated : item)));
    }
    setDynamicStage("Revision Draft");
  }

  async function rememberShowcasePreference() {
    const block = findBlock("memory_candidate");
    await recordShowcaseInteraction("memory.candidate.confirmed", { stage: "Memory", source: "dynamic_showcase" }, block);
    if (workspace && block) {
      const memory = await apiFetch<Memory>("/api/memories", {
        method: "POST",
        body: JSON.stringify({
          workspace_id: workspace.id,
          project_id: project?.id || null,
          source_run_id: artifact?.run_id || null,
          source_type: "ui_interaction",
          source_id: artifact?.id || null,
          type: String(block.data.memory_type || "preference"),
          content: String(block.data.content || "User prefers conservative contract review with actionable revision suggestions."),
          confidence: Number(block.data.confidence || 0.74),
          status: "candidate",
          is_confirmed: false,
          structured_payload: { stage: "Memory", artifact_id: artifact?.id || null, block_id: block.id }
        })
      });
      setMemories((items) => [memory, ...items]);
    }
  }

  async function approveConfirmation(id: string) {
    const updated = await apiFetch<Confirmation>(`/api/confirmations/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ decision: { approved_from: "console" } })
    });
    setConfirmations((items) => items.map((item) => (item.id === id ? updated : item)));
  }

  async function confirmMemory(id: string) {
    const updated = await apiFetch<Memory>(`/api/memories/${id}/confirm`, { method: "POST" });
    setMemories((items) => items.map((item) => (item.id === id ? updated : item)));
  }

  const memoryGroups = useMemo(() => {
    return {
      confirmed: memories.filter((memory) => memory.is_confirmed),
      candidates: memories.filter((memory) => !memory.is_confirmed)
    };
  }, [memories]);

  function findBlock(idOrType: string) {
    return artifact?.schema_json.blocks.find((block) => block.id === idOrType || block.type === idOrType);
  }

  if (mode === "showcase") {
    return (
      <DynamicShowcase
        artifact={artifact}
        busy={busy}
        content={content}
        confirmations={confirmations}
        detailDrawer={detailDrawer}
        dynamicStage={dynamicStage}
        error={error}
        interactions={interactions}
        memories={memories}
        onApproveRevision={approveShowcaseRevision}
        onChangeContent={setContent}
        onCloseDrawer={() => setDetailDrawer(null)}
        onOpenDrawer={setDetailDrawer}
        onRememberPreference={rememberShowcasePreference}
        onRun={() => void submit()}
        onRunDemo={(prompt) => {
          setContent(prompt);
          void submit(prompt);
        }}
        onStageChange={setDynamicStage}
        skills={skills}
        trace={trace}
      />
    );
  }

  return (
    <AppShell>
      <div className="console-grid">
        <section className="chat-panel">
          <header className="section-header command-header">
            <div>
              <span className="eyebrow">{workspace?.name || "Workspace"} · ROAM Loop</span>
              <h1>Command Center</h1>
              <p>State a goal. The agent renders a SaaS surface, your UI actions become observations, and confirmed learning updates memory.</p>
            </div>
            <button className="icon-button" title="Refresh context" onClick={() => void boot()}>
              <RefreshCcw size={16} />
            </button>
          </header>
          <div className="roam-stage-strip">
            {roamStages.map((stage, index) => (
              <div className="roam-stage" key={stage}>
                <span>{index + 1}</span>
                <strong>{stage}</strong>
              </div>
            ))}
          </div>
          <div className="demo-row">
            {demoPrompts.map((demo) => (
              <button
                key={demo.id}
                className="text-button"
                onClick={() => {
                  setContent(demo.prompt);
                  void submit(demo.prompt);
                }}
              >
                <Play size={14} />
                {demo.label}
              </button>
            ))}
          </div>
          <textarea value={content} onChange={(event) => setContent(event.target.value)} />
          <button className="primary-button" disabled={!canSend} onClick={() => void submit()}>
            <Send size={16} />
            {busy ? "Running" : "Send Message"}
          </button>
          {error ? <div className="error-box">{error}</div> : null}
          <div className="run-strip">
            <strong>{project?.name || "No project"}</strong>
            <span>{agent?.name || "No agent"} · observations {interactions.length}</span>
          </div>
        </section>

        <section className="artifact-panel">
          <WorkflowSurface artifact={artifact} />
        </section>

        <aside className="context-panel">
          <div className="context-tabs">
            {(["trace", "memory", "inbox", "skills", "observations"] as const).map((tab) => (
              <button className={activeContext === tab ? "context-tab active" : "context-tab"} key={tab} onClick={() => setActiveContext(tab)}>
                {tab[0].toUpperCase() + tab.slice(1)}
                {tab === "inbox" && confirmations.length ? <span>{confirmations.length}</span> : null}
                {tab === "memory" && memoryGroups.candidates.length ? <span>{memoryGroups.candidates.length}</span> : null}
                {tab === "observations" && interactions.length ? <span>{interactions.length}</span> : null}
              </button>
            ))}
          </div>

          {activeContext === "trace" ? (
            <section>
              <header className="mini-header">
                <strong>Trace</strong>
                <span>{trace.length}</span>
              </header>
              {trace.length ? (
                <ol className="trace-list">
                  {trace.map((step) => (
                    <li key={step.id}>
                      <strong>{step.title}</strong>
                      <span>{step.summary}</span>
                    </li>
                  ))}
                </ol>
              ) : (
                <EmptyState title="No trace yet" detail="Run a task to see visible execution steps." />
              )}
            </section>
          ) : null}

          {activeContext === "inbox" ? (
            <section>
              <header className="mini-header">
                <strong>Inbox</strong>
                <span>{confirmations.length}</span>
              </header>
              <div className="stack-list">
                {confirmations.length ? (
                  confirmations.map((item) => (
                    <div className="list-item" key={item.id}>
                      <strong>{item.title}</strong>
                      <span>{item.description}</span>
                      <button className="small-button" onClick={() => void approveConfirmation(item.id)}>
                        Approve
                      </button>
                    </div>
                  ))
                ) : (
                  <EmptyState title="No pending decisions" detail="Approval cards will create durable confirmation records." />
                )}
              </div>
            </section>
          ) : null}

          {activeContext === "memory" ? (
            <section>
              <header className="mini-header">
                <strong>Memory</strong>
                <span>
                  {memoryGroups.confirmed.length}/{memories.length}
                </span>
              </header>
              <div className="stack-list">
                {memoryGroups.candidates.slice(0, 3).map((memory) => (
                  <div className="list-item" key={memory.id}>
                    <strong>{memory.type}</strong>
                    <span>{memory.content}</span>
                    <button className="small-button" onClick={() => void confirmMemory(memory.id)}>
                      Confirm
                    </button>
                  </div>
                ))}
                {memoryGroups.confirmed.slice(0, 2).map((memory) => (
                  <div className="list-item confirmed" key={memory.id}>
                    <strong>{memory.type}</strong>
                    <span>{memory.content}</span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {activeContext === "skills" ? (
            <section>
              <header className="mini-header">
                <strong>Skills</strong>
                <span>{skills.length}/{skillCandidates.length}</span>
              </header>
              <div className="stack-list">
                {skillCandidates.slice(0, 3).map((candidate) => (
                  <div className="list-item" key={candidate.id}>
                    <strong>{candidate.name}</strong>
                    <span>{candidate.status}</span>
                  </div>
                ))}
                {skills.slice(0, 3).map((skill) => (
                  <div className="list-item confirmed" key={skill.id}>
                    <strong>{skill.name}</strong>
                    <span>{skill.description || skill.trigger_description}</span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {activeContext === "observations" ? (
            <section>
              <header className="mini-header">
                <strong>Observations</strong>
                <span>{interactions.length}</span>
              </header>
              <div className="stack-list">
                {interactions.length ? (
                  interactions.slice(0, 8).map((event) => (
                    <div className="list-item confirmed" key={event.id}>
                      <strong>{event.event_type}</strong>
                      <span>{event.block_id || event.action_id || "artifact interaction"}</span>
                      <small>{event.created_at}</small>
                    </div>
                  ))
                ) : (
                  <EmptyState title="No observations yet" detail="Click component actions to persist UIInteractionEvent records." />
                )}
              </div>
            </section>
          ) : null}
        </aside>
      </div>
    </AppShell>
  );
}

function DynamicShowcase({
  artifact,
  busy,
  content,
  confirmations,
  detailDrawer,
  dynamicStage,
  error,
  interactions,
  memories,
  onApproveRevision,
  onChangeContent,
  onCloseDrawer,
  onOpenDrawer,
  onRememberPreference,
  onRun,
  onRunDemo,
  onStageChange,
  skills,
  trace
}: {
  artifact: Artifact | null;
  busy: boolean;
  content: string;
  confirmations: Confirmation[];
  detailDrawer: DetailDrawer;
  dynamicStage: DynamicStage;
  error: string | null;
  interactions: UIInteractionEvent[];
  memories: Memory[];
  onApproveRevision: () => Promise<void>;
  onChangeContent: (content: string) => void;
  onCloseDrawer: () => void;
  onOpenDrawer: (drawer: DetailDrawer) => void;
  onRememberPreference: () => Promise<void>;
  onRun: () => void;
  onRunDemo: (prompt: string) => void;
  onStageChange: (stage: DynamicStage) => void;
  skills: Skill[];
  trace: TraceStep[];
}) {
  const blocks = artifact?.schema_json.blocks || [];
  const blockBy = (idOrType: string) => blocks.find((block) => block.id === idOrType || block.type === idOrType);
  const activeBlock =
    dynamicStage === "Risk Review" ? blockBy("risk_review") :
    dynamicStage === "Approval" ? blockBy("summary") :
    dynamicStage === "Revision Draft" ? blockBy("editable_revision") :
    dynamicStage === "Memory" ? blockBy("memory_candidate") :
    dynamicStage === "Contract Intake" ? blockBy("risk_summary") :
    null;

  return (
    <main className="dynamic-showcase">
      <header className="showcase-topbar">
        <div className="showcase-brand">
          <div className="brand-mark">T</div>
          <div>
            <strong>Tilo</strong>
            <span>Dynamic ROAM Surface</span>
          </div>
        </div>
        <nav>
          <a href="https://github.com/adam2go/tilo-framework" target="_blank" rel="noreferrer">GitHub</a>
          <a href="/workspace?mode=developer">Developer Console</a>
        </nav>
      </header>

      <section className="dynamic-stage-shell">
        <div className="dynamic-progress">
          {dynamicStages.map((stage) => (
            <button className={stage === dynamicStage ? "active" : ""} key={stage} onClick={() => onStageChange(stage)}>
              {stage}
            </button>
          ))}
        </div>

        <section className={`dynamic-surface-card stage-${dynamicStage.toLowerCase().replaceAll(" ", "-")}`}>
          {dynamicStage === "Intent" ? (
            <div className="intent-surface">
              <span className="eyebrow">Showcase Mode</span>
              <h1>What should Tilo review, decide, or generate for you?</h1>
              <p>Run the Contract Review demo to see an agent render a workflow, observe your decisions, act safely, and create reviewable memory.</p>
              <textarea value={content} onChange={(event) => onChangeContent(event.target.value)} />
              <div className="showcase-actions">
                <button className="primary-button" disabled={busy} onClick={() => onRunDemo(demoPrompts[0].prompt)}>
                  <Play size={16} />
                  {busy ? "Rendering workflow" : "Run Contract Review Demo"}
                </button>
                <button className="secondary-action" onClick={onRun} disabled={busy}>Run current goal</button>
              </div>
            </div>
          ) : (
            <ActiveShowcaseStage
              artifact={artifact}
              block={activeBlock || null}
              busy={busy}
              dynamicStage={dynamicStage}
              onApproveRevision={onApproveRevision}
              onRememberPreference={onRememberPreference}
              onStageChange={onStageChange}
            />
          )}
          {error ? <div className="error-box">{error}</div> : null}
        </section>

        <div className="showcase-pills">
          <button onClick={() => onOpenDrawer("trace")}>Trace <span>{trace.length}</span></button>
          <button onClick={() => onOpenDrawer("memory")}>Memory <span>{memories.length}</span></button>
          <button onClick={() => onOpenDrawer("inbox")}>Inbox <span>{confirmations.length}</span></button>
          <button onClick={() => onOpenDrawer("skills")}>Skills <span>{skills.length}</span></button>
          <button onClick={() => onOpenDrawer("observations")}>Observations <span>{interactions.length}</span></button>
        </div>
      </section>

      {detailDrawer ? (
        <ShowcaseDrawer
          confirmations={confirmations}
          drawer={detailDrawer}
          interactions={interactions}
          memories={memories}
          onClose={onCloseDrawer}
          skills={skills}
          trace={trace}
        />
      ) : null}
    </main>
  );
}

function ActiveShowcaseStage({
  artifact,
  block,
  busy,
  dynamicStage,
  onApproveRevision,
  onRememberPreference,
  onStageChange
}: {
  artifact: Artifact | null;
  block: ArtifactBlock | null;
  busy: boolean;
  dynamicStage: DynamicStage;
  onApproveRevision: () => Promise<void>;
  onRememberPreference: () => Promise<void>;
  onStageChange: (stage: DynamicStage) => void;
}) {
  if (busy || !artifact) {
    return (
      <div className="stage-loading">
        <span className="eyebrow">Render</span>
        <h1>Generating the contract workflow surface...</h1>
        <p>Tilo is creating a Task, Run, trace, artifact blocks, confirmation gates, and memory candidates.</p>
      </div>
    );
  }

  return (
    <div className="active-stage-content">
      <span className="eyebrow">{stageLabel(dynamicStage)}</span>
      <h1>{stageTitle(dynamicStage)}</h1>
      <p>{stageDescription(dynamicStage)}</p>
      {block ? <div className="active-stage-component">{renderInteractionComponent(artifact, block)}</div> : null}
      <div className="showcase-actions">
        {dynamicStage === "Contract Intake" ? <button className="primary-button" onClick={() => onStageChange("Risk Review")}>Review top risks</button> : null}
        {dynamicStage === "Risk Review" ? <button className="primary-button" onClick={() => onStageChange("Approval")}>Continue to decision</button> : null}
        {dynamicStage === "Approval" ? <button className="primary-button" onClick={() => void onApproveRevision()}>Approve conservative revision</button> : null}
        {dynamicStage === "Revision Draft" ? <button className="primary-button" onClick={() => onStageChange("Memory")}>Review memory candidate</button> : null}
        {dynamicStage === "Memory" ? <button className="primary-button" onClick={() => void onRememberPreference()}>Remember this preference</button> : null}
      </div>
    </div>
  );
}

function stageLabel(stage: DynamicStage) {
  if (stage === "Contract Intake" || stage === "Risk Review") return "Render";
  if (stage === "Approval") return "Observe";
  if (stage === "Revision Draft") return "Act";
  return "Memorize";
}

function stageTitle(stage: DynamicStage) {
  const titles: Record<DynamicStage, string> = {
    Intent: "Describe the contract review goal",
    "Contract Intake": "Contract intake surface",
    "Risk Review": "Three risks that need attention",
    Approval: "Generate a conservative revision draft?",
    "Revision Draft": "Revision draft surface",
    Memory: "Should Tilo remember this review preference?"
  };
  return titles[stage];
}

function stageDescription(stage: DynamicStage) {
  const descriptions: Record<DynamicStage, string> = {
    Intent: "Start with intent.",
    "Contract Intake": "Tilo detected the contract shape, review focus, and primary risk posture.",
    "Risk Review": "Focus on the current decision, not a dashboard of everything.",
    Approval: "One human decision becomes a durable observation and confirmation record.",
    "Revision Draft": "After approval, the surface changes to a revision preview.",
    Memory: "Tilo proposes reviewable memory instead of silently learning from everything."
  };
  return descriptions[stage];
}

function ShowcaseDrawer({
  confirmations,
  drawer,
  interactions,
  memories,
  onClose,
  skills,
  trace
}: {
  confirmations: Confirmation[];
  drawer: Exclude<DetailDrawer, null>;
  interactions: UIInteractionEvent[];
  memories: Memory[];
  onClose: () => void;
  skills: Skill[];
  trace: TraceStep[];
}) {
  return (
    <aside className="showcase-drawer">
      <header>
        <strong>{drawer[0].toUpperCase() + drawer.slice(1)}</strong>
        <button onClick={onClose}>Close</button>
      </header>
      <div className="stack-list">
        {drawer === "trace" ? trace.map((item) => <DrawerItem key={item.id} title={item.title} detail={item.summary} />) : null}
        {drawer === "memory" ? memories.slice(0, 8).map((item) => <DrawerItem key={item.id} title={item.type} detail={item.content} />) : null}
        {drawer === "inbox" ? confirmations.map((item) => <DrawerItem key={item.id} title={item.title} detail={item.status} />) : null}
        {drawer === "skills" ? skills.map((item) => <DrawerItem key={item.id} title={item.name} detail={item.description || item.trigger_description} />) : null}
        {drawer === "observations" ? interactions.map((item) => <DrawerItem key={item.id} title={item.event_type} detail={item.block_id || item.action_id || item.created_at} />) : null}
      </div>
    </aside>
  );
}

function DrawerItem({ title, detail }: { title: string; detail: string | null | undefined }) {
  return (
    <div className="list-item">
      <strong>{title}</strong>
      <span>{detail || "No details"}</span>
    </div>
  );
}
