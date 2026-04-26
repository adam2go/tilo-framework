# AI-native Interaction Components

This document defines Tilo's AI-native interaction component system.

Tilo is not only an agent runtime. Tilo should also explore a new interaction layer for AI-native SaaS: instead of forcing users to operate traditional SaaS screens, agents should generate, update, and control interactive result pages composed from reusable components.

---

## 1. Core Thesis

Traditional SaaS UI is built around fixed features:

```text
Navigation -> Page -> Form -> Table -> Button -> Result
```

AI-native SaaS UI should be built around user intent and agent-generated results:

```text
User goal -> Agent run -> Interactive artifact -> Human decision -> Memory update -> Next action
```

The conversation page is not a side feature. It is the main operating surface.

Tilo's UI should become:

```text
Conversation-driven command center + agent-generated SaaS component surface
```

---

## 2. Why This Matters

If Tilo wants to replace parts of traditional SaaS, it cannot only render Markdown or static cards.

It needs a component system that can express common SaaS interactions in AI-native form:

- review
- approve
- edit
- compare
- prioritize
- assign
- schedule
- track
- inspect
- simulate
- decide
- continue

These interactions should be generated from agent output and connected to durable backend objects such as Artifact, Confirmation, Memory, Task, Run, ToolInvocation, and SkillCandidate.

---

## 3. Design Principle

Tilo components should be:

1. **Agent-addressable**  
   The agent can request or generate the component through artifact schema.

2. **Human-actionable**  
   The user can approve, reject, edit, select, filter, compare, continue, or export.

3. **Stateful**  
   Important user actions are persisted as Confirmation, Feedback, Memory, or Artifact updates.

4. **Traceable**  
   Components should be linked back to Task, Run, TraceStep, ToolInvocation, and Memory where relevant.

5. **Composable**  
   Components should be reusable across legal, sales, HR, finance, product, and research workflows.

6. **Safe by default**  
   Risky actions must require Confirmation.

---

## 4. Component Layer Model

Tilo should organize AI-native UI into four layers:

```text
Conversation Layer
  -> Interaction Components
  -> Artifact Page
  -> Decision / Memory / Tool State
```

### 4.1 Conversation Layer

The user gives goals, clarifies requirements, and steers the agent.

It should include:

- goal input
- prompt suggestions
- inline clarification questions
- run progress
- quick actions
- conversation history when needed

### 4.2 Interaction Components

Reusable interactive components generated or selected by the agent.

Examples:

- ApprovalCard
- RiskReviewPanel
- ComparisonMatrix
- EditableDraft
- DecisionTable
- PrioritizationBoard
- TimelinePlanner
- ChecklistRunner
- FormReview
- MetricDashboard
- ActionQueue
- MemoryReviewCard
- SkillReviewCard

### 4.3 Artifact Page

The durable result page assembled from interaction components.

It should be shareable and revisitable in future versions.

### 4.4 State Layer

Component interactions must write to durable state:

- Confirmation
- Memory
- Feedback
- ArtifactVersion
- ToolInvocation
- SkillCandidate
- Task/Run

---

## 5. Component Taxonomy

### 5.1 Decision Components

Used when humans need to make a choice.

Required components:

```text
ApprovalCard
RejectReasonDialog
EditBeforeApprove
DecisionTable
ChoiceGroup
RiskDecisionPanel
```

Use cases:

- approve contract revision
- approve sales follow-up
- approve memory write
- approve tool action
- approve skill promotion

Backend mapping:

```text
Confirmation
Feedback
ToolInvocation
SkillCandidate
```

---

### 5.2 Review Components

Used when agents produce analysis that humans need to inspect.

Required components:

```text
RiskReviewPanel
ClauseReviewItem
DiffReview
EvidenceCard
CitationList
QualityChecklist
```

Use cases:

- contract review
- compliance review
- PRD review
- financial anomaly review
- HR policy review

Backend mapping:

```text
Artifact
TraceStep
Memory
```

---

### 5.3 Editing Components

