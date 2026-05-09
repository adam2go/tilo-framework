# The ROAM Loop

ROAM stands for:

```text
Render -> Observe -> Act -> Memorize
```

The ROAM Loop is Tilo's proposed interaction framework for AI-native SaaS agents.

Traditional agent loops such as ReAct usually treat observation as external tool output. Tilo extends this idea: **human interaction with generated UI components is also observation**.

In AI-native SaaS, the interface is not only where results are displayed. The interface becomes part of the agent loop.

---

## 1. Why ROAM?

Most agent frameworks focus on this loop:

```text
Observe -> Reason -> Act
```

or:

```text
Thought -> Action -> Observation
```

This works well for tool-using agents, but it is not enough for AI-native SaaS.

SaaS products are not only about backend actions. They are also about:

- presenting information
- collecting user decisions
- letting users edit and approve results
- showing state and progress
- turning work into durable interfaces
- learning from user interactions

Therefore, Tilo needs a loop that treats UI as a first-class runtime surface.

---

## 2. The ROAM Loop

```text
Render -> Observe -> Act -> Memorize
```

### 2.1 Render

The agent renders an interactive artifact or component surface.

This may include:

- contract review panels
- decision cards
- comparison matrices
- dashboards
- editable documents
- task boards
- timelines
- approval queues
- memory review cards

Render is not just final output. Render is an agent action.

The agent can create, update, patch, or replace UI components based on the current task state.

### 2.2 Observe

The system observes user interactions and external state changes.

Observations include:

- user clicks approve/reject
- user edits a document
- user selects an option
- user confirms a memory
- user rejects a recommendation
- user changes a priority
- a tool call succeeds or fails
- a generated artifact is revised

In Tilo, UI events are structured observations.

They should be captured as durable state, not treated as temporary frontend events.

### 2.3 Act

The agent acts based on observations.

Actions may include:

- invoke a tool
- update an artifact
- create a confirmation
- generate a revised draft
- call an external API
- create a memory candidate
- generate a skill candidate
- continue a task
- ask a clarification question

Actions should be permission-aware and traceable.

High-risk actions must require durable confirmation.

### 2.4 Memorize

The system extracts durable learning from the run.

Memorize may include:

- confirmed user preferences
- project facts
- decisions
- reusable task patterns
- feedback on artifact quality
- skill candidates
- memory recall/write events

Memorize must be safe and inspectable.

Tilo should not silently store every interaction as trusted memory.

---

## 3. ROAM vs ReAct

| ReAct-style Agent Loop | Tilo ROAM Loop |
|---|---|
| Observation usually comes from tools or environment | Observation also comes from human UI interactions |
| Action is usually tool invocation | Action includes tool invocation, artifact update, confirmation creation, UI patching |
| UI is often outside the loop | UI is part of the loop |
| Output is often text or tool result | Output is an interactive artifact page |
| Memory is optional or external | Memory is part of the loop |
| Human-in-the-loop is often approval only | Human interaction becomes structured agent observation |

---

## 4. ROAM and Tilo Domain Objects

ROAM maps directly to Tilo's core objects.

| ROAM Stage | Tilo Objects |
|---|---|
| Render | Artifact, ArtifactBlock, ArtifactAction, InteractionComponent |
| Observe | Confirmation, Feedback, MemoryCandidate, ToolInvocation, UIEvent |
| Act | Run, TraceStep, ToolInvocation, ArtifactVersion, Task |
| Memorize | Memory, MemoryWriteEvent, MemoryRecallEvent, SkillCandidate |

---

## 5. ROAM and AI-native Interaction Components

ROAM depends on reusable AI-native interaction components.

Examples:

### ApprovalCard

```text
Render: show approval card
Observe: user approves/rejects
Act: execute or cancel linked action
Memorize: store decision preference if confirmed
```

### RiskReviewPanel

```text
Render: show risks and suggested revisions
Observe: user accepts/edits/rejects risk item
Act: generate revised artifact
Memorize: learn user's risk tolerance
```

### ComparisonMatrix

