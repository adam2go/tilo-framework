"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { ArrowUpRight, Bot, Check, Code2, Database, FileText, Languages, MessageCircle, RotateCcw, Send, ShieldCheck, X } from "lucide-react";
import { apiFetch, getBootstrap, sendMessage } from "../../lib/api";
import { SAMPLE_CONTRACT_FALLBACK_FILE_NAME } from "../../lib/demoContracts";
import type { ConversationEvent } from "../../lib/conversationEvents";
import { settlePendingConversationEvents } from "../../lib/conversationEvents";
import type { DemoContractFixture, FollowUpIntent, FollowUpIntentResult } from "../../lib/demoContracts";
import { interactionPolicyService } from "../../lib/interactionPolicy";
import type { InteractionDecision } from "../../lib/interactionPolicy";
import { getMiniSurfaceRegistration } from "../../lib/miniSurfaceRegistry";
import type { MiniSurfaceType } from "../../lib/miniSurfaceRegistry";
import type { Agent, Artifact, ArtifactAction, Confirmation, Memory, Project, RuntimeCapabilities, TraceStep, UIInteractionEvent, Workspace } from "../../lib/types";

type Locale = "en" | "zh";
type InputMode = "sample" | "paste";
type DemoStage = "Intent" | "Risk Review" | "Revision Draft" | "Memory";
type SurfaceKind = MiniSurfaceType;
type MemoryLifecycle = "none" | "candidate" | "confirmed" | "saved";
type ChatTurn = ConversationEvent;
type LiveEvent = { id: string; label: string; detail: string; status?: "done" | "active" | "pending" };

