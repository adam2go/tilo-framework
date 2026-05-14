"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Database,
  FileText,
  Loader2,
  MessageSquare,
  PanelRightOpen,
  Search,
  Sparkles,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import {
  apiFetch,
  createConversationSession,
  getBootstrap,
  getConversationSession,
  startConversationMessage,
} from "../../lib/api";
import {
  executeSurfaceAction,
  fetchRunSurfaceTurns,
} from "../../lib/surfaceClient";
import { TiloRenderer } from "./TiloRenderer";
import { ArtifactCanvas } from "../artifact";
import type {
  ConversationSession,
  Memory,
  Project,
  Run,
  RuntimeCapabilities,
  TraceStep,
  Workspace,
} from "../../lib/types";
import type { SurfaceTurn } from "../../lib/surface";
import type { TiloAction } from "./types";

type RunPhase = "idle" | "thinking" | "rendered" | "error";
type Drawer = "why" | null;

const SAMPLE_GOALS: Record<string, Array<{ id: string; label: string; icon: string; text: string }>> = {
  en: [
    { id: "contract", label: "Contract review", icon: "📋", text: "Review this AI service agreement and flag risky clauses around liability, indemnity, data, payment, and termination." },
    { id: "sales", label: "Sales follow-up", icon: "📊", text: "Show me the current sales pipeline and suggest follow-up actions for our top three accounts: Acme, Northstar, and Finch Labs." },
    { id: "competitive", label: "Competitive analysis", icon: "🏆", text: "Run a competitive analysis comparing our positioning against the top two competitors in the AI agent market." },
  ],
  zh: [
    { id: "contract", label: "合同审查", icon: "📋", text: "审查这份 AI 客服系统服务合同，重点标注责任上限、赔偿例外、数据隐私、付款节奏和终止条款相关的风险条款。" },
    { id: "sales", label: "销售跟进", icon: "📊", text: "展示当前销售管线并为我们的三个重点客户（Acme、Northstar、Finch Labs）推荐跟进行动。" },
    { id: "competitive", label: "竞品分析", icon: "🏆", text: "对比我们与 AI Agent 市场前两名竞品的定位，分析各方优劣势。" },
  ],
};

const UI_TEXT: Record<string, Record<string, string>> = {
  en: {
    tagline: "AI-native runtime · Surface Protocol v1",
    introTitle: "Give Tilo a goal. Watch it think, then render only the decisions you need.",
    introBody: "Each step is a real runtime trace — recall, plan, tools, LLM, policy, render. The Canvas on the right becomes a domain workbench as soon as the run completes.",
    introTrace: "Activity stream is the agent's process, transparent and short.",
    introSurface: "Surfaces are the product layer — generated for the moment.",
    introMemory: "Memory only saves what you confirm.",
    trySample: "Try a scenario:",
    followUpLabel: "Continue the conversation:",
    whyTitle: "Why this UI?",
    placeholder: "Ask Tilo to review, compare, draft, or decide…",
    run: "Run",
    runAgain: "Run again",
    canvas: "Canvas",
    lang: "中文",
  },
  zh: {
    tagline: "AI 原生运行时 · Surface Protocol v1",
    introTitle: "给 Tilo 一个目标，看它思考，然后只渲染你需要的决策。",
    introBody: "每一步都是真实的运行时链路——记忆召回、规划、工具、LLM、策略、渲染。右侧 Canvas 在运行结束后自动变成领域工作台。",
    introTrace: "Activity stream 是 agent 的思考过程，透明而简短。",
    introSurface: "Surface 是产品层——为当下生成。",
    introMemory: "只有你确认的记忆才会被保存。",
    trySample: "选择一个场景：",
    followUpLabel: "继续对话：",
    whyTitle: "为什么是这个 UI？",
    placeholder: "让 Tilo 审查、对比、起草或决策……",
    run: "执行",
    runAgain: "再次执行",
    canvas: "画布",
    lang: "EN",
  },
};

