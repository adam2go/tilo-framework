"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Check, Code2, FileText, Info, Loader2, MemoryStick, Search, X } from "lucide-react";
import { apiFetch, createConversationSession, getBootstrap, getConversationSession, getConversationTurns, sendConversationMessage } from "../../lib/api";
import { executeArtifactAction } from "../../lib/artifactActions";
import type { DemoContractFixture } from "../../lib/demoContracts";
import type { Artifact, ArtifactAction, ArtifactActionResult, ConversationSession, ConversationTurn, Memory, Project, RuntimeCapabilities, TraceStep, Workspace, Agent } from "../../lib/types";

type DemoState = "idle" | "working" | "result" | "revision" | "memory";
type Drawer = "why" | "trace" | "developer" | null;

const SAMPLE_GOAL = "Review this AI service agreement and flag risky clauses around liability, indemnity, data, payment, and termination.";

const steps = [
  "Reading the contract",
  "Checking whether UI is useful",
  "Preparing one focused decision surface",
];

export function MinimalDemoPage() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [capabilities, setCapabilities] = useState<RuntimeCapabilities | null>(null);
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [goal, setGoal] = useState(SAMPLE_GOAL);
  const [state, setState] = useState<DemoState>("idle");
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [actionResult, setActionResult] = useState<ArtifactActionResult | null>(null);
  const [drawer, setDrawer] = useState<Drawer>(null);
  const [developerMode, setDeveloperMode] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void boot();
  }, []);

  const primaryRisk = useMemo(() => primaryRiskForArtifact(artifact), [artifact]);
  const revision = useMemo(() => findBlock(artifact, "editable_revision")?.data || null, [artifact]);
  const memoryCandidate = useMemo(() => memories.find((memory) => memory.status === "candidate" && !memory.is_confirmed) || null, [memories]);
  const modeLabel = capabilities?.llm_enabled ? `LLM mode · ${capabilities.llm_provider}` : "Deterministic mode";

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
            metadata: { source: "minimal_demo" },
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
    setError(null);
    setArtifact(null);
    setActionResult(null);
    setMemories([]);
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
      setState("result");
    } catch (err) {
      setState("idle");
      setError(err instanceof Error ? err.message : "Contract review failed.");
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
    try {
      const result = await executeArtifactAction({
        artifactId: artifact.id,
        actionId: action.id,
        blockId: findBlockForAction(artifact, action.id)?.id || null,
        sessionId: session.id,
        runId: artifact.run_id || null,
        source: "web",
        payload: { choice: "approve_revision", source: "minimal_demo" },
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
      setState("revision");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    }
  }

  async function rememberPreference() {
    if (!workspace || !artifact) return;
    setError(null);
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
          payload: { source: "minimal_demo" },
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
      setState("memory");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Memory confirmation failed.");
    }
  }

  async function notNow() {
    setError(null);
    setState("memory");
  }

  return (
    <main className="minimal-demo-page">
      <section className="minimal-demo-shell">
        <header className="minimal-demo-hero">
          <span className="eyebrow">Tilo v1.0</span>
          <h1>AI-native product runtime for goal-first agents.</h1>
          <p>Describe the outcome. Tilo renders the next useful surface, observes your decision, acts safely, and remembers only what you confirm.</p>
        </header>

        <section className="minimal-prompt-panel" aria-label="Tilo demo prompt">
          <textarea
            aria-label="Goal"
            disabled={state === "working"}
            onChange={(event) => setGoal(event.target.value)}
            placeholder="Ask Tilo to review a contract..."
            value={goal}
          />
          <div className="minimal-prompt-actions">
            <div className="minimal-chip-row">
              <button onClick={() => setGoal(SAMPLE_GOAL)} type="button">Review a contract</button>
              <button disabled title="Coming after v1.0" type="button">Draft sales follow-up</button>
              <button disabled title="Coming after v1.0" type="button">Compare agent frameworks</button>
            </div>
            <button className="primary-button" disabled={!workspace || !session || state === "working"} onClick={() => void runReview()} type="button">
              {state === "working" ? <Loader2 size={16} className="spin" /> : <Search size={16} />}
              Run demo
            </button>
          </div>
          {error ? <p className="minimal-error">{error}</p> : null}
        </section>

        {state === "working" ? <WorkingState /> : null}

        {artifact && state !== "working" ? (
          <section className="focused-result" aria-label="Focused contract review result">
            <div className="focused-result-header">
              <div>
                <span className="eyebrow">Contract Review</span>
                <h2>{artifact.title}</h2>
              </div>
              {developerMode ? <span className="runtime-pill">{modeLabel}</span> : null}
            </div>
            <RiskSummary artifact={artifact} primaryRisk={primaryRisk} />
            {state === "result" ? (
              <div className="focused-actions">
                <button className="primary-button" onClick={() => void approveRevision()} type="button"><Check size={16} /> Approve revision</button>
                <button className="secondary-action" onClick={() => setGoal("Make the revision softer and more customer-friendly.")} type="button">Adjust tone</button>
                <Link className="secondary-action" href={`/artifacts/${artifact.id}`}><ArrowUpRight size={14} /> Open artifact</Link>
              </div>
            ) : null}
            {state === "revision" || state === "memory" ? <RevisionCard revision={revision} /> : null}
            {state === "revision" ? (
              <MemoryPrompt
                content={memoryCandidate?.content || String(findBlock(artifact, "memory_candidate")?.data.content || "Prefer conservative but negotiation-friendly contract revisions.")}
                onNotNow={notNow}
                onRemember={rememberPreference}
              />
            ) : null}
            {state === "memory" ? <p className="minimal-success">Preference handled. Confirmed memory is available to later runs; skipped preferences were not stored.</p> : null}
            <div className="minimal-disclosure-row">
              <button onClick={() => setDrawer("why")} type="button"><Info size={14} /> Why this UI?</button>
              <button onClick={() => setDrawer("trace")} type="button"><FileText size={14} /> View trace</button>
              <button className={developerMode ? "active" : ""} onClick={() => {
                setDeveloperMode((value) => !value);
                setDrawer("developer");
              }} type="button"><Code2 size={14} /> Developer mode</button>
            </div>
          </section>
        ) : null}
      </section>

      {drawer ? (
        <DemoDrawer
          actionResult={actionResult}
          artifact={artifact}
          developerMode={developerMode}
          drawer={drawer}
          memoryCandidate={memoryCandidate}
          modeLabel={modeLabel}
          onClose={() => setDrawer(null)}
          session={session}
          trace={trace}
          turns={turns}
        />
      ) : null}
    </main>
  );
}