const demoCopy = {
  en: {
    otherLocaleLabel: "中文",
    demoGoal: "Review this AI service agreement, focusing on payment, acceptance, data compliance, IP, liability, and termination risks.",
    languageInstruction: "Return the Contract Review artifact in English.",
    title: "Tilo Conversational Surface Demo",
    subtitle: "A Telegram-like agent session where UI cards appear inside the conversation and user actions become observations.",
    thesis: "Conversation is the main interface. Mini surfaces appear when chat is not enough.",
    botName: "Tilo Bot",
    online: "online",
    thinking: "working",
    welcome: "Welcome to Tilo. Send a contract review goal, or run the sample demo.",
    sampleMode: "Use sample contract",
    pasteMode: "Paste contract",
    pastePlaceholder: "Paste contract text here. Press send to start the same Task -> Run -> Artifact loop.",
    sampleAttachmentDetail: "Problematic AI service agreement · 12 sections · realistic fixture",
    pastedAttachmentName: "Pasted contract text",
    pastedAttachmentDetail: (chars: number) => `${chars.toLocaleString()} characters · user-provided contract`,
    sampleUnavailable: "Sample contract is still loading. Try again in a moment.",
    runSample: "Run sample",
    replay: "Replay",
    reset: "Reset",
    inspector: "Inspector",
    stagePrefix: "Stage",
    stageIntent: "Intent",
    stageRiskReview: "Risk Review",
    stageRevisionDraft: "Revision Draft",
    stageMemory: "Memory",
    openArtifact: "Open Artifact",
    openFullReview: "Open Full Review",
    approveRevision: "Approve Revision",
    editDirection: "Edit Direction",
    remember: "Remember",
    notNow: "Not now",
    makeSofter: "Make softer",
    makeStricter: "Make stricter",
    draftEmail: "Draft negotiation email",
    received: "Received. I’m creating a Task and Run from this chat message.",
    readingContract: "Reading the attached contract from the sample fixture.",
    identifyingSections: "Identifying sections: scope, acceptance, payment, data, IP, SLA, confidentiality, liability, termination, and disputes.",
    scanningRisks: "Scanning risks against the contract text and recalled memory.",
    placingFullReview: "Most findings are being placed into the full review artifact.",
    rendering: "I’ll show only the key liability decision here because it affects the revision strategy.",
    ready: (count: number) => `I found ${count} high-risk issue${count === 1 ? "" : "s"} in the full contract. One needs direction now: clauses 8.1 and 8.2 conflict on liability cap and indemnity carve-outs.`,
    approvedObservation: "Observation: You approved a conservative revision for the liability and indemnity conflict in clauses 8.1 / 8.2.",
    approvedReply: "Got it. I’m generating a conservative but explainable revision draft for those clauses.",
    memoryPrompt: "I noticed you prefer conservative but negotiation-friendly revisions. Should I remember this?",
    memoryCandidateProposed: "Memory candidate proposed: conservative but negotiation-friendly contract revisions.",
    memoryConfirmed: "Memory confirmed by user.",
    memorySaved: "Memory saved to workspace memory.",
    rememberedObservation: "Observation: You confirmed this memory candidate.",
    rememberedReply: "Remembered. Future contract reviews will use this preference.",
    notNowObservation: "Observation: You skipped memory capture for now.",
    followupObservation: "Observation: Your follow-up preference was captured for this artifact.",
    followupReplies: {
      explain_risk: "The issue is that 8.1 looks like a cap, but 8.2 removes broad categories from that cap. That can make the cap unreliable in the exact cases that usually matter most.",
      revise_tone: "Understood. I’ll make the revision tone suitable for customer negotiation rather than overly aggressive.",
      focus_clause: "I’ll keep the focus on the clause you named and connect it back to the 8.1 / 8.2 liability strategy.",
      draft_email: "I’ll frame the revision as a negotiation email with business rationale, not as a hard rejection.",
      remember_preference: "That sounds like a reusable review preference. I’ll propose it as memory before applying it to future contract reviews.",
      general_followup: "I’ll keep that instruction attached to this review and apply it to the revision direction."
    },
    intentLabels: {
      explain_risk: "explain risk",
      revise_tone: "revise tone",
      focus_clause: "focus clause",
      draft_email: "draft email",
      remember_preference: "remember preference",
      general_followup: "general follow-up"
    },
    editObservation: "Observation: You asked to adjust the revision direction.",
    editReply: "Tell me the direction in the composer, for example: keep it firm but customer-friendly.",
    followupSuggestion: "Keep the tone customer-friendly and suitable for negotiation.",
    fullReviewObservation: "Observation: You opened the rich artifact for the complete finding list.",
    memoryLifecycle: "Memory lifecycle",
    memoryLifecycleLabels: {
      none: "No memory proposal yet",
      candidate: "Candidate proposed",
      confirmed: "User confirmed",
      saved: "Memory saved"
    },
    runtimeDeterministic: "Deterministic mode",
    runtimeLlm: (provider: string, model: string) => `LLM mode · ${provider} · ${model}`,
    noSecrets: "API keys stay backend-only.",
    contractReview: "ContractReviewMiniSurface",
    revisionDraft: "RevisionDraftMiniSurface",
    memoryCandidate: "MemoryCandidateMiniSurface",
    riskSummary: "Risk summary",
    activeRisk: "Primary issue",
    recommendedRevision: "Recommended revision",
    evidence: "Evidence",
    high: "High",
    medium: "Medium",
    low: "Low",
    revisionPreview: "Revision draft preview",
    before: "Before",
    after: "After",
    memoryWhy: "Tilo suggests remembering this because it can improve future contract reviews.",
    rendererDecision: "Renderer Decision",
    liveEvents: "Live Events",
    runtimeMode: "Runtime Mode",
    modelDiagnostics: "Model Diagnostics",
    interactionContract: "Interaction Contract",
    durableObservations: "Durable Observations",
    provider: "Provider",
    model: "Model",
    mode: "Mode",
    fallback: "Fallback",
    yes: "yes",
    no: "no",
    traceSteps: "trace steps",
    memories: "memories",
    confirmations: "pending confirmations",
    live: {
      waitingGoal: "Waiting for user goal",
      notRendered: "No mini surface rendered yet",
      noAction: "No UI action observed yet",
      noApproval: "No approval yet",
      noMemory: "No memory confirmed yet",
      goalReceived: "Chat message received",
      surfaceRendered: "ContractReviewMiniSurface inserted",
      approvalClicked: "Approve Revision clicked",
      confirmationApproved: "Linked Confirmation approved",
      memoryPersisted: "Memory candidate persisted"
    }
  },
  zh: {
    otherLocaleLabel: "English",
    demoGoal: "请审查这份 AI 客服系统服务合同，重点关注付款、验收、数据合规、知识产权、责任限制和终止条款。",
    languageInstruction: "请用简体中文输出 Contract Review artifact。JSON key 保持英文，但所有面向用户的字符串值必须是简体中文。",
    title: "Tilo 会话式 Surface 演示",
    subtitle: "一个类 Telegram 的 agent 会话：UI 卡片在聊天中出现，用户动作会成为观察记录。",
    thesis: "会话是主界面。聊天不够表达时，mini surface 会自然出现。",
    botName: "Tilo Bot",
    online: "在线",
    thinking: "处理中",
    welcome: "欢迎使用 Tilo。发送合同审查目标，或直接运行样例演示。",
    sampleMode: "使用样例合同",
    pasteMode: "粘贴合同",
    pastePlaceholder: "在这里粘贴合同文本。发送后会进入同一个 Task -> Run -> Artifact loop。",
    sampleAttachmentDetail: "问题样例 AI 服务合同 · 12 个章节 · 真实感 fixture",
    pastedAttachmentName: "粘贴的合同文本",
    pastedAttachmentDetail: (chars: number) => `${chars.toLocaleString()} 个字符 · 用户提供的合同`,
    sampleUnavailable: "样例合同还在加载，请稍后再试。",
    runSample: "运行样例",
    replay: "重放",
    reset: "重置",
    inspector: "Inspector",
    stagePrefix: "阶段",
    stageIntent: "意图",
    stageRiskReview: "风险审查",
    stageRevisionDraft: "修订草案",
    stageMemory: "记忆",
    openArtifact: "打开 Artifact",
    openFullReview: "打开完整审查",
    approveRevision: "批准修订",
    editDirection: "调整方向",
    remember: "记住",
    notNow: "暂不",
    makeSofter: "语气更柔和",
    makeStricter: "更严格",
    draftEmail: "起草谈判邮件",
    received: "已收到。正在从这条聊天消息创建 Task 和 Run。",
    readingContract: "正在读取样例 fixture 中的合同附件。",
    identifyingSections: "正在识别范围、验收、付款、数据、知识产权、SLA、保密、责任、解除和争议解决章节。",
    scanningRisks: "正在结合合同文本和召回记忆扫描风险。",
    placingFullReview: "大部分 findings 会进入完整审查 artifact。",
    rendering: "这里只展示一个关键责任决策，因为它会影响修订策略。",
    ready: (count: number) => `我在完整合同中发现 ${count} 个高风险问题。当前需要先确认的是：8.1 与 8.2 在责任上限和赔偿例外上存在冲突。`,
    approvedObservation: "Observation：你批准了针对 8.1 / 8.2 责任与赔偿冲突的保守修订方向。",
    approvedReply: "收到。我会为这两个条款生成一版保守但有解释空间的修订草案。",
    memoryPrompt: "我注意到你偏好保守但适合谈判的修订。要让我记住吗？",
    memoryCandidateProposed: "已提出记忆候选：保守但谈判友好的合同修订风格。",
    memoryConfirmed: "用户已确认该记忆。",
    memorySaved: "记忆已保存到 workspace memory。",
    rememberedObservation: "Observation：你确认了这个记忆候选。",
    rememberedReply: "已记住。未来合同审查会使用这个偏好。",
    notNowObservation: "Observation：你暂时跳过了记忆保存。",
    followupObservation: "Observation：你的谈判语气偏好已记录到当前 artifact 上。",
    followupReplies: {
      explain_risk: "这个问题的核心是：8.1 看起来设置了责任上限，但 8.2 又把大量关键场景排除在上限之外，导致上限在真正高风险场景下可能失效。",
      revise_tone: "明白。我会把修订建议调整成更适合发给客户谈判的表达，而不是直接否定对方条款。",
      focus_clause: "我会把重点放在你提到的条款上，并把它和 8.1 / 8.2 的责任策略关联起来。",
      draft_email: "我会把修订建议组织成适合发给客户的谈判邮件，并保留商业理由。",
      remember_preference: "这是一个可复用的审查偏好。我会先把它作为记忆候选提交给你确认。",
      general_followup: "我会把这条指令记录到当前审查中，并用于后续修订方向。"
    },
    intentLabels: {
      explain_risk: "解释风险",
      revise_tone: "调整语气",
      focus_clause: "聚焦条款",
      draft_email: "起草邮件",
      remember_preference: "记住偏好",
      general_followup: "一般追问"
    },
    editObservation: "Observation：你要求调整修订方向。",
    editReply: "请在输入框里告诉我方向，例如：语气不要太强硬，适合发给客户谈判。",
    followupSuggestion: "语气不要太强硬，适合发给客户谈判。",
    fullReviewObservation: "Observation：你打开了完整 artifact 查看全部 findings。",
    memoryLifecycle: "记忆生命周期",
    memoryLifecycleLabels: {
      none: "尚未提出记忆",
      candidate: "已提出候选",
      confirmed: "用户已确认",
      saved: "记忆已保存"
    },
    runtimeDeterministic: "确定性模式",
    runtimeLlm: (provider: string, model: string) => `LLM 模式 · ${provider} · ${model}`,
    noSecrets: "API key 只在后端使用。",
    contractReview: "ContractReviewMiniSurface",
    revisionDraft: "RevisionDraftMiniSurface",
    memoryCandidate: "MemoryCandidateMiniSurface",
    riskSummary: "风险摘要",
    activeRisk: "主要问题",
    recommendedRevision: "建议修订",
    evidence: "依据",
    high: "高",
    medium: "中",
    low: "低",
    revisionPreview: "修订草案预览",
    before: "修订前",
    after: "修订后",
    memoryWhy: "Tilo 建议记住它，因为这能改善未来的合同审查。",
    rendererDecision: "渲染决策",
    liveEvents: "实时事件",
    runtimeMode: "运行模式",
    modelDiagnostics: "模型诊断",
    interactionContract: "交互契约",
    durableObservations: "持久观察",
    provider: "Provider",
    model: "Model",
    mode: "Mode",
    fallback: "Fallback",
    yes: "是",
    no: "否",
    traceSteps: "trace 步数",
    memories: "记忆数",
    confirmations: "待确认",
    live: {
      waitingGoal: "等待用户目标",
      notRendered: "尚未渲染 mini surface",
      noAction: "尚未观察到 UI 动作",
      noApproval: "尚未批准",
      noMemory: "尚未确认记忆",
      goalReceived: "收到聊天消息",
      surfaceRendered: "已插入 ContractReviewMiniSurface",
      approvalClicked: "点击批准修订",
      confirmationApproved: "关联 Confirmation 已批准",
      memoryPersisted: "记忆候选已持久化"
    }
  }
};

