"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Check, ChevronDown, ChevronRight, Code2, FileText, Loader2, MemoryStick, Search, Sparkles, X } from "lucide-react";
import { apiFetch, createConversationSession, getBootstrap, getConversationSession, getConversationTurns, sendConversationMessage } from "../../lib/api";
import { executeArtifactAction } from "../../lib/artifactActions";
import type { DemoContractFixture } from "../../lib/demoContracts";
import type { Artifact, ArtifactAction, ArtifactActionResult, ConversationSession, ConversationTurn, Memory, Project, RuntimeCapabilities, TraceStep, Workspace, Agent } from "../../lib/types";
import { blockData } from "../../lib/types";

type DemoState = "idle" | "working" | "result" | "revision" | "memory";
type Drawer = "why" | "trace" | "developer" | null;
type WorkspaceView = "review" | "draft" | "memory";

const SAMPLE_GOAL = "Review this AI service agreement and flag risky clauses around liability, indemnity, data, payment, and termination.";

const activitySteps = [
  {
    live: "Loading the sample agreement",
    done: "Loaded the sample agreement",
    detail: "The demo uses a real fixture from the backend instead of front-end mock data.",
  },
  {
    live: "Creating a conversation-bound run",
    done: "Created a conversation-bound run",
    detail: "The user goal is sent through the conversation message endpoint so the runtime can create a task, run, and artifact.",
  },
  {
    live: "Waiting for the model or deterministic runtime",
    done: "Runtime returned a contract review artifact",
    detail: "This can be slow when LLM mode is enabled. Tilo is not showing hidden reasoning, only observable runtime activity.",
  },
  {
    live: "Preparing the focused workspace",
    done: "Prepared the focused workspace",
    detail: "Tilo loads the artifact, trace, turns, and memory candidates, then shows only the next useful decision.",
  },
];