Used when the agent drafts something and the user needs to edit or refine it.

Required components:

```text
EditableDocument
InlineSuggestion
RevisionBlock
CommentThread
VersionSwitcher
```

Use cases:

- contract clause rewrite
- email drafting
- sales message rewrite
- report editing
- PRD editing

Backend mapping:

```text
Artifact
ArtifactVersion
Feedback
MemoryCandidate
```

---

### 5.4 Comparison Components

Used when the agent compares options.

Required components:

```text
ComparisonMatrix
ScorecardTable
TradeoffCard
OptionPicker
RankingList
```

Use cases:

- competitor analysis
- vendor selection
- candidate screening
- product prioritization
- model/provider comparison

Backend mapping:

```text
Artifact
Feedback
Confirmation
```

---

### 5.5 Planning Components

Used when the agent creates a plan or schedule.

Required components:

```text
TimelinePlanner
MilestoneMap
TaskBoard
ChecklistRunner
DependencyGraph
```

Use cases:

- project planning
- travel planning
- implementation roadmap
- sales campaign
- content calendar

Backend mapping:

```text
Task
Run
Artifact
Confirmation
```

---

### 5.6 Dashboard Components

Used when the agent summarizes status or metrics.

Required components:

```text
MetricCard
InsightCard
StatusGrid
TrendPanel
AlertList
```

Use cases:

- sales follow-up dashboard
- project health
- evaluation report
- memory quality dashboard
- runtime observability

Backend mapping:

```text
RunMetric
Artifact
ToolInvocation
Feedback
```

---

### 5.7 Memory Components

Used when users inspect and control memory.

Required components:

```text
MemoryCandidateCard
MemoryTimeline
MemoryConflictResolver
MemoryScopeBadge
MemoryProvenanceCard
```

Use cases:

- confirm memory candidate
- reject incorrect memory
- resolve conflicting memory
- inspect why memory was recalled
- edit memory scope

Backend mapping:

```text
Memory
MemoryWriteEvent
MemoryRecallEvent
MemoryConflict
```

---

### 5.8 Agent Action Components

Used when the agent wants to continue work or invoke tools.

Required components:

```text
ActionQueue
ToolCallPreview
PermissionGate
NextStepCard
RunAgainButton
ContinueTaskInput
```

Use cases:

- send email
- run browser search
- generate revised artifact
- call MCP tool
- update external SaaS

Backend mapping:

```text
ToolInvocation
Confirmation
Run
TraceStep
```

---

## 6. Artifact Schema Extension

Tilo's artifact schema should support interaction components.

Recommended block shape:

```ts
export type ArtifactBlock = {
  id: string;
  type: string;
  title?: string;
  data: Record<string, unknown>;
  actions?: ArtifactAction[];
  state_binding?: StateBinding;
};
```

Recommended action shape:

```ts
export type ArtifactAction = {
  id: string;
  label: string;
  action_type:
    | "approve"
    | "reject"
    | "edit"
    | "select"
    | "continue_task"
    | "regenerate"
    | "invoke_tool"
    | "create_memory"
    | "promote_skill"
    | "export";
  confirmation_required: boolean;
  payload?: Record<string, unknown>;
};
```

Recommended state binding:

```ts
export type StateBinding = {
  entity_type:
    | "artifact"
    | "confirmation"
    | "memory"
    | "skill_candidate"
    | "tool_invocation"
    | "task"
    | "run";
  entity_id: string;
  field?: string;
};
```

---

## 7. Component Registry

Frontend should maintain a registry:

```ts
const interactionComponentRegistry = {
  approval_card: ApprovalCard,
  risk_review_panel: RiskReviewPanel,
  comparison_matrix: ComparisonMatrix,
  editable_document: EditableDocument,
  timeline_planner: TimelinePlanner,
  metric_dashboard: MetricDashboard,
  memory_candidate_card: MemoryCandidateCard,
  tool_call_preview: ToolCallPreview,
};
```