type DemoCopy = (typeof demoCopy)["en"];

function initialLiveEvents(copy: DemoCopy): LiveEvent[] {
  return [
    { id: "channel.message.received", label: "channel.message.received", detail: copy.live.waitingGoal, status: "pending" },
    { id: "artifact.rendered", label: "artifact.rendered", detail: copy.live.notRendered, status: "pending" },
    { id: "artifact.action.clicked", label: "artifact.action.clicked", detail: copy.live.noAction, status: "pending" },
    { id: "confirmation.approved", label: "confirmation.approved", detail: copy.live.noApproval, status: "pending" },
    { id: "memory.candidate.created", label: "memory.candidate.created", detail: copy.live.noMemory, status: "pending" }
  ];
}

function initialTurns(copy: DemoCopy): ChatTurn[] {
  return [
    { id: "welcome", type: "agent_message", content: copy.welcome },
    { id: "thesis", type: "system_event", content: copy.thesis }
  ];
}

export function TelegramDemoPage() {
  const [locale, setLocale] = useState<Locale>("en");
  const copy = demoCopy[locale];
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [capabilities, setCapabilities] = useState<RuntimeCapabilities | null>(null);
  const [sampleContract, setSampleContract] = useState<DemoContractFixture | null>(null);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [confirmations, setConfirmations] = useState<Confirmation[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [interactions, setInteractions] = useState<UIInteractionEvent[]>([]);
  const [turns, setTurns] = useState<ChatTurn[]>(initialTurns(copy));
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>(initialLiveEvents(copy));
  const [composer, setComposer] = useState(copy.demoGoal);
  const [inputMode, setInputMode] = useState<InputMode>("sample");
  const [stage, setStage] = useState<DemoStage>("Intent");
  const [lastIntent, setLastIntent] = useState<FollowUpIntentResult | null>(null);
  const [memoryLifecycle, setMemoryLifecycle] = useState<MemoryLifecycle>("none");
  const [lastPolicyDecision, setLastPolicyDecision] = useState<InteractionDecision | null>(null);
  const [fullReviewOpen, setFullReviewOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);

  useEffect(() => {
    void boot();
  }, []);

  async function boot() {
    const [bootstrap, runtime, contract] = await Promise.all([
      getBootstrap(),
      apiFetch<RuntimeCapabilities>("/api/runtime/capabilities"),
      apiFetch<DemoContractFixture>("/api/demo/contracts/problematic-ai-service-agreement")
    ]);
    setWorkspace(bootstrap.workspace);
    setProject(bootstrap.projects[0] || null);
    setAgent(bootstrap.agents[0] || null);
    setCapabilities(runtime);
    setSampleContract(contract);
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
    setTurns(initialTurns(nextCopy));
    setLiveEvents(initialLiveEvents(nextCopy));
    setComposer(nextCopy.demoGoal);
    setInputMode("sample");
    setStage("Intent");
    setLastIntent(null);
    setMemoryLifecycle("none");
    setLastPolicyDecision(null);
    setFullReviewOpen(false);
  }

  function resetDemo() {
    setArtifact(null);
    setConfirmations([]);
    setTrace([]);
    setInteractions([]);
    setTurns(initialTurns(copy));
    setLiveEvents(initialLiveEvents(copy));
    setComposer(inputMode === "sample" ? copy.demoGoal : "");
    setStage("Intent");
    setLastIntent(null);
    setMemoryLifecycle("none");
    setLastPolicyDecision(null);
    setFullReviewOpen(false);
  }

  async function submitMessage() {
    if (!workspace || busy) return;
    if (!artifact) {
      if (inputMode === "sample" && !sampleContract) {
        setTurns((items) => [...items, { id: id("sample-loading"), type: "agent_message", content: copy.sampleUnavailable }]);
        return;
      }
      await runInitialReview(buildDemoMessage(copy, inputMode, composer, sampleContract), userMessagePreview(copy, inputMode, composer), inputMode);
      return;
    }
    await handleFollowUp(composer.trim());
  }

  async function runInitialReview(content: string, preview: string, sourceMode: InputMode) {
    if (!workspace) return;
    setBusy(true);
    setStage("Intent");
    setLiveEvents((items) => advanceLiveEvent(items, "channel.message.received", copy.live.goalReceived));
    setTurns((items) => [
      ...items,
      { id: id("user"), type: "user_message", content: preview },
      contractAttachmentTurn(copy, sourceMode, content, sampleContract),
      { id: id("bot-task"), type: "agent_message", content: copy.received, status: "typing" },
      { id: id("bot-read-contract"), type: "agent_message", content: copy.readingContract, status: "typing" },
      { id: id("bot-identify-sections"), type: "agent_message", content: copy.identifyingSections, status: "typing" },
      { id: id("bot-scan-risks"), type: "agent_message", content: copy.scanningRisks, status: "typing" },
      { id: id("bot-full-review"), type: "agent_message", content: copy.placingFullReview, status: "typing" },
      { id: id("bot-render"), type: "agent_message", content: copy.rendering, status: "rendering" }
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
      setLiveEvents((items) => advanceLiveEvent(items, "artifact.rendered", copy.live.surfaceRendered));
      const decision = interactionPolicyService.evaluate({
        event: "artifact_ready",
        artifact: nextArtifact,
        riskLevel: "high",
        visibleMiniSurfaceCount: countVisibleMiniSurfaces(settlePendingConversationEvents([])),
        channel: "web",
      });
      setLastPolicyDecision(decision);
      setTurns((items) => [
        ...settlePendingConversationEvents(items),
        { id: id("bot-ready"), type: "agent_message", content: copy.ready(riskSummary(nextArtifact)) },
        ...eventsForDecision(decision, "review", copy)
      ]);
      setComposer("");
    } finally {
      setBusy(false);
    }
  }

  async function handleFollowUp(content: string) {
    if (!workspace || !artifact || !content) return;
    const intent = await classifyFollowUp(content, locale, artifact);
    setLastIntent(intent);
    const event = await persistInteraction("channel.telegram_demo.text_followup", {
      content,
      intent: intent.intent,
      intent_mode: intent.mode,
      intent_confidence: intent.confidence
    });
    setInteractions((items) => [event, ...items]);
    const shouldProposeMemory = stage === "Revision Draft" && ["revise_tone", "remember_preference"].includes(intent.intent);
    const decision = interactionPolicyService.evaluate({
      event: "followup_received",
      artifact,
      followUpIntent: intent.intent,
      visibleMiniSurfaceCount: countVisibleMiniSurfaces(turns),
      channel: "web",
    });
    setLastPolicyDecision(decision);
    if (shouldProposeMemory) setMemoryLifecycle("candidate");
    setTurns((items) => [
      ...items,
      { id: id("user-followup"), type: "user_message", content },
      { id: id("observe-followup"), type: "observation", content: `${copy.followupObservation} (${copy.intentLabels[intent.intent]}, ${intent.mode})` },
      { id: id("bot-followup"), type: "agent_message", content: copy.followupReplies[intent.intent] },
      ...(shouldProposeMemory ? [
        { id: id("observe-memory-candidate"), type: "observation" as const, content: copy.memoryCandidateProposed },
        { id: id("bot-memory-prompt"), type: "agent_message" as const, content: copy.memoryPrompt },
        ...eventsForDecision(decision, "memory", copy)
      ] : [])
    ]);
    if (shouldProposeMemory) setStage("Memory");
    setComposer("");
  }

  async function requestEditDirection() {
    if (!artifact) return;
    const event = await persistInteraction("channel.telegram_demo.revision_direction_requested", {});
    setInteractions((items) => [event, ...items]);
    setTurns((items) => [
      ...items,
      { id: id("observe-edit"), type: "observation", content: copy.editObservation },
      { id: id("bot-edit"), type: "agent_message", content: copy.editReply }
    ]);
    setComposer(copy.followupSuggestion);
  }

  async function openFullReview() {
    if (!artifact) return;
    const event = await persistInteraction("channel.telegram_demo.open_full_review", {});
    setInteractions((items) => [event, ...items]);
    const decision = interactionPolicyService.evaluate({ event: "open_full_review", artifact, richSurfaceOpened: fullReviewOpen, channel: "web" });
    setLastPolicyDecision(decision);
    setFullReviewOpen(true);
    setTurns((items) => [
      ...items,
      { id: id("observe-full-review"), type: "observation", content: `${copy.fullReviewObservation} (${decision.reason})` },
      { id: id("rich-surface-link"), type: "rich_surface_link", content: copy.openArtifact, metadata: { artifact_id: artifact.id } }
    ]);
  }

  async function approveRevision() {
    if (!workspace || !artifact) return;
    const action = findApprovalAction(artifact);
    const block = findBlock(artifact, "summary");
    const primaryRisk = primaryRiskForArtifact(artifact);
    const event = await persistInteraction("channel.telegram_demo.approve_revision", {
      confirmation_id: action?.confirmation_id || null,
      block_id: block?.id || null,
      primary_risk_id: String(primaryRisk?.id || "risk_liability_indemnity_conflict"),
      clauses: String(primaryRisk?.clause || "8.1 / 8.2")
    });
    if (action?.confirmation_id) {
      const updated = await apiFetch<Confirmation>(`/api/confirmations/${action.confirmation_id}/approve`, {
        method: "POST",
        body: JSON.stringify({ decision: { source: "telegram_in_chat_demo" } })
      });
      setConfirmations((items) => items.map((item) => (item.id === updated.id ? updated : item)).filter((item) => item.status === "pending"));
    }
    setInteractions((items) => [event, ...items]);
    setStage("Revision Draft");
    const decision = interactionPolicyService.evaluate({
      event: "revision_approved",
      artifact,
      visibleMiniSurfaceCount: countVisibleMiniSurfaces(turns),
      channel: "web",
    });
    setLastPolicyDecision(decision);
    setLiveEvents((items) =>
      advanceLiveEvent(
        advanceLiveEvent(items, "artifact.action.clicked", copy.live.approvalClicked),
        "confirmation.approved",
        copy.live.confirmationApproved
      )
    );
    setTurns((items) => [
      ...items,
      { id: id("observe-approve"), type: "observation", content: copy.approvedObservation },
      { id: id("bot-approved"), type: "agent_message", content: copy.approvedReply },
      ...eventsForDecision(decision, "revision", copy)
    ]);
    setComposer(copy.followupSuggestion);
  }

  async function rememberPreference() {
    if (!workspace || !artifact) return;
    const block = findBlock(artifact, "memory_candidate");
    const event = await persistInteraction("channel.telegram_demo.remember_preference", { block_id: block?.id || null });
    setInteractions((items) => [event, ...items]);
    setMemoryLifecycle("confirmed");
    if (block) {
      const memory = await apiFetch<Memory>("/api/memories", {
        method: "POST",
        body: JSON.stringify({
          workspace_id: workspace.id,
          project_id: project?.id || null,
          source_run_id: artifact.run_id,
          source_type: "telegram_in_chat_demo",
          source_id: artifact.id,
          type: String(block.data.memory_type || "preference"),
          content: String(block.data.content || copy.rememberedReply),
          confidence: Number(block.data.confidence || 0.75),
          status: "confirmed",
          is_confirmed: true,
          structured_payload: { artifact_id: artifact.id, block_id: block.id, channel: "telegram-demo" }
        })
      });
      setMemories((items) => [memory, ...items]);
    }
    setMemoryLifecycle("saved");
    setStage("Memory");
    setLiveEvents((items) => advanceLiveEvent(items, "memory.candidate.created", copy.live.memoryPersisted));
    setTurns((items) => [
      ...items,
      { id: id("observe-memory"), type: "observation", content: copy.rememberedObservation },
      { id: id("observe-memory-confirmed"), type: "observation", content: copy.memoryConfirmed },
      { id: id("observe-memory-saved"), type: "observation", content: copy.memorySaved },
      { id: id("bot-memory"), type: "agent_message", content: copy.rememberedReply }
    ]);
  }

  async function skipMemory() {
    if (!artifact) return;
    const event = await persistInteraction("channel.telegram_demo.skip_memory", {});
    setInteractions((items) => [event, ...items]);
    setTurns((items) => [...items, { id: id("observe-skip-memory"), type: "observation", content: copy.notNowObservation }]);
  }

  async function persistInteraction(eventType: string, payload: Record<string, unknown>) {
    if (!workspace || !artifact) throw new Error("Missing artifact");
    return apiFetch<UIInteractionEvent>("/api/interactions", {
      method: "POST",
      body: JSON.stringify({
        workspace_id: workspace.id,
        project_id: project?.id || null,
        artifact_id: artifact.id,
        run_id: artifact.run_id,
        event_type: eventType,
        payload: { channel: "telegram-demo", ...payload }
      })
    });
  }

  const modeLabel = capabilities?.llm_enabled ? copy.runtimeLlm(capabilities.llm_provider, capabilities.default_model) : copy.runtimeDeterministic;
  const diagnostics = modelDiagnostics(capabilities, trace);

  return (
    <main className="telegram-chat-page">
      <section className="telegram-chat-shell">
        <header className="telegram-chat-topbar">
          <div className="telegram-avatar"><Bot size={18} /></div>
          <div>
            <span className="eyebrow">{copy.title}</span>
            <h1>{copy.botName}</h1>
            <p>{copy.subtitle}</p>
          </div>
          <div className="telegram-chat-actions">
            <span className="stage-badge">{copy.stagePrefix}: {stageLabel(stage, copy)}</span>
            <span className={capabilities?.llm_enabled ? "runtime-badge llm" : "runtime-badge"}>{modeLabel}</span>
            <button className="language-toggle" onClick={() => switchLocale(locale === "en" ? "zh" : "en")}><Languages size={14} /> {copy.otherLocaleLabel}</button>
            <button className="language-toggle" onClick={() => setInspectorOpen(true)}><Code2 size={14} /> {copy.inspector}</button>
          </div>
        </header>

        <div className="telegram-chat-thread">
          {turns.map((turn) => (
            <ChatTurnItem
              artifact={artifact}
              copy={copy}
              key={turn.id}
              onApprove={approveRevision}
              onEdit={requestEditDirection}
              onFullReview={openFullReview}
              onMemory={rememberPreference}
              onSkipMemory={skipMemory}
              turn={turn}
            />
          ))}
        </div>

        <footer className="telegram-chat-composer">
          {!artifact ? (
            <div className="contract-input-toggle">
              {(["sample", "paste"] as const).map((mode) => (
                <button className={inputMode === mode ? "active" : ""} key={mode} onClick={() => {
                  setInputMode(mode);
                  setComposer(mode === "sample" ? copy.demoGoal : "");
                }} type="button">
                  {mode === "sample" ? copy.sampleMode : copy.pasteMode}
                </button>
              ))}
            </div>
          ) : null}
          <button className="secondary-action" onClick={() => {
            if (!sampleContract) {
              setTurns((items) => [...items, { id: id("sample-loading"), type: "agent_message", content: copy.sampleUnavailable }]);
              return;
            }
            void runInitialReview(buildDemoMessage(copy, "sample", copy.demoGoal, sampleContract), copy.demoGoal, "sample");
          }} disabled={busy}>{copy.runSample}</button>
          <button className="secondary-action" onClick={resetDemo} disabled={busy}><RotateCcw size={14} /> {copy.reset}</button>
          {inputMode === "paste" && !artifact ? (
            <textarea placeholder={copy.pastePlaceholder} value={composer} onChange={(event) => setComposer(event.target.value)} />
          ) : (
            <input value={composer} onChange={(event) => setComposer(event.target.value)} onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submitMessage();
              }
            }} />
          )}
          <button className="primary-button" onClick={() => void submitMessage()} disabled={busy}><Send size={16} /></button>
        </footer>
      </section>

      {inspectorOpen ? (
        <DeveloperInspectorDrawer
          capabilities={capabilities}
          confirmations={confirmations}
          copy={copy}
          diagnostics={diagnostics}
          interactions={interactions}
          lastIntent={lastIntent}
          lastPolicyDecision={lastPolicyDecision}
          liveEvents={liveEvents}
          memoryLifecycle={memoryLifecycle}
          memories={memories}
          modeLabel={modeLabel}
          onClose={() => setInspectorOpen(false)}
          trace={trace}
        />
      ) : null}

      {fullReviewOpen && artifact ? (
        <FullReviewDrawer artifact={artifact} copy={copy} onClose={() => setFullReviewOpen(false)} />
      ) : null}
    </main>
  );
}