/**
 * Generate context-aware follow-up suggestions from the current run's
 * artifact and surfaces. This is NOT hardcoded — the suggestions are
 * derived from what the agent actually produced. When the artifact has
 * risk findings, suggestions reference those clauses; when it's a
 * dashboard, suggestions reference account names; etc.
 */
function deriveFollowUps(
  artifact: { type: string; schema_json: Record<string, unknown> } | null,
  resultSummary: string | null,
  locale: string,
): string[] {
  if (!artifact) return [];
  const spec = artifact.schema_json as Record<string, unknown>;
  const blocks = (spec.blocks ?? []) as Array<{ type: string; data: Record<string, unknown> }>;
  const zh = locale === "zh";

  if (artifact.type === "contract_review") {
    const riskBlock = blocks.find((b) => b.type === "risk_review_panel");
    const risks = (riskBlock?.data?.risks ?? []) as Array<{ clause: string; risk_level: string; issue: string }>;
    const highRisks = risks.filter((r) => r.risk_level === "high");
    const clauses = highRisks.slice(0, 2).map((r) => r.clause).join(" / ");
    return [
      zh ? `针对条款 ${clauses || "高风险条款"} 起草保守修订意见，语气要求协商友好。` : `Draft conservative revisions for clauses ${clauses || "the high-risk clauses"} with a negotiation-friendly tone.`,
      zh ? `${highRisks.length} 个高风险项中，哪些应该立即升级给法务团队？按业务影响排优先级。` : `Of the ${highRisks.length} high-risk findings, which should we escalate to legal immediately? Prioritize by business impact.`,
    ];
  }
  if (artifact.type === "dashboard") {
    const actionBlock = blocks.find((b) => b.type === "action_queue");
    const items = ((actionBlock?.data?.items ?? []) as Array<{ title: string }>).slice(0, 2);
    const names = items.map((i) => i.title.replace("Follow up with ", "").replace("Send renewal summary", "Northstar")).join(" and ");
    return [
      zh ? `为 ${names || "最优先客户"} 起草一封简短的跟进邮件，询问采购时间表。` : `Draft a concise follow-up email for ${names || "the top-priority account"} asking about procurement timelines.`,
      zh ? `基于当前管线数据，下周的三个最关键行动是什么？` : `Based on the current pipeline data, what are the three most critical actions for next week?`,
    ];
  }
  if (artifact.type === "table") {
    return [
      zh ? `基于这份分析，起草一页定位声明，强调我们的记忆原生优势。` : `Based on this analysis, draft a one-page positioning statement emphasizing our memory-native advantage.`,
      zh ? `对比我们和头号竞品的定价模型，什么策略能让我们更有竞争力？` : `Compare our pricing model against the top competitor's. What strategy would make ours more compelling?`,
    ];
  }
  // Fallback
  return [
    zh ? `请展开关键发现并建议后续步骤。` : `Can you expand on the key findings and suggest next steps?`,
  ];
}

interface HistoryRound {
  id: string;
  goal: string;
  trace: TraceStep[];
  turns: SurfaceTurn[];
  run: Run | null;
  memories: Memory[];
  actedTurns: Record<string, string>;
}

interface InteractionEvent {
  id: string;
  event_type: string;
  action_id: string | null;
  block_id: string | null;
  payload_json: Record<string, unknown> | null;
  created_at: string;
}

