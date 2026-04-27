"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Bot, Check, Code2, Database, FileText, GitBranch, Languages, MessageCircle, Play, RadioTower, RotateCcw, Send, ShieldCheck } from "lucide-react";
import { renderInteractionComponent } from "../interaction/registry";
import { apiFetch, getBootstrap, sendMessage } from "../../lib/api";
import type { Agent, Artifact, ArtifactAction, ArtifactBlock, Confirmation, Memory, Project, RuntimeCapabilities, TraceStep, UIInteractionEvent, Workspace } from "../../lib/types";

type Locale = "en" | "zh";
type ChatMessage = { id: string; role: "bot" | "user"; text: string; status?: string };
type DemoStage = "Intent" | "Risk Review" | "Approval" | "Revision Draft" | "Memory";
type LiveEvent = { id: string; label: string; detail: string; status?: "done" | "active" | "pending" };

const demoCopy = {
  en: {
    localeLabel: "English",
    otherLocaleLabel: "中文",
    demoGoal: "Review this contract for payment, liability, and termination risks.",
    languageInstruction: "Return the Contract Review artifact in English.",
    headerEyebrow: "Tilo Telegram-like Demo · ROAM Loop",
    headline: "Chat is the entry. Surface is the workspace. Interaction becomes memory.",
    subhead: "Chat starts the task. Tilo renders the surface. User actions become durable observations.",
    developerConsole: "Developer Console",
    github: "GitHub",
    botName: "Tilo Bot",
    online: "online",
    renderingWorkflow: "rendering workflow",
    welcome: "Welcome to Tilo. Send me a goal, or run a demo.",
    runDemo: "Run Contract Review Demo",
    replayDemo: "Replay Demo",
    openSurface: "Open Review Surface",
    approveRevision: "Approve Revision",
    remember: "Remember",
    openArtifactPage: "Open artifact page",
    received: "Received. Creating Task and Run from the chat entry.",
    recalling: "Recalling memory and selecting the Contract Review surface.",
    renderingSurface: "Rendering the Rich ROAM Surface now.",
    ready: (count: number) => `Contract Review is ready. ${count} high-risk clause${count === 1 ? "" : "s"} found. I opened the rich review surface.`,
    replayStarted: "Replay started. I will run the same contract review loop again.",
    userOpenSurface: "Open Review Surface",
    userApproved: "Approve Revision",
    approved: "Approved. Tilo is generating a conservative revision draft.",
    memoryReady: "Memory candidate ready. Should Tilo remember this review preference?",
    userRemember: "Remember this preference",
    remembered: "Remembered. Future contract reviews will use this preference.",
    runtimeDeterministic: "Demo mode: deterministic artifact generation",
    runtimeLlm: (provider: string, model: string) => `LLM mode: ${provider} · ${model}`,
    surfaceEyebrow: "Dynamic ROAM Surface",
    surfaceTitle: "Contract Review Surface",
    modeExplanation: "Deterministic mode runs locally with a safe artifact generator. LLM mode uses backend-only OpenAI-compatible config; API keys never reach the browser.",
    loadingEyebrow: "Render in progress",
    loadingTitle: "Generating the Contract Review surface",
    loadingBody: "Tilo is creating Task, Run, TraceStep, Artifact, Confirmation, and Memory candidates.",
    roamPhases: ["Render", "Observe", "Act", "Memorize"],
    stageRail: ["Intent", "Contract Intake", "Risk Review", "Approval", "Revision Draft", "Memory"],
    previewEyebrow: "Preview Flow",
    previewTitle: "Chat starts the task. Tilo renders the workspace.",
    previewBody: "A lightweight message launches a full ROAM surface for review, approval, revision, and memory.",
    previewSteps: [
      { title: "Chat entry", detail: "User sends a contract review goal." },
      { title: "Rich Surface", detail: "Tilo opens the review where dense UI belongs." },
      { title: "Approval", detail: "Human decision becomes a durable confirmation." },
      { title: "Revision", detail: "Approved action generates a focused draft." },
      { title: "Memory", detail: "Confirmed preference improves future work." }
    ],
    previewCardTitle: "Contract Review Surface",
    previewCardBody: "RiskReviewPanel is too rich for chat, so it opens here.",
    previewRisk: "Liability",
    highRisk: "high risk",
    activeRiskNode: "Active Risk Node",
    recommendedRevision: "Recommended revision",
    evidence: "Evidence",
    summaryHigh: "High",
    summaryMedium: "Medium",
    summaryLow: "Low",
    primaryApprove: "Approve Revision",
    rememberPreference: "Remember Preference",
    inspectorRendererDecision: "Renderer Decision",
    inspectorLiveEvents: "Live Events",
    inspectorRuntimeMode: "Runtime Mode",
    inspectorInteractionContract: "Interaction Contract",
    inspectorChannelRouting: "Channel Routing",
    inspectorDurableObservations: "Durable Observations",
    show: "show",
    hide: "hide",
    rendererDecisionRows: [
      "RiskReviewPanel routes rich review into the Rich Surface",
      "ApprovalCard renders as chat buttons",
      "MemoryCandidateCard can render in chat or surface"
    ],
    runtimeProviderFamily: "Provider family",
    runtimeTelegramBot: "Telegram live bot",
    configured: "configured",
    notConfigured: "not configured",
    frontendSecretNote: "Model exposed to frontend: no API key, mode only",
    pendingConfirmations: "pending confirmations",
    memories: "memories",
    traceSteps: "trace steps",
    stageTitle: {
      Intent: "Intent",
      "Risk Review": "Risk Review",
      Approval: "Approval",
      "Revision Draft": "Revision Draft",
      Memory: "Memory"
    },
    stageCopy: {
      Intent: "The chat-like entry captures user intent.",
      "Risk Review": "Rich contract review opens in the ROAM surface, not inside the chat thread.",
      Approval: "A lightweight approval can happen from chat or the rich surface.",
      "Revision Draft": "After approval, Tilo acts and renders the conservative revision draft.",
      Memory: "Confirmed preference becomes inspectable long-term memory."
    },
    liveEvents: {
      waitingGoal: "Waiting for user goal",
      notRendered: "Rich surface not rendered yet",
      noAction: "No action observed yet",
      noApproval: "No approval yet",
      noMemory: "Memory not created yet",
      goalReceived: "Goal received from Telegram-like chat",
      surfaceRendered: "Contract Review surface rendered",
      approvalClicked: "Approve Revision clicked from chat/surface",
      confirmationApproved: "Linked Confirmation approved",
      memoryPersisted: "Confirmed preference persisted to memory"
    }
  },
  zh: {
    localeLabel: "中文",
    otherLocaleLabel: "English",
    demoGoal: "请审查这份合同中的付款、责任限制和终止条款风险，并用简体中文输出合同审查结果。",
    languageInstruction: "请用简体中文输出 Contract Review artifact。JSON key 保持英文，但所有面向用户的字符串值必须是简体中文。",
    headerEyebrow: "Tilo 类 Telegram 演示 · ROAM Loop",
    headline: "聊天是入口，Surface 是工作区，交互会变成记忆。",
    subhead: "用户从聊天发起任务。Tilo 渲染结构化 Surface。用户动作会成为可追踪的观察记录。",
    developerConsole: "开发者控制台",
    github: "GitHub",
    botName: "Tilo Bot",
    online: "在线",
    renderingWorkflow: "正在渲染工作流",
    welcome: "欢迎使用 Tilo。你可以发送目标，也可以直接运行演示。",
    runDemo: "运行合同审查演示",
    replayDemo: "重放演示",
    openSurface: "打开审查 Surface",
    approveRevision: "批准修订",
    remember: "记住偏好",
    openArtifactPage: "打开 artifact 页面",
    received: "已收到。正在从聊天入口创建 Task 和 Run。",
    recalling: "正在召回记忆，并选择合同审查 Surface。",
    renderingSurface: "正在渲染 Rich ROAM Surface。",
    ready: (count: number) => `合同审查已完成。发现 ${count} 个高风险条款，我已打开结构化审查 Surface。`,
    replayStarted: "已开始重放。我会再次运行同一个合同审查 loop。",
    userOpenSurface: "打开审查 Surface",
    userApproved: "批准修订",
    approved: "已批准。Tilo 正在生成保守的合同修订草案。",
    memoryReady: "记忆候选已准备好。是否让 Tilo 记住这个审查偏好？",
    userRemember: "记住这个偏好",
    remembered: "已记住。之后的合同审查会使用这个偏好。",
    runtimeDeterministic: "演示模式：本地确定性 artifact 生成",
    runtimeLlm: (provider: string, model: string) => `LLM 模式：${provider} · ${model}`,
    surfaceEyebrow: "Dynamic ROAM Surface",
    surfaceTitle: "合同审查 Surface",
    modeExplanation: "确定性模式可在本地直接运行。LLM 模式只通过后端 OpenAI-compatible 配置调用模型，API key 不会进入浏览器。",
    loadingEyebrow: "正在 Render",
    loadingTitle: "正在生成合同审查 Surface",
    loadingBody: "Tilo 正在创建 Task、Run、TraceStep、Artifact、Confirmation 和 Memory candidate。",
    roamPhases: ["Render", "Observe", "Act", "Memorize"],
    stageRail: ["意图", "合同输入", "风险审查", "审批", "修订草案", "记忆"],
    previewEyebrow: "流程预览",
    previewTitle: "聊天发起任务，Tilo 渲染工作区。",
    previewBody: "一条轻量消息会启动完整的 ROAM Surface，用于审查、批准、修订和记忆。",
    previewSteps: [
      { title: "聊天入口", detail: "用户发送合同审查目标。" },
      { title: "Rich Surface", detail: "Tilo 在适合复杂交互的区域打开审查。" },
      { title: "审批", detail: "人的决定会成为持久 Confirmation。" },
      { title: "修订", detail: "批准后的动作会生成聚焦的草案。" },
      { title: "记忆", detail: "确认后的偏好会影响未来工作。" }
    ],
    previewCardTitle: "合同审查 Surface",
    previewCardBody: "RiskReviewPanel 太复杂，不适合塞进聊天气泡，所以会在这里打开。",
    previewRisk: "责任限制",
    highRisk: "高风险",
    activeRiskNode: "当前风险节点",
    recommendedRevision: "建议修订",
    evidence: "依据",
    summaryHigh: "高",
    summaryMedium: "中",
    summaryLow: "低",
    primaryApprove: "批准修订",
    rememberPreference: "记住偏好",
    inspectorRendererDecision: "渲染决策",
    inspectorLiveEvents: "实时事件",
    inspectorRuntimeMode: "运行模式",
    inspectorInteractionContract: "交互契约",
    inspectorChannelRouting: "通道路由",
    inspectorDurableObservations: "持久观察",
    show: "展开",
    hide: "收起",
    rendererDecisionRows: [
      "RiskReviewPanel 内容过重，进入 Rich Surface",
      "ApprovalCard 可以渲染成聊天按钮",
      "MemoryCandidateCard 可在聊天或 Surface 中呈现"
    ],
    runtimeProviderFamily: "Provider family",
    runtimeTelegramBot: "Telegram live bot",
    configured: "已配置",
    notConfigured: "未配置",
    frontendSecretNote: "前端只展示模式，不暴露 API key",
    pendingConfirmations: "待确认",
    memories: "记忆数",
    traceSteps: "trace 步数",
    stageTitle: {
      Intent: "意图",
      "Risk Review": "风险审查",
      Approval: "审批",
      "Revision Draft": "修订草案",
      Memory: "记忆"
    },
    stageCopy: {
      Intent: "聊天入口捕获用户意图。",
      "Risk Review": "复杂合同审查在 ROAM Surface 中打开，而不是塞进聊天消息。",
      Approval: "轻量审批可以来自聊天，也可以来自 Rich Surface。",
      "Revision Draft": "批准后，Tilo 执行动作并渲染保守修订草案。",
      Memory: "确认后的偏好会成为可检查的长期记忆。"
    },
    liveEvents: {
      waitingGoal: "等待用户目标",
      notRendered: "Rich surface 尚未渲染",
      noAction: "尚未观察到动作",
      noApproval: "尚未批准",
      noMemory: "尚未创建记忆",
      goalReceived: "从类 Telegram 聊天收到目标",
      surfaceRendered: "合同审查 Surface 已渲染",
      approvalClicked: "从聊天或 Surface 点击批准修订",
      confirmationApproved: "关联 Confirmation 已批准",
      memoryPersisted: "已确认的偏好已写入记忆"
    }
  }
};