function ChatTurnItem({
  artifact,
  copy,
  onApprove,
  onEdit,
  onFullReview,
  onMemory,
  onSkipMemory,
  turn
}: {
  artifact: Artifact | null;
  copy: DemoCopy;
  onApprove: () => Promise<void>;
  onEdit: () => Promise<void>;
  onFullReview: () => Promise<void>;
  onMemory: () => Promise<void>;
  onSkipMemory: () => Promise<void>;
  turn: ChatTurn;
}) {
  if (turn.type === "mini_surface" || turn.type === "memory_candidate") {
    if (!artifact) return null;
    if (turn.surface === "MiniIssueCard") return <ContractReviewMiniSurface artifact={artifact} copy={copy} onApprove={onApprove} onEdit={onEdit} onFullReview={onFullReview} />;
    if (turn.surface === "MiniRevisionPreview") return <RevisionDraftMiniSurface artifact={artifact} copy={copy} onFullReview={onFullReview} />;
    if (turn.surface === "MiniChoiceCard") return <MiniChoiceCard artifact={artifact} copy={copy} onFullReview={onFullReview} />;
    if (turn.surface === "MiniToolPreview") return <MiniToolPreview copy={copy} />;
    return <MemoryCandidateMiniSurface artifact={artifact} copy={copy} onMemory={onMemory} onSkip={onSkipMemory} />;
  }
  if (turn.type === "attachment") {
    return (
      <div className="chat-turn attachment">
        <FileText size={18} />
        <div>
          <strong>{turn.fileName}</strong>
          <span>{turn.detail}</span>
        </div>
      </div>
    );
  }
  if (!("content" in turn)) return null;
  return (
    <div className={`chat-turn ${turn.type}`}>
      <span>{turn.content}</span>
      {turn.status ? <span className="typing-dots"><i /> <i /> <i /></span> : null}
    </div>
  );
}