export function CoworkSurfaceDemo() {
  // Hydration-safe gate: the server renders an empty placeholder so the
  // client and server HTML always match. Real content mounts after the
  // first effect runs, exclusively on the client.
  const [mounted, setMounted] = useState(false);
  const [locale, setLocale] = useState<"en" | "zh">("en");
  const t = UI_TEXT[locale];
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [capabilities, setCapabilities] = useState<RuntimeCapabilities | null>(null);
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [goal, setGoal] = useState("");
  const [phase, setPhase] = useState<RunPhase>("idle");
  const [run, setRun] = useState<Run | null>(null);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [turns, setTurns] = useState<SurfaceTurn[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [events, setEvents] = useState<InteractionEvent[]>([]);
  // Multi-turn: completed rounds are pushed here so the conversation
  // scroll shows all previous rounds, not just the latest one.
  const [history, setHistory] = useState<HistoryRound[]>([]);
  const [lastArtifactType, setLastArtifactType] = useState<string | null>(null);
  const [lastArtifact, setLastArtifact] = useState<{ type: string; schema_json: Record<string, unknown> } | null>(null);
  const [drawer, setDrawer] = useState<Drawer>(null);
  const [inspectorOpen, setInspectorOpen] = useState(true);
  // Canvas tab hint: when the user clicks "Open in Canvas" on a surface
  // bubble, we set this to the view id that best matches the intent. The
  // ArtifactCanvas picks it up and switches tabs. This is a *suggestion*,
  // not state we own — the Canvas is self-contained.
  const [activeTabHint, setActiveTabHint] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activityCollapsed, setActivityCollapsed] = useState(false);
  // Track which surface turns have been acted on so we can show feedback.
  const [actedTurns, setActedTurns] = useState<Record<string, string>>({});
  const conversationEndRef = useRef<HTMLDivElement | null>(null);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setMounted(true);
    void boot();
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
  }, []);

  // Auto-scroll conversation to the bottom whenever content changes.
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [trace.length, turns.length, phase]);

  // Once a run completes, nudge the Canvas to show the first declared view.
  // The actual tab state lives inside ArtifactCanvas — we just set a hint.
  useEffect(() => {
    if (phase === "rendered") {
      setActiveTabHint(null); // reset, let Canvas auto-select first view
    }
  }, [phase]);

  const modeLabel = capabilities?.llm_enabled
    ? `LLM · ${capabilities.llm_provider} · ${capabilities.default_model ?? ""}`
    : "Deterministic mode";
  const isThinking = phase === "thinking";

  async function boot() {
    try {
      setError(null);
      const [bootstrap, runtime] = await Promise.all([
        getBootstrap(),
        apiFetch<RuntimeCapabilities>("/api/runtime/capabilities"),
      ]);
      setWorkspace(bootstrap.workspace);
      setProject(bootstrap.projects[0] ?? null);
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
            project_id: bootstrap.projects[0]?.id ?? null,
            channel: "web",
            metadata: { source: "cowork_surface_demo" },
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

  // Track the goal text that was actually submitted for the current round
  // so that archiving to history always captures the right label.
  const submittedGoalRef = useRef("");

  async function runReview(nextGoal = goal) {
    if (!workspace || !session || !nextGoal.trim() || isThinking) return;
    if (pollTimer.current) clearInterval(pollTimer.current);
    // Archive the current round into history if there's anything to show.
    if (trace.length > 0 || turns.length > 0) {
      setHistory((prev) => [
        ...prev,
        { id: run?.id ?? `h_${Date.now()}`, goal: submittedGoalRef.current, trace, turns, run, memories, actedTurns },
      ]);
    }
    submittedGoalRef.current = nextGoal.trim();
    setError(null);
    setActivityCollapsed(false);
    setTrace([]);
    setTurns([]);
    setRun(null);
    setActiveTabHint(null);
    setActedTurns({});
    setGoal("");
    setPhase("thinking");
    try {
      const message = await startConversationMessage(session.id, {
        content: nextGoal.trim(),
        attachments: [],
      });
      const newRunId = message.run_id;
      // Poll trace + surface-turns + run status until run terminates.
      pollTimer.current = setInterval(async () => {
        try {
          const [t, st, r] = await Promise.all([
            apiFetch<TraceStep[]>(`/api/runs/${newRunId}/trace`),
            fetchRunSurfaceTurns(newRunId),
            apiFetch<Run>(`/api/runs/${newRunId}`),
          ]);
          setTrace(t);
          setTurns(st);
          setRun(r);
          if (r.status === "completed" || r.status === "failed") {
            if (pollTimer.current) {
              clearInterval(pollTimer.current);
              pollTimer.current = null;
            }
            const memoryList = await apiFetch<Memory[]>(
              `/api/memories?workspace_id=${workspace.id}`,
            );
            // Only show memories from the current run to avoid showing
            // dozens of historical entries from previous sessions.
            setMemories(memoryList.filter((m) => m.source_run_id === newRunId));
            await refreshEvents(newRunId);
            // Detect what type of artifact was produced so we can suggest follow-ups.
            try {
              const arts = await apiFetch<Array<{ type: string; schema_json: Record<string, unknown> }>>(`/api/artifacts?workspace_id=${workspace.id}&task_id=${r.task_id}`);
              setLastArtifactType(arts[0]?.type ?? null);
              setLastArtifact(arts[0] ?? null);
            } catch { /* non-critical */ }
            setPhase(r.status === "failed" ? "error" : "rendered");
            setActivityCollapsed(true);
            // Clear the composer so follow-up suggestion chips appear.
            setGoal("");
          }
        } catch {
          /* transient errors during polling are fine; next tick retries */
        }
      }, 500);
    } catch (err) {
      setPhase("error");
      setError(err instanceof Error ? err.message : "Run failed.");
    }
  }

  async function refreshEvents(runId: string) {
    if (!workspace) return;
    try {
      const list = await apiFetch<InteractionEvent[]>(
        `/api/interactions?workspace_id=${workspace.id}&run_id=${runId}`,
      );
      setEvents(list);
    } catch {
      // ignore
    }
  }

  async function fireAction(turn: SurfaceTurn, event: TiloAction) {
    if (!session || !workspace) return;
    setError(null);
    try {
      const result = await executeSurfaceAction({
        surface: turn.surface_spec_json,
        actionId: event.action.id,
        workspaceId: workspace.id,
        sessionId: session.id,
        runId: turn.run_id,
        artifactId: turn.artifact_id ?? null,
        payload: event.payload ?? {},
      });
      // Layered effect: confirm/reject memory candidate when the surface
      // is a memory-confirmation surface.
      if (turn.intent === "confirm_memory") {
        const memoryList = await apiFetch<Memory[]>(
          `/api/memories?workspace_id=${workspace.id}`,
        );
        const candidate =
          memoryList.find(
            (m) => m.source_run_id === turn.run_id && m.status === "candidate",
          ) ?? memoryList.find((m) => m.status === "candidate");
        if (candidate) {
          if (result.action.action_type === "create_memory") {
            await apiFetch<Memory>(`/api/memories/${candidate.id}/confirm`, {
              method: "POST",
            });
          } else if (result.action.action_type === "reject") {
            await apiFetch<Memory>(`/api/memories/${candidate.id}/reject`, {
              method: "POST",
              body: JSON.stringify({ reason: "rejected_via_surface" }),
            });
          }
        }
      }
      // Refresh side panels after every action.
      const memoryList = await apiFetch<Memory[]>(
        `/api/memories?workspace_id=${workspace.id}`,
      );
      setMemories(memoryList.filter((m) => m.source_run_id === turn.run_id));
      if (turn.run_id) await refreshEvents(turn.run_id);
      // Mark the turn as "acted" so the UI shows a confirmation badge.
      setActedTurns((prev) => ({ ...prev, [turn.id]: event.action.action_type }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    }
  }

  function handleOpenInCanvas(turn: SurfaceTurn) {
    // For now, just open the Canvas. In the future, a smart heuristic can
    // map intent → view id, but we don't want to hardcode business logic.
    setInspectorOpen(true);
    // Hint: use first view if available; the Canvas ignores invalid ids.
    setActiveTabHint(null);
  }

  const visibleSteps = useMemo(() => trace.filter((step) => isUserVisibleStep(step.step_type)), [trace]);

  if (!mounted) {
    return <div className="acp-shell" suppressHydrationWarning />;
  }

  return (
    <div className="acp-shell">
      <header className="acp-topbar">
        <div className="acp-brand">
          <span className="acp-brand-dot">T</span>
          <div>
            <strong>Tilo</strong>
            <small>{t.tagline}</small>
          </div>
        </div>
        <div className="acp-topbar-tools">
          <ModeBadge label={modeLabel} llm={Boolean(capabilities?.llm_enabled)} />
          <button className="acp-icon-button" onClick={() => setLocale((l) => l === "en" ? "zh" : "en")} title="Toggle language" type="button">
            <span style={{ fontSize: 14 }}>🌐</span>
            <span>{t.lang}</span>
          </button>
          <button className="acp-icon-button" onClick={() => setDrawer("why")} title={t.whyTitle} type="button">
            <Sparkles size={16} />
            <span>Why this UI</span>
          </button>
          <button
            className={`acp-icon-button ${inspectorOpen ? "active" : ""}`}
            onClick={() => setInspectorOpen((open) => !open)}
            title="Toggle Canvas"
            type="button"
          >
            <PanelRightOpen size={16} />
            <span>{t.canvas}</span>
          </button>
        </div>
      </header>

      <main className={`acp-main ${inspectorOpen ? "with-inspector" : ""}`}>
        <section className="acp-conversation">
          <div className="acp-conversation-scroll">
            {phase === "idle" && trace.length === 0 && history.length === 0 ? (
              <ConversationIntro t={t} />
            ) : null}

            {/* Render completed rounds from history */}
            {history.map((round) => (
              <HistoryRoundBubbles key={round.id} round={round} onAction={fireAction} onOpenCanvas={handleOpenInCanvas} />
            ))}

            {/* Current round */}
            {trace.length || turns.length || phase !== "idle" ? (
              <UserBubble goal={submittedGoalRef.current} />
            ) : null}
            {(isThinking || trace.length > 0) ? (
              <ActivityBubble
                steps={visibleSteps}
                isThinking={isThinking}
                modeLabel={modeLabel}
                collapsed={activityCollapsed}
                onToggle={() => setActivityCollapsed((c) => !c)}
              />
            ) : null}
            {turns.map((turn) => (
              <SurfaceBubble
                key={turn.id}
                turn={turn}
                onAction={(event) => fireAction(turn, event)}
                onOpenCanvas={() => handleOpenInCanvas(turn)}
                actedAction={actedTurns[turn.id] ?? null}
              />
            ))}
            {phase === "rendered" && turns.length > 0 ? <RunDoneBubble run={run} turns={turns} /> : null}
            {error ? (
              <div className="acp-bubble error">
                <span>{error}</span>
              </div>
            ) : null}
            <div ref={conversationEndRef} />
          </div>

          <Composer
            disabled={!workspace || !session || isThinking}
            goal={goal}
            onGoalChange={setGoal}
            onSelectSample={(text) => void runReview(text)}
            onSubmit={() => void runReview()}
            phase={phase}
            lastArtifact={lastArtifact}
            locale={locale}
          />
        </section>

        {inspectorOpen ? (
          <aside className="acp-inspector">
            <ArtifactCanvas
              workspaceId={workspace?.id ?? null}
              run={run}
              turns={turns}
              memories={memories}
              modeLabel={modeLabel}
              activeTabHint={activeTabHint}
            />
          </aside>
        ) : null}
      </main>

      {drawer === "why" ? (
        <WhyDrawer onClose={() => setDrawer(null)} turns={turns} modeLabel={modeLabel} />
      ) : null}
    </div>
  );
}

function ConversationIntro({ t }: { t: Record<string, string> }) {
  return (
    <div className="acp-intro">
      <span className="acp-eyebrow">Tilo · Surface Protocol</span>
      <h1>{t.introTitle}</h1>
      <p>{t.introBody}</p>
      <ul className="acp-intro-points">
        <li><Activity size={14} /> {t.introTrace}</li>
        <li><Sparkles size={14} /> {t.introSurface}</li>
        <li><Database size={14} /> {t.introMemory}</li>
      </ul>
    </div>
  );
}

function UserBubble({ goal }: { goal: string }) {
  return (
    <article className="acp-bubble user">
      <div className="acp-bubble-body">{goal}</div>
    </article>
  );
}

function ActivityBubble({
  steps,
  isThinking,
  modeLabel,
  collapsed,
  onToggle,
}: {
  steps: TraceStep[];
  isThinking: boolean;
  modeLabel: string;
  collapsed: boolean;
  onToggle: () => void;
}) {
  const summary = isThinking
    ? steps.length === 0
      ? "Starting the run…"
      : describeStep(steps[steps.length - 1])
    : `Activity completed · ${steps.length} steps`;
  return (
    <article className="acp-bubble assistant">
      <div className="acp-avatar">
        {isThinking ? <Loader2 size={14} className="spin" /> : <Activity size={14} />}
      </div>
      <div className="acp-bubble-body activity">
        <button className="acp-activity-summary" onClick={onToggle} type="button">
          <span className="acp-chevron">{collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}</span>
          <strong>{summary}</strong>
          <small>{isThinking ? modeLabel : `${steps.length} steps`}</small>
        </button>
        {!collapsed ? (
          <ol className="acp-activity-list">
            {steps.map((step, index) => {
              const stateClass = stepStateClass(step, index, steps.length, isThinking);
              const isThinkingStream =
                step.step_type === "llm_generation" && step.status === "running" && Boolean(step.summary);
              return (
                <li key={step.id} className={`acp-activity-step ${stateClass}`}>
                  <span className="acp-activity-step-icon">{stepIcon(step.step_type)}</span>
                  <div className="acp-activity-step-body">
                    <strong>{describeStep(step)}</strong>
                    {isThinkingStream ? (
                      <ThinkingStream text={step.summary} />
                    ) : step.summary ? (
                      <span>{step.summary}</span>
                    ) : null}
                  </div>
                </li>
              );
            })}
            {isThinking ? (
              <li className="acp-activity-step pending">
                <span className="acp-activity-step-icon"><Loader2 size={12} className="spin" /></span>
                <div className="acp-activity-step-body">
                  <strong>Working…</strong>
                </div>
              </li>
            ) : null}
          </ol>
        ) : null}
      </div>
    </article>
  );
}

function SurfaceBubble({
  turn,
  onAction,
  onOpenCanvas,
  actedAction,
}: {
  turn: SurfaceTurn;
  onAction: (event: TiloAction) => void;
  onOpenCanvas: () => void;
  actedAction: string | null;
}) {
  return (
    <article className="acp-bubble assistant surface">
      <div className="acp-avatar surface">
        <Sparkles size={14} />
      </div>
      <div className="acp-bubble-body">
        <div className="acp-surface-meta">
          <span className="acp-intent-pill">{turn.intent.replace(/_/g, " ")}</span>
          <small>SurfaceTurn #{turn.ordinal} · {turn.composer_mode}</small>
          <button type="button" className="acp-chip open-canvas" onClick={onOpenCanvas}>
            <PanelRightOpen size={12} /> Open in Canvas
          </button>
        </div>
        <div className="acp-surface-card">
          {actedAction ? (
            <div className="acp-action-done">
              <CheckCircle2 size={13} />
              <span>Action recorded: <strong>{actedAction}</strong></span>
            </div>
          ) : (
            <TiloRenderer surface={turn.surface_spec_json} onAction={onAction} />
          )}
        </div>
      </div>
    </article>
  );
}

function RunDoneBubble({ run, turns }: { run: Run | null; turns: SurfaceTurn[] }) {
  return (
    <article className="acp-bubble assistant muted">
      <div className="acp-avatar">
        <CheckCircle2 size={14} />
      </div>
      <div className="acp-bubble-body">
        <strong>Run complete.</strong>
        <small>
          {turns.length} surface{turns.length === 1 ? "" : "s"} produced.
          {run?.result_summary ? ` ${run.result_summary}` : ""}
        </small>
      </div>
    </article>
  );
}

function Composer({
  disabled,
  goal,
  onGoalChange,
  onSelectSample,
  onSubmit,
  phase,
  lastArtifact,
  locale,
}: {
  disabled: boolean;
  goal: string;
  onGoalChange: (value: string) => void;
  onSelectSample: (text: string) => void;
  onSubmit: () => void;
  phase: RunPhase;
  lastArtifact: { type: string; schema_json: Record<string, unknown> } | null;
  locale: string;
}) {
  const t = UI_TEXT[locale];
  const followUps = useMemo(() => deriveFollowUps(lastArtifact, null, locale), [lastArtifact, locale]);
  const showSamples = phase === "idle" && !goal.trim();
  const showFollowUps = phase === "rendered" && followUps.length > 0 && !goal.trim();
  const samples = SAMPLE_GOALS[locale] ?? SAMPLE_GOALS.en;
  return (
    <form
      className="acp-composer"
      onSubmit={(event) => {
        event.preventDefault();
        if (!disabled) onSubmit();
      }}
    >
      <textarea
        aria-label="Goal"
        disabled={disabled}
        onChange={(event) => onGoalChange(event.target.value)}
        placeholder={t.placeholder}
        rows={2}
        value={goal}
      />
      {showSamples ? (
        <div className="acp-sample-chips">
          <span className="acp-sample-label">{t.trySample}</span>
          {samples.map((sg) => (
            <button key={sg.id} type="button" className="acp-chip" disabled={disabled} onClick={() => onSelectSample(sg.text)}>
              <span>{sg.icon}</span> {sg.label}
            </button>
          ))}
        </div>
      ) : null}
      {showFollowUps ? (
        <div className="acp-sample-chips">
          <span className="acp-sample-label">{t.followUpLabel}</span>
          {followUps.map((text, i) => (
            <button key={i} type="button" className="acp-chip followup" disabled={disabled} onClick={() => onSelectSample(text)}>
              <MessageSquare size={12} /> {text.length > 80 ? text.slice(0, 77) + "…" : text}
            </button>
          ))}
        </div>
      ) : null}
      <div className="acp-composer-row">
        <div />
        <button className="acp-send" disabled={disabled || !goal.trim()} type="submit">
          {phase === "thinking" ? <Loader2 size={14} className="spin" /> : <Search size={14} />}
          {phase === "idle" ? t.run : t.runAgain}
        </button>
      </div>
    </form>
  );
}

/** Collapsed view of a completed history round. */
function HistoryRoundBubbles({ round, onAction, onOpenCanvas }: { round: HistoryRound; onAction: (turn: SurfaceTurn, event: TiloAction) => void; onOpenCanvas: (turn: SurfaceTurn) => void }) {
  return (
    <>
      <UserBubble goal={round.goal} />
      <article className="acp-bubble assistant muted">
        <div className="acp-avatar"><Activity size={14} /></div>
        <div className="acp-bubble-body">
          <strong>Completed · {round.trace.length} steps · {round.turns.length} surface{round.turns.length === 1 ? "" : "s"}</strong>
        </div>
      </article>
      {round.turns.map((turn) => (
        <SurfaceBubble
          key={turn.id}
          turn={turn}
          onAction={(event) => onAction(turn, event)}
          onOpenCanvas={() => onOpenCanvas(turn)}
          actedAction={round.actedTurns[turn.id] ?? null}
        />
      ))}
    </>
  );
}

function ModeBadge({ label, llm }: { label: string; llm: boolean }) {
  return (
    <span className={`acp-mode-badge ${llm ? "live" : "deterministic"}`}>
      <span className="acp-dot" />
      {label}
    </span>
  );
}

function WhyDrawer({ onClose, turns, modeLabel }: { onClose: () => void; turns: SurfaceTurn[]; modeLabel: string }) {
  return (
    <div className="acp-drawer-overlay" onClick={onClose}>
      <aside className="acp-drawer" onClick={(e) => e.stopPropagation()}>
        <header>
          <div>
            <span className="acp-eyebrow">Inspectable internals</span>
            <h2>Why this UI?</h2>
          </div>
          <button onClick={onClose} type="button"><X size={16} /></button>
        </header>
        <div className="acp-drawer-body">
          <p>
            Tilo evaluates an <strong>InteractionPolicy</strong> on every plan step. For each step
            the policy answers: should this produce a surface, ask for text, or stay silent?
          </p>
          <div className="acp-drawer-stat">
            <strong>{turns.length}</strong>
            <span>surfaces produced this run</span>
          </div>
          <p>
            Each surface is a validated <code>tilo.surface.v1</code> SurfaceSpec composed from
            a closed block vocabulary (heading, decision, comparison, evidence, form…). The
            renderer never branches on app id — only on block type.
          </p>
          <p>
            The <strong>Canvas</strong> on the right is the domain workbench: for contract review
            it surfaces risks, a clause-linked reader, and a revision draft. Clicking "Open in
            Canvas" on a surface bubble jumps the canvas to the matching clause.
          </p>
          <p>
            <strong>Runtime mode:</strong> {modeLabel}.
          </p>
          <ul className="acp-drawer-points">
            <li><MessageSquare size={13} /> User input → Task → Run</li>
            <li><Brain size={13} /> Memory recall → Skill select → Tool calls</li>
            <li><Sparkles size={13} /> Per-step InteractionPolicy → SurfaceTurn</li>
            <li><Zap size={13} /> Each click → UIInteractionEvent (action stream)</li>
            <li><Database size={13} /> Reflection → Memory candidate → Confirmation</li>
          </ul>
        </div>
      </aside>
    </div>
  );
}

function ThinkingStream({ text }: { text: string }) {
  // Auto-scroll the thinking box to bottom so the newest tokens stay
  // visible while the model is still streaming.
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [text]);
  return (
    <div className="acp-thinking-stream" ref={ref}>
      <div className="acp-thinking-label">
        <Brain size={11} /> Thinking
      </div>
      <div className="acp-thinking-text">
        {text}
        <span className="acp-thinking-caret" />
      </div>
    </div>
  );
}

// ---- helpers ----

const STEP_LABELS: Record<string, { label: string; icon: JSX.Element }> = {
  recall_memory: { label: "Recalling relevant memory", icon: <Brain size={12} /> },
  select_skill: { label: "Selecting skill", icon: <Wrench size={12} /> },
  build_prompt: { label: "Building context", icon: <FileText size={12} /> },
  plan: { label: "Planning steps", icon: <Activity size={12} /> },
  invoke_tool: { label: "Invoking tool", icon: <Wrench size={12} /> },
  llm_generation: { label: "Calling the model", icon: <Brain size={12} /> },
  generate_artifact: { label: "Generating artifact", icon: <FileText size={12} /> },
  ask_confirmation: { label: "Preparing confirmation", icon: <Sparkles size={12} /> },
  policy_decision: { label: "Policy decision", icon: <Activity size={12} /> },
  render_surface: { label: "Rendering surface", icon: <Sparkles size={12} /> },
  extract_memory: { label: "Extracting memory candidates", icon: <Brain size={12} /> },
};

const HIDDEN_STEPS = new Set<string>(["build_prompt", "policy_decision"]); // internal plumbing, noisy for end users

function isUserVisibleStep(stepType: string): boolean {
  return !HIDDEN_STEPS.has(stepType);
}

function describeStep(step: TraceStep): string {
  // Prefer the runtime's own title — backend writes specific titles for many
  // step types (e.g. "Calling tencent · kimi-k2.6", "Render surface · request_approval").
  if (step.title && step.title !== step.step_type) return step.title;
  const meta = STEP_LABELS[step.step_type];
  return meta ? meta.label : step.step_type;
}

function stepIcon(stepType: string): JSX.Element {
  return STEP_LABELS[stepType]?.icon ?? <Activity size={12} />;
}

function stepStateClass(step: TraceStep, index: number, total: number, isThinking: boolean): string {
  if (step.status === "failed") return "failed";
  if (step.status === "running") return "active";
  if (isThinking && index === total - 1) return "active";
  return "done";
}