type DemoCopy = (typeof demoCopy)["en"];

function initialLiveEvents(copy: DemoCopy): LiveEvent[] {
  return [
    { id: "channel.message.received", label: "channel.message.received", detail: copy.liveEvents.waitingGoal, status: "pending" },
    { id: "artifact.rendered", label: "artifact.rendered", detail: copy.liveEvents.notRendered, status: "pending" },
    { id: "artifact.action.clicked", label: "artifact.action.clicked", detail: copy.liveEvents.noAction, status: "pending" },
    { id: "confirmation.approved", label: "confirmation.approved", detail: copy.liveEvents.noApproval, status: "pending" },
    { id: "memory.candidate.created", label: "memory.candidate.created", detail: copy.liveEvents.noMemory, status: "pending" }
  ];
}

function initialMessages(copy: DemoCopy): ChatMessage[] {
  return [{ id: "welcome", role: "bot", text: copy.welcome }];
}

export function TelegramDemoPage() {
  const [locale, setLocale] = useState<Locale>("en");
  const copy = demoCopy[locale];
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [capabilities, setCapabilities] = useState<RuntimeCapabilities | null>(null);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [confirmations, setConfirmations] = useState<Confirmation[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [interactions, setInteractions] = useState<UIInteractionEvent[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages(copy));
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>(initialLiveEvents(copy));
  const [composer, setComposer] = useState(copy.demoGoal);
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

  function switchLocale(nextLocale: Locale) {
    const nextCopy = demoCopy[nextLocale];
    setLocale(nextLocale);
    setArtifact(null);
    setConfirmations([]);
    setTrace([]);
    setInteractions([]);
    setMessages(initialMessages(nextCopy));
    setLiveEvents(initialLiveEvents(nextCopy));
    setComposer(nextCopy.demoGoal);
    setStage("Intent");
    setError(null);
  }

  async function runDemo(content = copy.demoGoal) {
    if (!workspace) return;
    setBusy(true);
    setError(null);
    setStage("Intent");
    setLiveEvents((items) => advanceLiveEvent(items, "channel.message.received", copy.liveEvents.goalReceived));
    setMessages((items) => [
      ...items,
      { id: `user-${Date.now()}`, role: "user", text: content },
      { id: `bot-task-${Date.now()}`, role: "bot", text: copy.received, status: "typing" },
      { id: `bot-recall-${Date.now()}`, role: "bot", text: copy.recalling, status: "typing" },
      { id: `bot-loading-${Date.now()}`, role: "bot", text: copy.renderingSurface, status: "rendering" }
    ]);
    try {
      const response = await sendMessage({
        workspace_id: workspace.id,
        project_id: project?.id,
        agent_id: agent?.id,
        content: withLanguageInstruction(content, copy)
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
      setLiveEvents((items) => advanceLiveEvent(items, "artifact.rendered", copy.liveEvents.surfaceRendered));
      setMessages((items) => [
        ...items.filter((item) => item.status !== "rendering"),
        { id: `bot-ready-${Date.now()}`, role: "bot", text: copy.ready(riskCount) }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run Telegram-like demo");
    } finally {
      setBusy(false);
    }
  }

  async function replayDemo() {
    setArtifact(null);
    setConfirmations([]);
    setTrace([]);
    setInteractions([]);
    setLiveEvents(initialLiveEvents(copy));
    setMessages([
      ...initialMessages(copy),
      { id: `bot-replay-${Date.now()}`, role: "bot", text: copy.replayStarted }
    ]);
    setStage("Intent");
    await runDemo(composer || copy.demoGoal);
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
    setMessages((items) => [...items, { id: `user-open-${Date.now()}`, role: "user", text: copy.userOpenSurface }]);
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
        advanceLiveEvent(items, "artifact.action.clicked", copy.liveEvents.approvalClicked),
        "confirmation.approved",
        copy.liveEvents.confirmationApproved
      )
    );
    setMessages((items) => [
      ...items,
      { id: `user-approved-${Date.now()}`, role: "user", text: copy.userApproved },
      { id: `bot-approved-${Date.now()}`, role: "bot", text: copy.approved },
      { id: `bot-memory-ready-${Date.now()}`, role: "bot", text: copy.memoryReady }
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
          content: String(block.data.content || copy.remembered),
          confidence: Number(block.data.confidence || 0.75),
          status: "confirmed",
          is_confirmed: true,
          structured_payload: { artifact_id: artifact.id, block_id: block.id, channel: "telegram-demo" }
        })
      });
      setMemories((items) => [memory, ...items]);
    }
    setStage("Memory");
    setLiveEvents((items) => advanceLiveEvent(items, "memory.candidate.created", copy.liveEvents.memoryPersisted));
    setMessages((items) => [
      ...items,
      { id: `user-remember-${Date.now()}`, role: "user", text: copy.userRemember },
      { id: `bot-memory-${Date.now()}`, role: "bot", text: copy.remembered }
    ]);
  }

  const modeLabel = capabilities?.llm_enabled ? copy.runtimeLlm(capabilities.llm_provider, capabilities.default_model) : copy.runtimeDeterministic;
  const activeBlocks = useMemo(() => selectBlocksForStage(artifact, stage), [artifact, stage]);

  return (
    <main className="telegram-demo-page">
      <header className="telegram-demo-header">
        <div>
          <span className="eyebrow">{copy.headerEyebrow}</span>
          <h1>{copy.headline}</h1>
          <p>{copy.subhead}</p>
        </div>
        <nav>
          <button className="language-toggle" onClick={() => switchLocale(locale === "en" ? "zh" : "en")}><Languages size={14} /> {copy.otherLocaleLabel}</button>
          <a href="/workspace?mode=developer">{copy.developerConsole}</a>
          <a href="https://github.com/adam2go/tilo-framework" target="_blank" rel="noreferrer">{copy.github}</a>
        </nav>
      </header>

      <section className="telegram-demo-grid">
        <ChatSimulator
          artifact={artifact}
          busy={busy}
          composer={composer}
          copy={copy}
          messages={messages}
          onApprove={approveRevision}
          onChangeComposer={setComposer}
          onOpenSurface={openSurface}
          onRemember={rememberPreference}
          onReplay={() => void replayDemo()}
          onRun={() => void runDemo(composer || copy.demoGoal)}
        />
        <RichSurfacePreview
          activeBlocks={activeBlocks}
          artifact={artifact}
          busy={busy}
          copy={copy}
          error={error}
          modeLabel={modeLabel}
          onApprove={approveRevision}
          onRemember={rememberPreference}
          onReplay={() => void replayDemo()}
          stage={stage}
        />
        <DeveloperInspector
          capabilities={capabilities}
          confirmations={confirmations}
          copy={copy}
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
  copy,
  messages,
  onApprove,
  onChangeComposer,
  onOpenSurface,
  onRemember,
  onReplay,
  onRun
}: {
  artifact: Artifact | null;
  busy: boolean;
  composer: string;
  copy: DemoCopy;
  messages: ChatMessage[];
  onApprove: () => Promise<void>;
  onChangeComposer: (value: string) => void;
  onOpenSurface: () => Promise<void>;
  onRemember: () => Promise<void>;
  onReplay: () => void;
  onRun: () => void;
}) {
  return (
    <aside className="telegram-phone">
      <header>
        <div className="telegram-avatar"><Bot size={18} /></div>
        <div>
          <strong>{copy.botName}</strong>
          <span>{busy ? copy.renderingWorkflow : copy.online}</span>
        </div>
      </header>
      <div className="telegram-thread">
        {messages.map((message) => (
          <div className={`telegram-bubble ${message.role} ${message.status || ""}`} key={message.id}>
            {message.text}
            {message.status === "typing" || message.status === "rendering" ? <span className="typing-dots"><i /> <i /> <i /></span> : null}
          </div>
        ))}
        <div className="telegram-inline-actions">
          <button onClick={onRun} disabled={busy}><Play size={14} /> {copy.runDemo}</button>
          <button onClick={onReplay} disabled={busy}><RotateCcw size={14} /> {copy.replayDemo}</button>
          <button onClick={() => void onOpenSurface()} disabled={!artifact}><ArrowUpRight size={14} /> {copy.openSurface}</button>
          <button onClick={() => void onApprove()} disabled={!artifact}><Check size={14} /> {copy.approveRevision}</button>
          <button onClick={() => void onRemember()} disabled={!artifact}><Database size={14} /> {copy.remember}</button>
        </div>
      </div>
      {artifact ? <a className="telegram-artifact-link" href={`/artifacts/${artifact.id}?channel=telegram-demo`}>{copy.openArtifactPage}</a> : null}
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
  copy,
  error,
  modeLabel,
  onApprove,
  onRemember,
  onReplay,
  stage
}: {
  activeBlocks: ArtifactBlock[];
  artifact: Artifact | null;
  busy: boolean;
  copy: DemoCopy;
  error: string | null;
  modeLabel: string;
  onApprove: () => Promise<void>;
  onRemember: () => Promise<void>;
  onReplay: () => void;
  stage: DemoStage;
}) {
  return (
    <section className="telegram-rich-surface">
      <div className="surface-topline">
        <div>
          <span className="eyebrow">{copy.surfaceEyebrow}</span>
          <h2>{artifact?.title || copy.surfaceTitle}</h2>
        </div>
        <span className={modeLabel.startsWith("LLM") ? "runtime-badge llm" : "runtime-badge"}>{modeLabel}</span>
      </div>
      <p className="surface-explainer">
        {copy.modeExplanation}
      </p>
      <div className="roam-mini-strip">
        {copy.roamPhases.map((item) => <span className={roamPhaseForStage(stage, item) ? "active" : ""} key={item}>{item}</span>)}
      </div>
      <div className="showcase-stage-rail">
        {copy.stageRail.map((item, index) => (
          <span className={index <= stageIndex(stage, busy) ? "active" : ""} key={item}>{item}</span>
        ))}
      </div>
      {busy ? (
        <div className="surface-loading-hero">
          <div>
            <MessageCircle size={26} />
          </div>
          <span className="eyebrow">{copy.loadingEyebrow}</span>
          <strong>{copy.loadingTitle}</strong>
          <p>{copy.loadingBody}</p>
        </div>
      ) : null}
      {!busy && !artifact ? (
        <InitialSurfacePreview copy={copy} />
      ) : null}
      {error ? <div className="error-box">{error}</div> : null}
      {artifact ? (
        <div className="telegram-surface-blocks">
          <div className="stage-context">
            <span>{copy.stageTitle[stage]}</span>
            <p>{stageCopy(stage, copy)}</p>
          </div>
          <FocusedContractSurface artifact={artifact} blocks={activeBlocks} copy={copy} stage={stage} />
          <div className="surface-primary-actions">
            <button className="primary-button" onClick={() => void onApprove()} disabled={stage === "Revision Draft" || stage === "Memory"}>{copy.primaryApprove}</button>
            <button className="secondary-action" onClick={() => void onRemember()}>{copy.rememberPreference}</button>
            <button className="secondary-action" onClick={onReplay}>{copy.replayDemo}</button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function InitialSurfacePreview({ copy }: { copy: DemoCopy }) {
  const steps = [
    { icon: <MessageCircle size={16} />, ...copy.previewSteps[0] },
    { icon: <FileText size={16} />, ...copy.previewSteps[1] },
    { icon: <ShieldCheck size={16} />, ...copy.previewSteps[2] },
    { icon: <GitBranch size={16} />, ...copy.previewSteps[3] },
    { icon: <Database size={16} />, ...copy.previewSteps[4] }
  ];
  return (
    <div className="telegram-preview-surface">
      <div className="preview-hero-card">
        <span className="eyebrow">{copy.previewEyebrow}</span>
        <h3>{copy.previewTitle}</h3>
        <p>{copy.previewBody}</p>
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
          <strong>{copy.previewCardTitle}</strong>
          <span>{copy.previewCardBody}</span>
        </div>
        <div className="preview-risk-node">
          <b>{copy.previewRisk}</b>
          <em>{copy.highRisk}</em>
        </div>
      </div>
    </div>
  );
}

function FocusedContractSurface({ artifact, blocks, copy, stage }: { artifact: Artifact; blocks: ArtifactBlock[]; copy: DemoCopy; stage: DemoStage }) {
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
            <span>{copy.summaryHigh}</span>
          </div>
          <div>
            <strong>{String(riskSummaryBlock.data.medium_count || 0)}</strong>
            <span>{copy.summaryMedium}</span>
          </div>
          <div>
            <strong>{String(riskSummaryBlock.data.low_count || 0)}</strong>
            <span>{copy.summaryLow}</span>
          </div>
          <p>{String(riskSummaryBlock.data.summary || "")}</p>
        </div>
      ) : null}

      {activeRisk ? (
        <article className="active-risk-node">
          <div className="active-risk-heading">
            <div>
              <span className="eyebrow">{copy.activeRiskNode}</span>
              <h3>{String(activeRisk.clause || "Contract risk")}</h3>
            </div>
            <em>{String(activeRisk.risk_level || "medium")}</em>
          </div>
          <p>{String(activeRisk.issue || "")}</p>
          <div className="revision-callout">
            <strong>{copy.recommendedRevision}</strong>
            <span>{String(activeRisk.suggested_revision || "")}</span>
          </div>
          {activeRisk.evidence ? <small>{copy.evidence}: {String(activeRisk.evidence)}</small> : null}
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
  copy,
  interactions,
  liveEvents,
  memories,
  modeLabel,
  trace
}: {
  capabilities: RuntimeCapabilities | null;
  confirmations: Confirmation[];
  copy: DemoCopy;
  interactions: UIInteractionEvent[];
  liveEvents: LiveEvent[];
  memories: Memory[];
  modeLabel: string;
  trace: TraceStep[];
}) {
  return (
    <aside className="telegram-dev-inspector">
      <InspectorCard icon={<GitBranch size={16} />} title={copy.inspectorRendererDecision}>
        {copy.rendererDecisionRows.map((row) => <span key={row}>{row}</span>)}
      </InspectorCard>
      <InspectorCard icon={<MessageCircle size={16} />} title={copy.inspectorLiveEvents}>
        {liveEvents.map((event) => (
          <span className={`live-event ${event.status || "pending"}`} key={event.id}>
            {event.label}: {event.detail}
          </span>
        ))}
      </InspectorCard>
      <InspectorCard icon={<ShieldCheck size={16} />} title={copy.inspectorRuntimeMode}>
        <strong>{modeLabel}</strong>
        <span>{copy.runtimeProviderFamily}: {capabilities?.llm_provider_family || "openai_compatible"}</span>
        <span>{copy.runtimeTelegramBot}: {capabilities?.telegram_enabled ? copy.configured : copy.notConfigured}</span>
        <span>{copy.frontendSecretNote}</span>
      </InspectorCard>
      <details className="inspector-card inspector-collapsible">
        <summary data-show-label={copy.show} data-hide-label={copy.hide}><Code2 size={16} /><strong>{copy.inspectorInteractionContract}</strong></summary>
        <div>
          <code>when: risk.detected</code>
          <code>condition: risk_level == high</code>
          <code>render: RiskReviewPanel</code>
          <code>observe: approve_revision</code>
          <code>act: generate_revised_clause</code>
          <code>memorize: user_preference</code>
        </div>
      </details>
      <details className="inspector-card inspector-collapsible">
        <summary data-show-label={copy.show} data-hide-label={copy.hide}><RadioTower size={16} /><strong>{copy.inspectorChannelRouting}</strong></summary>
        <div>
          <span>ApprovalCard to Telegram buttons</span>
          <span>RiskReviewPanel to Open rich surface</span>
          <span>EditableDocument to Open artifact page</span>
          <span>MemoryCandidate to Chat or surface</span>
        </div>
      </details>
      <InspectorCard icon={<Database size={16} />} title={copy.inspectorDurableObservations}>
        {interactions.slice(0, 5).map((event) => <span key={event.id}>{event.event_type}</span>)}
        {!interactions.length ? <span>channel.message.received</span> : null}
        <span>{copy.pendingConfirmations}: {confirmations.length}</span>
        <span>{copy.memories}: {memories.length}</span>
        <span>{copy.traceSteps}: {trace.length}</span>
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

function stageCopy(stage: DemoStage, copy: DemoCopy) {
  return copy.stageCopy[stage];
}

function withLanguageInstruction(content: string, copy: DemoCopy) {
  return `${content.trim()}\n\n${copy.languageInstruction}`;
}

function stageIndex(stage: DemoStage, busy: boolean) {
  if (busy) return 1;
  const index: Record<DemoStage, number> = {
    Intent: 0,
    "Risk Review": 2,
    Approval: 3,
    "Revision Draft": 4,
    Memory: 5
  };
  return index[stage];
}

function roamPhaseForStage(stage: DemoStage, phase: string) {
  const active: Record<DemoStage, string[]> = {
    Intent: ["Render"],
    "Risk Review": ["Render", "Observe"],
    Approval: ["Observe"],
    "Revision Draft": ["Act"],
    Memory: ["Memorize"]
  };
  return active[stage]?.includes(phase);
}

function advanceLiveEvent(items: LiveEvent[], eventId: string, detail: string): LiveEvent[] {
  return items.map((event) => event.id === eventId ? { ...event, detail, status: "done" as const } : event);
}