function ContractReviewMiniSurface({
  artifact,
  copy,
  onApprove,
  onEdit,
  onFullReview
}: {
  artifact: Artifact;
  copy: DemoCopy;
  onApprove: () => Promise<void>;
  onEdit: () => Promise<void>;
  onFullReview: () => Promise<void>;
}) {
  const summary = findBlock(artifact, "risk_summary");
  const activeRisk = primaryRiskForArtifact(artifact);
  return (
    <article className="mini-surface-card contract-review-mini">
      <header>
        <span className="eyebrow">{copy.contractReview}</span>
        <h2>{artifact.title}</h2>
      </header>
      {summary ? (
        <div className="mini-risk-metrics">
          <div><strong>{String(summary.data.high_count || 0)}</strong><span>{copy.high}</span></div>
          <div><strong>{String(summary.data.medium_count || 0)}</strong><span>{copy.medium}</span></div>
          <div><strong>{String(summary.data.low_count || 0)}</strong><span>{copy.low}</span></div>
        </div>
      ) : null}
      {activeRisk ? (
        <section className="mini-active-risk">
          <strong>{copy.activeRisk}: {String(activeRisk.clause || "")}</strong>
          <p>{String(activeRisk.issue || "")}</p>
          <b>{copy.recommendedRevision}</b>
          <p>{String(activeRisk.suggested_revision || "")}</p>
          {activeRisk.evidence ? <small>{copy.evidence}: {String(activeRisk.evidence)}</small> : null}
        </section>
      ) : null}
      <div className="mini-surface-actions">
        <button className="primary-button" onClick={() => void onApprove()}><Check size={14} /> {copy.approveRevision}</button>
        <button className="secondary-action" onClick={() => void onEdit()}>{copy.editDirection}</button>
        <button className="secondary-action" onClick={() => void onFullReview()}><ArrowUpRight size={14} /> {copy.openFullReview}</button>
      </div>
    </article>
  );
}