```text
Render: show options and scores
Observe: user selects or reprioritizes options
Act: refine recommendation
Memorize: learn decision criteria
```

### MemoryCandidateCard

```text
Render: show memory candidate
Observe: user confirms/edits/rejects
Act: update memory store
Memorize: confirmed long-term memory
```

---

## 6. ROAM Runtime Contract

A ROAM-compatible artifact block should support:

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

Actions should be durable:

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

State bindings connect UI components to backend entities:

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

## 7. ROAM Event Model

Tilo should eventually capture interaction events as structured observations.

Recommended model:

```text
UIInteractionEvent
```

Fields:

```text
id
workspace_id
project_id nullable
user_id nullable
artifact_id nullable
block_id nullable
action_id nullable
run_id nullable
event_type
payload_json
created_at
```

Examples:

```text
artifact.action.approved
artifact.action.rejected
artifact.block.edited
artifact.option.selected
memory.candidate.confirmed
memory.candidate.rejected
skill.candidate.promoted
tool.invocation.approved
```

These events become observations for the next agent step.

---

## 8. ROAM Design Rules

1. Rendering is an agent action.
2. UI interaction is observation.
3. Observation should be structured and durable.
4. Important actions should be confirmation-gated.
5. Memory updates should be reviewable.
6. Artifact pages should be revisitable and stateful.
7. The conversation page should be the command center.
8. Components should be generated from schema, not hardcoded per demo.
9. Components should write to backend state, not only local frontend state.
10. Every loop should improve future runs when safely confirmed.

---

## 9. Why This Can Be a New Framework Concept

ROAM gives Tilo a unique point of view:

> Agents should not only reason and act. They should render interactive surfaces, observe human interaction, act on those observations, and memorize durable learning.

This makes Tilo different from ordinary agent frameworks.

Tilo is not just about tool calling.

Tilo is about AI-native SaaS delivery.

---

## 10. Suggested README Positioning

Use this message when explaining Tilo publicly:

```text
Tilo introduces the ROAM Loop: Render, Observe, Act, Memorize.

Unlike traditional agent frameworks that treat observation mainly as tool output, Tilo treats human interaction with generated UI as structured observation.

This enables agents to deliver interactive SaaS-like artifacts, capture decisions, and improve through confirmed memory.
```

---

## 11. Implementation Plan

### Phase 1: Document and expose the concept

- Add ROAM Loop to README.
- Link ROAM to AI-native interaction components.
- Explain how ROAM extends ReAct.

### Phase 2: Add interaction event model

- Add `UIInteractionEvent` model.
- Log artifact action clicks.
- Log memory candidate decisions.
- Log confirmation decisions.

### Phase 3: Make artifact actions ROAM-compatible

- Add action metadata.
- Add state bindings.
- Route actions through backend APIs.

### Phase 4: Feed observations back into runtime

- Let new runs retrieve relevant interaction events.
- Let memory extractor use interaction events.
- Let skill candidate generator use repeated interaction patterns.

### Phase 5: Build showcase demos

- Contract review: RiskReviewPanel -> ApprovalCard -> EditableDocument -> MemoryCandidate
- Sales follow-up: Dashboard -> DecisionTable -> ApprovalCard -> ActionQueue
- Competitive analysis: ComparisonMatrix -> OptionPicker -> ContinueTaskInput -> Memory update

---

## 12. Codex Prompt

```text
Read docs/ROAM_LOOP.md and docs/AI_NATIVE_FRAMEWORK_PRINCIPLES.md.

Implement the ROAM Loop foundation.

Start with:
1. Add ROAM explanation to README and README.zh-CN.md.
2. Add UIInteractionEvent model if backend structure allows.
3. Extend artifact actions with action_type, confirmation_required, payload, and state_binding.
4. Ensure user interactions in Artifact components call backend APIs and create durable observations.
5. Refactor interaction components so Render -> Observe -> Act -> Memorize is visible in code.
6. Do not turn this into local-only frontend state.

The goal is to make UI interaction a first-class part of the agent loop.
```