Do not hardcode all UI behavior inside one ArtifactRenderer.

---

## 8. Conversation-first UX

The conversation page should be the command center.

It should not be a small sidebar afterthought.

Required capabilities:

1. The user can state a goal naturally.
2. The agent can ask clarification questions inline.
3. The agent can generate interactive components as part of the result.
4. The user can act on components without leaving the flow.
5. Actions update durable backend state.
6. The artifact page remains the final durable result.

Suggested layout direction:

```text
Left/Top: Conversation and goal steering
Center: Generated AI-native SaaS surface
Right: Context, memory, trace, decisions
```

The conversation area should include:

- command composer
- task summary
- run progress
- clarification messages
- next-step suggestions
- recent decisions

---

## 9. Replacement Mapping from Traditional SaaS

Tilo should define AI-native replacements for common SaaS components.

| Traditional SaaS | AI-native Tilo Replacement |
|---|---|
| Form | Conversational goal + generated clarification component |
| Table | DecisionTable / ComparisonMatrix with agent-generated insights |
| Dashboard | MetricDashboard with natural language summary and next actions |
| Modal confirm | Durable Confirmation / ApprovalCard |
| Workflow stepper | Agent Run Progress + ActionQueue |
| Settings page | Memory / Tool / Skill review components |
| Report page | Artifact page with interactive blocks |
| Notification center | Inbox with pending decisions |
| Search/filter | Agent-assisted query + scoped result components |
| CRUD editor | EditableArtifact with version history |

---

## 10. v0.3 Implementation Plan

### Phase 1: Define component protocol

- Extend artifact block schema with `actions` and `state_binding`.
- Add shared TypeScript types.
- Add backend Pydantic schemas.
- Add validation.

### Phase 2: Build component registry

Implement first components:

```text
ApprovalCard
RiskReviewPanel
ComparisonMatrix
MetricDashboard
MemoryCandidateCard
ToolCallPreview
EditableDocument placeholder
ActionQueue
```

### Phase 3: Connect actions to backend

- approval -> Confirmation API
- memory confirmation -> Memory API
- skill promotion -> Skill Candidate API
- tool invocation -> Tool API with permission gate
- continue task -> Message API

### Phase 4: Redesign Console around conversation + components

- Make conversation/task area more prominent.
- Use generated interaction components in Artifact panel.
- Move Inbox into both right panel and inline artifact actions.

### Phase 5: Add demo flows

Demo flows must prove AI-native SaaS interactions:

1. Contract review: RiskReviewPanel + ApprovalCard + EditableDocument
2. Sales follow-up: MetricDashboard + DecisionTable + ApprovalCard
3. Competitive analysis: ComparisonMatrix + OptionPicker + ContinueTaskInput

---

## 11. Acceptance Criteria

The AI-native interaction component module is successful when:

1. Artifacts can render at least 6 reusable interaction components.
2. Components are selected by schema, not hardcoded per demo.
3. User actions write to durable backend state.
4. Confirmations are visible both in artifacts and Inbox.
5. Memory candidates can be confirmed from component UI.
6. The conversation page feels like the primary operating surface.
7. A first-time user understands that Tilo replaces SaaS interactions with agent-generated components.
8. Demo flows look attractive enough for a public open-source README screenshot.

---

## 12. Codex Prompt

Use this prompt when implementing this module:

```text
Read docs/AI_NATIVE_INTERACTION_COMPONENTS.md first.

Implement Tilo's AI-native interaction component system.

Do not simply beautify the current UI.

Focus on defining reusable agent-generated interaction components that replace traditional SaaS components.

Start with:
1. artifact block action/state_binding schema
2. frontend interaction component registry
3. ApprovalCard
4. RiskReviewPanel
5. ComparisonMatrix
6. MetricDashboard
7. MemoryCandidateCard
8. ToolCallPreview
9. ActionQueue
10. Console layout update so conversation remains the primary operating surface

Preserve all existing backend APIs unless changes are necessary.

All component actions that change durable state must call backend APIs.
```