function RevisionDraftMiniSurface({ artifact, copy, onFullReview }: { artifact: Artifact; copy: DemoCopy; onFullReview: () => Promise<void> }) {
  const block = findBlock(artifact, "editable_revision");
  const activeRisk = risksForArtifact(artifact).find((risk) => String(risk.risk_level) === "high");
  return (
    <article className="mini-surface-card revision-mini">
      <header>
        <span className="eyebrow">{copy.revisionDraft}</span>
        <h2>{String(block?.data.heading || copy.revisionPreview)}</h2>
      </header>
      <div className="mini-before-after">
        <div><span>{copy.before}</span><p>{String(activeRisk?.evidence || activeRisk?.issue || "")}</p></div>
        <div><span>{copy.after}</span><p>{String(block?.data.content || activeRisk?.suggested_revision || "")}</p></div>
      </div>
      <div className="mini-surface-actions">
        <button className="secondary-action">{copy.makeSofter}</button>
        <button className="secondary-action">{copy.makeStricter}</button>
        <button className="secondary-action">{copy.draftEmail}</button>
        <button className="secondary-action" onClick={() => void onFullReview()}><ArrowUpRight size={14} /> {copy.openArtifact}</button>
      </div>
    </article>
  );
}

function MemoryCandidateMiniSurface({ artifact, copy, onMemory, onSkip }: { artifact: Artifact; copy: DemoCopy; onMemory: () => Promise<void>; onSkip: () => Promise<void> }) {
  const block = findBlock(artifact, "memory_candidate");
  return (
    <article className="mini-surface-card memory-mini">
      <header>
        <span className="eyebrow">{copy.memoryCandidate}</span>
        <h2>{copy.memoryCandidate}</h2>
      </header>
      <p>{String(block?.data.content || copy.memoryPrompt)}</p>
      <small>{copy.memoryWhy}</small>
      <div className="mini-surface-actions">
        <button className="primary-button" onClick={() => void onMemory()}><Database size={14} /> {copy.remember}</button>
        <button className="secondary-action">{copy.editDirection}</button>
        <button className="secondary-action" onClick={() => void onSkip()}>{copy.notNow}</button>
      </div>
    </article>
  );
}