export function MinimalDemoPage() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [capabilities, setCapabilities] = useState<RuntimeCapabilities | null>(null);
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [goal, setGoal] = useState(SAMPLE_GOAL);
  const [state, setState] = useState<DemoState>("idle");
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>("review");
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [actionResult, setActionResult] = useState<ArtifactActionResult | null>(null);
  const [drawer, setDrawer] = useState<Drawer>(null);
  const [developerMode, setDeveloperMode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activityStepIndex, setActivityStepIndex] = useState(0);
  const [activityExpanded, setActivityExpanded] = useState(true);

  useEffect(() => {
    void boot();
  }, []);

  useEffect(() => {
    if (state !== "working") return undefined;
    setActivityStepIndex(0);
    setActivityExpanded(true);
    const interval = window.setInterval(() => {
      setActivityStepIndex((index) => Math.min(index + 1, activitySteps.length - 1));
    }, 1800);
    return () => window.clearInterval(interval);
  }, [state]);

  const primaryRisk = useMemo(() => primaryRiskForArtifact(artifact), [artifact]);
  const revision = useMemo(() => { const b = findBlock(artifact, "editable_revision"); return b ? blockData(b) : null; }, [artifact]);
  const memoryCandidate = useMemo(() => memories.find((memory) => memory.status === "candidate" && !memory.is_confirmed) || null, [memories]);
  const modeLabel = capabilities?.llm_enabled ? `LLM · ${capabilities.llm_provider}` : "Deterministic";
  const hasResult = Boolean(artifact);

  async function boot() {
    try {
      setError(null);
      const [bootstrap, runtime] = await Promise.all([
        getBootstrap(),
        apiFetch<RuntimeCapabilities>("/api/runtime/capabilities"),
      ]);
      setWorkspace(bootstrap.workspace);
      setProject(bootstrap.projects[0] || null);
      setAgent(bootstrap.agents[0] || null);
      setCapabilities(runtime);
      if (bootstrap.workspace) {
        const existingSessionId = new URLSearchParams(window.location.search).get("session_id");
        let nextSession: ConversationSession | null = null;
        if (existingSessionId) {
          try {
            nextSession = await getConversationSession(existingSessionId);
          } catch {
            nextSession = null;
          }
        }
        if (!nextSession) {
          nextSession = await createConversationSession({
            app_id: "contract-review-agent",
            workspace_id: bootstrap.workspace.id,
            project_id: bootstrap.projects[0]?.id || null,
            agent_id: bootstrap.agents[0]?.id || null,
            channel: "web",
            metadata: { source: "cowork_demo" },
          });
          const url = new URL(window.location.href);
          url.searchParams.set("session_id", nextSession.id);
          window.history.replaceState(null, "", url.toString());
        }
        setSession(nextSession);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo startup failed.");
    }
  }

  async function runReview(nextGoal = goal) {
    if (!workspace || !session || !nextGoal.trim()) return;
    setState("working");
    setWorkspaceView("review");
    setError(null);
    setArtifact(null);
    setActionResult(null);
    setMemories([]);
    setIsSubmitting(true);
    try {
      const fixture = await apiFetch<DemoContractFixture>("/api/demo/contracts/problematic-ai-service-agreement");
      const message = await sendConversationMessage(session.id, {
        content: `${nextGoal.trim()}\n\nUse this sample contract:\n\n${fixture.content}`,
        attachments: [{ name: fixture.file_name, type: "sample_contract", source_path: fixture.source_path }],
      });
      const [artifacts, traceList, turnList, memoryList] = await Promise.all([
        apiFetch<Artifact[]>(`/api/artifacts?workspace_id=${workspace.id}&task_id=${message.task_id}`),
        apiFetch<TraceStep[]>(`/api/runs/${message.run_id}/trace`),
        getConversationTurns(session.id),
        apiFetch<Memory[]>(`/api/memories?workspace_id=${workspace.id}`),
      ]);
      setArtifact(artifacts[0] || null);
      setTrace(traceList);
      setTurns(turnList);
      setMemories(memoryList);
      setActivityStepIndex(activitySteps.length - 1);
      setActivityExpanded(false);
      setState("result");
    } catch (err) {
      setState("idle");
      setError(err instanceof Error ? err.message : "Contract review failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function approveRevision() {
    if (!artifact || !session || !workspace) return;
    const action = findApprovalAction(artifact);
    if (!action) {
      setError("This artifact does not include an approval action.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const result = await executeArtifactAction({
        artifactId: artifact.id,
        actionId: action.id,
        blockId: findBlockForAction(artifact, action.id)?.id || null,
        sessionId: session.id,
        runId: artifact.run_id || null,
        source: "web",
        payload: { choice: "approve_revision", source: "cowork_demo" },
      });
      setActionResult(result);
      const [traceList, turnList, memoryList] = await Promise.all([
        artifact.run_id ? apiFetch<TraceStep[]>(`/api/runs/${artifact.run_id}/trace`) : Promise.resolve([]),
        getConversationTurns(session.id),
        apiFetch<Memory[]>(`/api/memories?workspace_id=${workspace.id}`),
      ]);
      setTrace(traceList);
      setTurns(turnList);
      setMemories(memoryList);
      setWorkspaceView("draft");
      setState("revision");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function rememberPreference() {
    if (!workspace || !artifact) return;
    setError(null);
    setIsSubmitting(true);
    try {
      let memory = memoryCandidate;
      if (!memory) {
        const block = findBlock(artifact, "memory_candidate");
        const action = block?.actions?.find((item) => item.action_type === "create_memory");
        if (!block || !action) {
          setError("No memory candidate action is available.");
          return;
        }
        const result = await executeArtifactAction({
          artifactId: artifact.id,
          actionId: action.id,
          blockId: block.id,
          sessionId: session?.id || null,
          runId: artifact.run_id || null,
          source: "web",
          payload: { source: "cowork_demo" },
        });
        setActionResult(result);
        if (!result.memory_id) {
          setError(result.message);
          return;
        }
        const memoryList = await apiFetch<Memory[]>(`/api/memories?workspace_id=${workspace.id}`);
        memory = memoryList.find((item) => item.id === result.memory_id) || null;
        setMemories(memoryList);
      }
      if (!memory) {
        setError("No memory candidate is available to confirm.");
        return;
      }
      const confirmed = await apiFetch<Memory>(`/api/memories/${memory.id}/confirm`, { method: "POST" });
      setMemories((items) => [confirmed, ...items.filter((item) => item.id !== confirmed.id)]);
      setWorkspaceView("memory");
      setState("memory");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Memory confirmation failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function notNow() {
    setError(null);
    setWorkspaceView("memory");
    setState("memory");
  }

  function handleChip(kind: "contract" | "sales" | "compare") {
    if (kind === "contract") {
      setGoal(SAMPLE_GOAL);
      return;
    }
    setGoal(kind === "sales" ? "Draft a sales follow-up plan for accounts that need attention this week." : "Compare agent frameworks for memory-native AI applications.");
  }

  return (
    <main className="cowork-demo-page">
      <header className="cowork-topbar">
        <div className="cowork-brand">
          <span className="brand-dot">T</span>
          <div>
            <strong>Tilo</strong>
            <small>AI-native product runtime</small>
          </div>
        </div>
        <nav>
          <button onClick={() => setDrawer("why")} type="button">Why this UI?</button>
          <button onClick={() => setDrawer("trace")} type="button">Trace</button>
          <button className={developerMode ? "active" : ""} onClick={() => {
            setDeveloperMode((value) => !value);
            setDrawer("developer");
          }} type="button">Developer</button>
        </nav>
      </header>

      <section className={`cowork-shell ${hasResult ? "has-workspace" : ""}`}>
        <section className="cowork-conversation" aria-label="Tilo cowork conversation">
          <ConversationIntro />

          {state !== "idle" ? <UserMessage goal={goal} /> : null}
          {state !== "idle" ? (
            <AssistantActivity
              expanded={activityExpanded}
              modeLabel={modeLabel}
              onToggle={() => setActivityExpanded((value) => !value)}
              state={state}
              stepIndex={activityStepIndex}
              trace={trace}
            />
          ) : null}
          {artifact && state !== "working" ? (
            <AssistantReviewMessage
              artifact={artifact}
              isSubmitting={isSubmitting}
              onApprove={() => void approveRevision()}
              primaryRisk={primaryRisk}
              state={state}
            />
          ) : null}
          {artifact && (state === "revision" || state === "memory") ? (
            <AssistantRevisionMessage revision={revision} />
          ) : null}
          {artifact && state === "revision" ? (
            <AssistantMemoryMessage
              content={memoryCandidate?.content || String(findBlock(artifact, "memory_candidate") ? blockData(findBlock(artifact, "memory_candidate")!).content : "Prefer conservative but negotiation-friendly contract revisions.")}
              isSubmitting={isSubmitting}
              onNotNow={notNow}
              onRemember={rememberPreference}
            />
          ) : null}
          {state === "memory" ? <AssistantDoneMessage memoryConfirmed={Boolean(memories.find((memory) => memory.is_confirmed))} /> : null}

          {error ? <p className="cowork-error">{error}</p> : null}

          <Composer
            disabled={!workspace || !session || isSubmitting || state === "working"}
            goal={goal}
            onChip={handleChip}
            onGoalChange={setGoal}
            onSubmit={() => void runReview()}
            state={state}
          />
        </section>

        <aside className="cowork-workspace" aria-label="Tilo workspace">
          <WorkspacePanel
            actionResult={actionResult}
            artifact={artifact}
            modeLabel={modeLabel}
            primaryRisk={primaryRisk}
            revision={revision}
            state={state}
            view={workspaceView}
          />
        </aside>
      </section>

      {drawer ? (
        <DemoDrawer
          actionResult={actionResult}
          agent={agent}
          artifact={artifact}
          developerMode={developerMode}
          drawer={drawer}
          memoryCandidate={memoryCandidate}
          modeLabel={modeLabel}
          onClose={() => setDrawer(null)}
          project={project}
          session={session}
          trace={trace}
          turns={turns}
          workspace={workspace}
        />
      ) : null}
    </main>
  );
}

function ConversationIntro() {
  return (
    <div className="cowork-intro">
      <span className="eyebrow">Tilo v1.0</span>
      <h1>Give Tilo a goal. It creates the workspace only when it helps.</h1>
      <p>Not a dashboard with an AI sidebar. Tilo runs the product loop behind the scenes and keeps the surface focused on the next decision.</p>
    </div>
  );
}

function UserMessage({ goal }: { goal: string }) {
  return (
    <article className="cowork-message user">
      <div className="avatar">You</div>
      <div className="bubble">{goal}</div>
    </article>
  );
}

function AssistantActivity({
  expanded,
  modeLabel,
  onToggle,
  state,
  stepIndex,
  trace,
}: {
  expanded: boolean;
  modeLabel: string;
  onToggle: () => void;
  state: DemoState;
  stepIndex: number;
  trace: TraceStep[];
}) {
  const isWorking = state === "working";
  const currentIndex = isWorking ? Math.min(stepIndex, activitySteps.length - 1) : activitySteps.length - 1;
  const traceCount = trace.length;
  const shouldShowDetails = expanded || isWorking;

  return (
    <article className="cowork-message assistant">
      <div className="avatar">Tilo</div>
      <div className="bubble activity">
        <button className="activity-summary" onClick={onToggle} type="button">
          <span>{shouldShowDetails ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</span>
          <strong>{isWorking ? activitySteps[currentIndex].live : "Activity completed"}</strong>
          <small>{isWorking ? modeLabel : `${activitySteps.length} steps · ${traceCount || "trace"} events available`}</small>
          {isWorking ? <Loader2 size={15} className="spin" /> : null}
        </button>
        {shouldShowDetails ? (
          <div className="activity-step-list">
            {activitySteps.map((step, index) => {
              const done = !isWorking || index < currentIndex;
              const active = isWorking && index === currentIndex;
              const pending = isWorking && index > currentIndex;
              return (
                <div className={`activity-step ${done ? "done" : ""} ${active ? "active" : ""} ${pending ? "pending" : ""}`} key={step.live}>
                  <span>{done ? <Check size={13} /> : active ? <Loader2 size={13} className="spin" /> : index + 1}</span>
                  <div>
                    <strong>{done ? step.done : step.live}</strong>
                    <p>{step.detail}</p>
                  </div>
                </div>
              );
            })}
            <p className="activity-note">Activity shows observable runtime progress, not hidden model reasoning.</p>
          </div>
        ) : null}
      </div>
    </article>
  );
}

function AssistantReviewMessage({
  artifact,
  isSubmitting,
  onApprove,
  primaryRisk,
  state,
}: {
  artifact: Artifact;
  isSubmitting: boolean;
  onApprove: () => void;
  primaryRisk: Record<string, unknown> | null;
  state: DemoState;
}) {
  const summary = findBlock(artifact, "risk_summary") ? blockData(findBlock(artifact, "risk_summary")!) : {};
  return (
    <article className="cowork-message assistant">
      <div className="avatar">Tilo</div>
      <div className="bubble">
        <p>I found a few issues, but only one needs your decision right now.</p>
        <div className="inline-decision">
          <span className="eyebrow">Primary decision</span>
          <strong>{String(primaryRisk?.clause || "Liability and indemnity")}</strong>
          <p>{String(primaryRisk?.issue || summary.summary || "A liability clause needs approval before revision.")}</p>
        </div>
        {state === "result" ? (
          <div className="cowork-actions">
            <button className="cowork-primary" disabled={isSubmitting} onClick={onApprove} type="button">
              {isSubmitting ? <Loader2 size={15} className="spin" /> : <Check size={15} />}
              Approve revision
            </button>
            <Link className="cowork-secondary" href={`/artifacts/${artifact.id}`}><ArrowUpRight size={14} /> Open artifact</Link>
          </div>
        ) : null}
      </div>
    </article>
  );
}

function AssistantRevisionMessage({ revision }: { revision: Record<string, unknown> | null }) {
  return (
    <article className="cowork-message assistant">
      <div className="avatar">Tilo</div>
      <div className="bubble">
        <p>Done. I drafted a conservative version and kept the negotiation tone workable.</p>
        <div className="inline-draft">
          <strong>{String(revision?.heading || "Conservative revision draft")}</strong>
          <p>{String(revision?.content || "Tilo prepared a revision draft for the approved risk.")}</p>
        </div>
      </div>
    </article>
  );
}

function AssistantMemoryMessage({
  content,
  isSubmitting,
  onNotNow,
  onRemember,
}: {
  content: string;
  isSubmitting: boolean;
  onNotNow: () => Promise<void>;
  onRemember: () => Promise<void>;
}) {
  return (
    <article className="cowork-message assistant">
      <div className="avatar">Tilo</div>
      <div className="bubble memory">
        <MemoryStick size={16} />
        <div>
          <strong>Should I remember this preference?</strong>
          <p>{content}</p>
          <div className="cowork-actions">
            <button className="cowork-primary" disabled={isSubmitting} onClick={() => void onRemember()} type="button">Remember</button>
            <button className="cowork-secondary" disabled={isSubmitting} onClick={() => void onNotNow()} type="button">Not now</button>
          </div>
        </div>
      </div>
    </article>
  );
}

function AssistantDoneMessage({ memoryConfirmed }: { memoryConfirmed: boolean }) {
  return (
    <article className="cowork-message assistant">
      <div className="avatar">Tilo</div>
      <div className="bubble muted">
        {memoryConfirmed ? "Preference saved. Future reviews can reuse it after recall." : "No problem. I will not store that preference."}
      </div>
    </article>
  );
}

function Composer({
  disabled,
  goal,
  onChip,
  onGoalChange,
  onSubmit,
  state,
}: {
  disabled: boolean;
  goal: string;
  onChip: (kind: "contract" | "sales" | "compare") => void;
  onGoalChange: (value: string) => void;
  onSubmit: () => void;
  state: DemoState;
}) {
  return (
    <section className="cowork-composer" aria-label="Tilo goal composer">
      <textarea
        aria-label="Goal"
        disabled={disabled}
        onChange={(event) => onGoalChange(event.target.value)}
        placeholder="Ask Tilo to review, compare, draft, or decide..."
        value={goal}
      />
      <div className="composer-footer">
        <div className="cowork-chip-row">
          <button onClick={() => onChip("contract")} type="button">Review contract</button>
          <button onClick={() => onChip("sales")} title="Coming after v1.0" type="button">Sales follow-up</button>
          <button onClick={() => onChip("compare")} title="Coming after v1.0" type="button">Compare frameworks</button>
        </div>
        <button className="cowork-send" disabled={disabled || !goal.trim()} onClick={onSubmit} type="button">
          {state === "working" ? <Loader2 size={16} className="spin" /> : <Search size={16} />}
          {state === "idle" ? "Start" : "Run again"}
        </button>
      </div>
    </section>
  );
}

function WorkspacePanel({
  actionResult,
  artifact,
  modeLabel,
  primaryRisk,
  revision,
  state,
  view,
}: {
  actionResult: ArtifactActionResult | null;
  artifact: Artifact | null;
  modeLabel: string;
  primaryRisk: Record<string, unknown> | null;
  revision: Record<string, unknown> | null;
  state: DemoState;
  view: WorkspaceView;
}) {
  const summary = findBlock(artifact, "risk_summary") ? blockData(findBlock(artifact, "risk_summary")!) : {};
  if (!artifact) {
    return (
      <div className="workspace-empty">
        <Sparkles size={20} />
        <strong>Workspace appears when useful</strong>
        <p>Tilo starts as a conversation. When a decision needs structure, it opens a focused surface here.</p>
        <span>{modeLabel}</span>
      </div>
    );
  }

  return (
    <div className="workspace-card">
      <div className="workspace-header">
        <span className="eyebrow">Current workspace</span>
        <h2>{view === "draft" ? "Revision draft" : view === "memory" ? "Memory decision" : artifact.title}</h2>
        <p>{view === "draft" ? "The approved decision has been translated into a draft." : view === "memory" ? "Only confirmed learning becomes memory." : "Tilo is keeping the full review in the workspace while the conversation stays focused."}</p>
      </div>

      {view === "review" ? (
        <div className="workspace-section">
          <div className="workspace-metrics">
            <span><strong>{String(summary.high_count || 0)}</strong> high-risk</span>
            <span><strong>{String(summary.medium_count || 0)}</strong> medium</span>
          </div>
          <div className="workspace-evidence">
            <span className="eyebrow">Evidence</span>
            <strong>{String(primaryRisk?.clause || "Liability and indemnity")}</strong>
            <p>{String(primaryRisk?.evidence || primaryRisk?.suggested_revision || primaryRisk?.issue || "Review the full artifact for supporting evidence.")}</p>
          </div>
        </div>
      ) : null}

      {view === "draft" || view === "memory" ? (
        <div className="workspace-section">
          <div className="workspace-evidence draft">
            <span className="eyebrow">Draft</span>
            <strong>{String(revision?.heading || "Conservative revision draft")}</strong>
            <p>{String(revision?.content || "Tilo prepared a revision draft for the approved risk.")}</p>
          </div>
          {actionResult ? <span className="action-result-chip">Action runtime: {actionResult.status}</span> : null}
        </div>
      ) : null}

      <Link className="workspace-open" href={`/artifacts/${artifact.id}`}>Open full artifact <ArrowUpRight size={14} /></Link>
    </div>
  );
}

function DemoDrawer({
  actionResult,
  agent,
  artifact,
  developerMode,
  drawer,
  memoryCandidate,
  modeLabel,
  onClose,
  project,
  session,
  trace,
  turns,
  workspace,
}: {
  actionResult: ArtifactActionResult | null;
  agent: Agent | null;
  artifact: Artifact | null;
  developerMode: boolean;
  drawer: Exclude<Drawer, null>;
  memoryCandidate: Memory | null;
  modeLabel: string;
  onClose: () => void;
  project: Project | null;
  session: ConversationSession | null;
  trace: TraceStep[];
  turns: ConversationTurn[];
  workspace: Workspace | null;
}) {
  const title = drawer === "why" ? "Why this UI?" : drawer === "trace" ? "Runtime trace" : "Developer mode";
  return (
    <div className="cowork-drawer-overlay">
      <aside className="cowork-drawer">
        <header>
          <div>
            <span className="eyebrow">Inspectable internals</span>
            <h2>{title}</h2>
          </div>
          <button onClick={onClose} type="button"><X size={16} /></button>
        </header>
        {drawer === "why" ? (
          <div className="drawer-stack">
            <p>Tilo kept the chat focused and opened a workspace only because the review found a high-risk contract decision that benefits from structured approval.</p>
            <span>Policy intent: render a focused surface only when user decision quality improves.</span>
            <span>Action runtime: POST /api/artifacts/{artifact?.id || "artifact_id"}/actions/{findApprovalAction(artifact)?.id || "action_id"}</span>
            <span>Observation: approval creates UIInteractionEvent and ConversationTurn(observation).</span>
            <span>Memory: reflection can propose a candidate, but user confirmation is required.</span>
          </div>
        ) : null}
        {drawer === "trace" ? (
          <div className="drawer-stack">
            <span>{modeLabel}</span>
            <span>session: {session?.id || "none"}</span>
            <span>artifact: {artifact?.id || "none"}</span>
            {actionResult ? <span>last action: {actionResult.status} · {actionResult.message}</span> : null}
            {trace.slice(0, 8).map((step) => <span key={step.id}>{step.step_type}: {step.status}</span>)}
            {turns.slice(-5).map((turn) => <span key={turn.id}>{turn.turn_type}: {turn.content || turn.surface_type || turn.interaction_id}</span>)}
          </div>
        ) : null}
        {drawer === "developer" ? (
          <div className="drawer-stack">
            <span>developer mode: {developerMode ? "on" : "off"}</span>
            <span>runtime: {modeLabel}</span>
            <span>workspace: {workspace?.id || "none"}</span>
            <span>project: {project?.id || "none"}</span>
            <span>agent: {agent?.id || "none"}</span>
            <span>blocks: {artifact?.schema_json.blocks.length || 0}</span>
            <span>artifact actions: {artifact?.schema_json.actions.length || 0}</span>
            <span>memory candidate: {memoryCandidate ? "available" : "not proposed yet"}</span>
            <span>last action result: {actionResult ? `${actionResult.status} / ${actionResult.action_id}` : "none"}</span>
          </div>
        ) : null}
      </aside>
    </div>
  );
}

function findBlock(artifact: Artifact | null, idOrType: string) {
  return artifact?.schema_json.blocks.find((block) => block.id === idOrType || block.type === idOrType);
}

function findApprovalAction(artifact: Artifact | null): ArtifactAction | undefined {
  return artifact?.schema_json.actions.find((action) => action.confirmation_id || action.action_type === "approve")
    || findBlock(artifact, "summary")?.actions?.find((action) => action.confirmation_id || action.action_type === "approve");
}

function findBlockForAction(artifact: Artifact, actionId: string) {
  return artifact.schema_json.blocks.find((block) => block.actions?.some((action) => action.id === actionId));
}

function primaryRiskForArtifact(artifact: Artifact | null) {
  const riskBlock = findBlock(artifact, "risk_review");
  const risks = ((riskBlock ? blockData(riskBlock).risks as Array<Record<string, unknown>> : []) || []);
  return (
    risks.find((risk) => {
      const text = `${String(risk.id || "")} ${String(risk.clause || "")} ${String(risk.issue || "")}`.toLowerCase();
      return (text.includes("8.1") && text.includes("8.2")) || (text.includes("liability") && text.includes("indemn")) || (text.includes("责任") && text.includes("赔偿"));
    }) || risks.find((risk) => String(risk.risk_level) === "high") || risks[0] || null
  );
}