function WorkingState() {
  return (
    <section className="minimal-working">
      {steps.map((step, index) => (
        <span key={step}>
          <Loader2 size={14} className={index === steps.length - 1 ? "spin" : ""} />
          {step}
        </span>
      ))}
    </section>
  );
}

function RiskSummary({ artifact, primaryRisk }: { artifact: Artifact; primaryRisk: Record<string, unknown> | null }) {
  const summary = findBlock(artifact, "risk_summary")?.data || {};
  return (
    <div className="minimal-risk-card">
      <div className="minimal-risk-counts">
        <span><strong>{String(summary.high_count || 0)}</strong> high-risk</span>
        <span><strong>{String(summary.medium_count || 0)}</strong> medium</span>
      </div>
      <p>{String(summary.summary || "Tilo found contract risk that needs a decision before revision.")}</p>
      <article className="primary-decision">
        <span className="eyebrow">Primary decision</span>
        <h3>{String(primaryRisk?.clause || "Liability and indemnity")}</h3>
        <p>{String(primaryRisk?.issue || "A liability cap conflicts with broad indemnity carve-outs.")}</p>
        <small>{String(primaryRisk?.evidence || primaryRisk?.suggested_revision || "Review the full artifact for supporting evidence.")}</small>
      </article>
    </div>
  );
}

function RevisionCard({ revision }: { revision: Record<string, unknown> | null }) {
  const highlights = (revision?.highlights as string[]) || [];
  return (
    <section className="revision-result-card">
      <span className="eyebrow">Revision draft created</span>
      <h3>{String(revision?.heading || "Conservative revision draft")}</h3>
      <p>{String(revision?.content || "Tilo prepared a conservative revision for the approved risk.")}</p>
      {highlights.length ? (
        <div className="minimal-chip-row">
          {highlights.map((item) => <span key={item}>{item}</span>)}
        </div>
      ) : null}
    </section>
  );
}

function MemoryPrompt({ content, onNotNow, onRemember }: { content: string; onNotNow: () => Promise<void>; onRemember: () => Promise<void> }) {
  return (
    <section className="memory-prompt-card">
      <MemoryStick size={18} />
      <div>
        <strong>Want me to remember this preference?</strong>
        <p>{content}</p>
        <div className="focused-actions">
          <button className="primary-button" onClick={() => void onRemember()} type="button">Remember</button>
          <button className="secondary-action" onClick={() => void onNotNow()} type="button">Not now</button>
        </div>
      </div>
    </section>
  );
}

function DemoDrawer({
  actionResult,
  artifact,
  developerMode,
  drawer,
  memoryCandidate,
  modeLabel,
  onClose,
  session,
  trace,
  turns,
}: {
  actionResult: ArtifactActionResult | null;
  artifact: Artifact | null;
  developerMode: boolean;
  drawer: Exclude<Drawer, null>;
  memoryCandidate: Memory | null;
  modeLabel: string;
  onClose: () => void;
  session: ConversationSession | null;
  trace: TraceStep[];
  turns: ConversationTurn[];
}) {
  const title = drawer === "why" ? "Why this UI?" : drawer === "trace" ? "View trace" : "Developer mode";
  return (
    <div className="minimal-drawer-overlay">
      <aside className="minimal-drawer">
        <header>
          <div>
            <span className="eyebrow">Inspectable internals</span>
            <h2>{title}</h2>
          </div>
          <button onClick={onClose} type="button"><X size={16} /></button>
        </header>
        {drawer === "why" ? (
          <div className="drawer-stack">
            <p>Tilo rendered one focused surface because the contract review produced a high-risk liability decision that benefits from human approval.</p>
            <span>Policy intent: mini surface for high-risk liability confirmation.</span>
            <span>Action runtime: POST /api/artifacts/{artifact?.id || "artifact_id"}/actions/{findApprovalAction(artifact)?.id || "action_id"}</span>
            <span>Observation: approval creates a UIInteractionEvent and a ConversationTurn(observation).</span>
            <span>Memory: reflection may propose an unconfirmed preference candidate.</span>
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
  const risks = ((findBlock(artifact, "risk_review")?.data.risks as Array<Record<string, unknown>>) || []);
  return (
    risks.find((risk) => {
      const text = `${String(risk.id || "")} ${String(risk.clause || "")} ${String(risk.issue || "")}`.toLowerCase();
      return (text.includes("8.1") && text.includes("8.2")) || (text.includes("liability") && text.includes("indemn")) || (text.includes("责任") && text.includes("赔偿"));
    }) || risks.find((risk) => String(risk.risk_level) === "high") || risks[0] || null
  );
}