function MiniChoiceCard({ artifact, copy, onFullReview }: { artifact: Artifact; copy: DemoCopy; onFullReview: () => Promise<void> }) {
  return (
    <article className="mini-surface-card choice-mini">
      <header>
        <span className="eyebrow">MiniChoiceCard</span>
        <h2>{copy.draftEmail}</h2>
      </header>
      <p>{copy.followupReplies.draft_email}</p>
      <div className="mini-surface-actions">
        <button className="secondary-action">{copy.makeSofter}</button>
        <button className="secondary-action">{copy.makeStricter}</button>
        <button className="secondary-action" onClick={() => void onFullReview()}><ArrowUpRight size={14} /> {copy.openArtifact}</button>
      </div>
      <small>{artifact.title}</small>
    </article>
  );
}

function MiniToolPreview({ copy }: { copy: DemoCopy }) {
  return (
    <article className="mini-surface-card tool-mini">
      <header>
        <span className="eyebrow">MiniToolPreview</span>
        <h2>{copy.approveRevision}</h2>
      </header>
      <p>{copy.rendering}</p>
    </article>
  );
}

function FullReviewDrawer({ artifact, copy, onClose }: { artifact: Artifact; copy: DemoCopy; onClose: () => void }) {
  const risks = risksForArtifact(artifact);
  return (
    <div className="inspector-overlay">
      <aside className="inspector-drawer full-review-drawer">
        <header>
          <div><span className="eyebrow">{copy.openFullReview}</span><h2>{artifact.title}</h2></div>
          <button onClick={onClose}><X size={16} /></button>
        </header>
        <section className="inspector-card">
          <header><FileText size={16} /><strong>{copy.riskSummary}</strong></header>
          <div>
            <span>{copy.activeRisk}: 8.1 / 8.2</span>
            <a className="secondary-action" href={`/artifacts/${artifact.id}?channel=telegram-demo`}><ArrowUpRight size={14} /> {copy.openArtifact}</a>
          </div>
        </section>
        <section className="full-review-list">
          {risks.map((risk) => (
            <article className="risk-block" key={String(risk.id || risk.clause)}>
              <div>
                <strong>{String(risk.clause || "Risk")}</strong>
                <span className={`risk-level ${String(risk.risk_level || "medium")}`}>{String(risk.risk_level || "medium")}</span>
              </div>
              <p>{String(risk.issue || "")}</p>
              <small>{String(risk.evidence || risk.suggested_revision || "")}</small>
            </article>
          ))}
        </section>
      </aside>
    </div>
  );
}

function DeveloperInspectorDrawer({
  capabilities,
  confirmations,
  copy,
  diagnostics,
  interactions,
  lastIntent,
  lastPolicyDecision,
  liveEvents,
  memoryLifecycle,
  memories,
  modeLabel,
  onClose,
  trace
}: {
  capabilities: RuntimeCapabilities | null;
  confirmations: Confirmation[];
  copy: DemoCopy;
  diagnostics: ReturnType<typeof modelDiagnostics>;
  interactions: UIInteractionEvent[];
  lastIntent: FollowUpIntentResult | null;
  lastPolicyDecision: InteractionDecision | null;
  liveEvents: LiveEvent[];
  memoryLifecycle: MemoryLifecycle;
  memories: Memory[];
  modeLabel: string;
  onClose: () => void;
  trace: TraceStep[];
}) {
  return (
    <div className="inspector-overlay">
      <aside className="inspector-drawer">
        <header>
          <div><span className="eyebrow">Developer</span><h2>{copy.inspector}</h2></div>
          <button onClick={onClose}><X size={16} /></button>
        </header>
        <InspectorCard icon={<MessageCircle size={16} />} title={copy.liveEvents}>
          {liveEvents.map((event) => <span className={`live-event ${event.status || "pending"}`} key={event.id}>{event.label}: {event.detail}</span>)}
        </InspectorCard>
        <InspectorCard icon={<ShieldCheck size={16} />} title={copy.runtimeMode}>
          <strong>{modeLabel}</strong>
          <span>{copy.provider}: {diagnostics.provider}</span>
          <span>{copy.model}: {diagnostics.model}</span>
          <span>{copy.mode}: {diagnostics.mode}</span>
          <span>{copy.fallback}: {diagnostics.fallback ? copy.yes : copy.no}</span>
          <span>{copy.noSecrets}</span>
        </InspectorCard>
        <InspectorCard icon={<FileText size={16} />} title={copy.rendererDecision}>
          {lastPolicyDecision ? (
            <span>{lastPolicyDecision.decision}: {lastPolicyDecision.surfaceType || "none"} · {lastPolicyDecision.reason}</span>
          ) : null}
          {Object.values(["MiniIssueCard", "MiniApprovalCard", "MiniRevisionPreview", "MiniMemoryCard", "MiniToolPreview", "MiniChoiceCard"] as MiniSurfaceType[]).map((type) => {
            const registration = getMiniSurfaceRegistration(type);
            return <span key={type}>{`${registration.type} -> ${registration.supportedChannels.join(", ")} · fallback ${registration.fallback}`}</span>;
          })}
        </InspectorCard>
        <details className="inspector-card inspector-collapsible">
          <summary data-show-label="show" data-hide-label="hide"><Code2 size={16} /><strong>{copy.interactionContract}</strong></summary>
          <div>
            <code>when: risk.detected</code>
            <code>render: ContractReviewMiniSurface</code>
            <code>observe: approve_revision</code>
            <code>act: generate_revised_clause</code>
            <code>memorize: user_preference</code>
          </div>
        </details>
        <InspectorCard icon={<Database size={16} />} title={copy.durableObservations}>
          {interactions.slice(0, 5).map((event) => <span key={event.id}>{event.event_type}</span>)}
          {!interactions.length ? <span>channel.message.received</span> : null}
          {lastIntent ? <span>followup intent: {copy.intentLabels[lastIntent.intent]} ({lastIntent.mode})</span> : null}
          <span>{copy.memoryLifecycle}: {copy.memoryLifecycleLabels[memoryLifecycle]}</span>
          <span>{copy.confirmations}: {confirmations.length}</span>
          <span>{copy.memories}: {memories.length}</span>
          <span>{copy.traceSteps}: {trace.length}</span>
          <span>Telegram live bot: {capabilities?.telegram_enabled ? "configured" : "not configured"}</span>
        </InspectorCard>
      </aside>
    </div>
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

function findBlock(artifact: Artifact, idOrType: string) {
  return artifact.schema_json.blocks.find((block) => block.id === idOrType || block.type === idOrType);
}

function findApprovalAction(artifact: Artifact): ArtifactAction | undefined {
  return artifact.schema_json.actions.find((action) => action.confirmation_id) || findBlock(artifact, "summary")?.actions?.find((action) => action.confirmation_id);
}

function risksForArtifact(artifact: Artifact) {
  return ((findBlock(artifact, "risk_review")?.data.risks as Array<Record<string, unknown>>) || []);
}

function primaryRiskForArtifact(artifact: Artifact) {
  const risks = risksForArtifact(artifact);
  return (
    risks.find((risk) => {
      const text = `${String(risk.id || "")} ${String(risk.clause || "")} ${String(risk.issue || "")}`.toLowerCase();
      return (text.includes("8.1") && text.includes("8.2")) || (text.includes("liability") && text.includes("indemn")) || (text.includes("责任") && text.includes("赔偿"));
    }) || risks.find((risk) => String(risk.risk_level) === "high") || risks[0]
  );
}

function riskSummary(artifact: Artifact | null) {
  const block = artifact?.schema_json.blocks.find((item) => item.id === "risk_summary");
  return Number(block?.data.high_count || 3);
}

function countVisibleMiniSurfaces(turns: ChatTurn[]) {
  return turns.filter((turn) => turn.type === "mini_surface" || turn.type === "memory_candidate").length;
}

function eventsForDecision(decision: InteractionDecision, context: "review" | "revision" | "memory", copy: DemoCopy): ChatTurn[] {
  if (decision.decision !== "mini_surface" || !decision.surfaceType) {
    if (decision.decision === "rich_surface_link") {
      return [{ id: id(`rich-${context}`), type: "rich_surface_link", content: copy.openFullReview, metadata: { reason: decision.reason } }];
    }
    return [];
  }
  return [
    {
      id: id(`surface-${context}`),
      type: decision.surfaceType === "MiniMemoryCard" ? "memory_candidate" : "mini_surface",
      surface: decision.surfaceType,
      metadata: { reason: decision.reason, priority: decision.priority },
    },
  ];
}

function stageLabel(stage: DemoStage, copy: DemoCopy) {
  if (stage === "Risk Review") return copy.stageRiskReview;
  if (stage === "Revision Draft") return copy.stageRevisionDraft;
  if (stage === "Memory") return copy.stageMemory;
  return copy.stageIntent;
}

function buildDemoMessage(copy: DemoCopy, inputMode: InputMode, composer: string, sampleContract: DemoContractFixture | null) {
  if (inputMode === "sample") {
    return `${copy.demoGoal}\n\nAttached contract file: ${sampleContract?.file_name || SAMPLE_CONTRACT_FALLBACK_FILE_NAME}\n\nContract text:\n${sampleContract?.content || ""}`;
  }
  const pasted = composer.trim();
  return pasted ? `${copy.demoGoal}\n\nContract text:\n${pasted}` : copy.demoGoal;
}

function userMessagePreview(copy: DemoCopy, inputMode: InputMode, composer: string) {
  if (inputMode === "sample") return copy.demoGoal;
  const pasted = composer.trim();
  if (!pasted) return copy.demoGoal;
  return copy.demoGoal;
}

function contractAttachmentTurn(copy: DemoCopy, inputMode: InputMode, content: string, sampleContract: DemoContractFixture | null): ChatTurn {
  if (inputMode === "sample") {
    return {
      id: id("attachment"),
      type: "attachment",
      fileName: sampleContract?.file_name || SAMPLE_CONTRACT_FALLBACK_FILE_NAME,
      detail: copy.sampleAttachmentDetail,
    };
  }
  const contractLength = Math.max(0, content.length - copy.demoGoal.length);
  return {
    id: id("attachment"),
    type: "attachment",
    fileName: copy.pastedAttachmentName,
    detail: copy.pastedAttachmentDetail(contractLength),
  };
}

async function classifyFollowUp(text: string, locale: Locale, artifact: Artifact): Promise<FollowUpIntentResult> {
  try {
    return await apiFetch<FollowUpIntentResult>("/api/demo/followup-intent", {
      method: "POST",
      body: JSON.stringify({
        text,
        locale,
        artifact_id: artifact.id,
        run_id: artifact.run_id,
      }),
    });
  } catch {
    return deterministicFollowUpIntent(text);
  }
}

function deterministicFollowUpIntent(text: string): FollowUpIntentResult {
  const normalized = text.toLowerCase();
  let intent: FollowUpIntent = "general_followup";
  let reason = "fallback";
  if (/记住|记忆|以后|remember|save this|preference/i.test(normalized)) {
    intent = "remember_preference";
    reason = "memory keyword";
  } else if (/语气|强硬|柔和|客户|谈判|tone|softer|friendlier|friendly|negotiat/i.test(normalized)) {
    intent = "revise_tone";
    reason = "tone keyword";
  } else if (/邮件|email|mail|发给|回复客户/i.test(normalized)) {
    intent = "draft_email";
    reason = "email keyword";
  } else if (/8\.1|8\.2|条款|clause|section/i.test(normalized)) {
    intent = "focus_clause";
    reason = "clause keyword";
  } else if (/为什么|解释|原因|why|explain|meaning|risk/i.test(normalized)) {
    intent = "explain_risk";
    reason = "explanation keyword";
  }
  return { intent, confidence: 0.62, mode: "deterministic", reason };
}

function withLanguageInstruction(content: string, copy: DemoCopy) {
  return `${content.trim()}\n\n${copy.languageInstruction}`;
}

function modelDiagnostics(capabilities: RuntimeCapabilities | null, trace: TraceStep[]) {
  const llmStep = trace.find((step) => step.step_type === "llm_generation");
  const output = llmStep?.output_json || {};
  const status = String(output.status || "");
  return {
    provider: capabilities?.llm_provider || "openai",
    model: String(output.model || capabilities?.default_model || "n/a"),
    mode: capabilities?.llm_runtime_mode || "deterministic",
    fallback: status === "fallback" || Boolean(output.fallback_reason)
  };
}

function advanceLiveEvent(items: LiveEvent[], eventId: string, detail: string): LiveEvent[] {
  return items.map((event) => event.id === eventId ? { ...event, detail, status: "done" as const } : event);
}

function id(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
