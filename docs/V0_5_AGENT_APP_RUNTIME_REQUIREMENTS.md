# Tilo v0.5 Agent App Runtime Requirements

This document defines the next major implementation milestone for Tilo.

The goal is to move Tilo from a strong demo into a reusable open-source framework for building AI-native agent apps.

Tilo's core product thesis remains:

```text
Agent by default. UI when necessary.
```

The framework should help developers build agents that work autonomously most of the time, render lightweight UI only at meaningful decision points, observe user interactions, continue acting, and persist confirmed learning as memory.

---

## 1. Why v0.5 Matters

The current project has proven the interaction concept through the contract review demo.

However, much of the logic is still demo-specific.

v0.5 should make the pattern reusable:

```text
Agent App Manifest
  + Interaction Policy Runtime
  + Conversation Runtime
  + Mini Surface Registry
  + Rich Surface Escalation
  + Example Apps
```

A developer should be able to clone the repo, inspect `examples/apps/`, and understand how to build their own Tilo agent app.

---

## 2. Non-goals

Do not turn Tilo into a heavy dashboard platform.

Do not build a complex workflow engine in this milestone.

Do not make UI appear for every agent step.

Do not create a large standard/protocol claim yet.

Do not overfit only to contract review.

Do not break the existing deterministic demo mode.

---

## 3. Version Split

Implement v0.5 in two rounds.

### Round 1: App Definition and Interaction Runtime Foundation

Goal:

```text
Make Tilo apps declarative and reusable.
```

Scope:

1. Agent App Manifest
2. Interaction Policy Runtime
3. Mini Surface Registry
4. Contract Review App example migrated to manifest/policy
5. Documentation for developers

### Round 2: Backend Conversation Runtime and Multi-app Capability

Goal:

```text
Make Tilo runtime persistent, channel-friendly, and app-extensible.
```

Scope:

1. Backend ConversationSession and ConversationTurn
2. Conversation APIs
3. Rich Surface Escalation standardization
4. Sales Follow-up App example
5. Telegram callback integration with conversation runtime
6. Stronger tests and README updates

---

# Round 1 Requirements

## 4. Agent App Manifest

Add a formal manifest format for Tilo agent apps.

Recommended file name:

```text
app.yaml
```

Recommended location:

```text
examples/apps/contract-review-agent/app.yaml
```

### 4.1 Manifest goals

The manifest should describe:

- app id
- name
- description
- entry mode
- runtime model config
- memory behavior
- interaction policy file
- mini surfaces
- rich surfaces
- tools
- channels
- sample inputs

### 4.2 Manifest example

```yaml
id: contract-review-agent
version: 0.1
name: Contract Review Agent
description: Reviews contracts and asks for human input only at key legal/business decision points.

entry:
  type: conversation
  default_prompt: 请审查这份合同，重点关注付款、验收、数据合规、知识产权、责任限制和终止条款。

runtime:
  model: default
  deterministic_fallback: true
  memory: enabled
  interaction_policy: interaction.policy.yaml

surfaces:
  mini:
    - MiniIssueCard
    - MiniApprovalCard
    - MiniRevisionPreview
    - MiniMemoryCard
  rich:
    - ContractReviewArtifact

sample_inputs:
  - type: contract_fixture
    name: problematic-ai-service-agreement
    path: ../../contracts/problematic-ai-service-agreement.md

tools:
  - name: contract_parser
    required: false
  - name: document_exporter
    required: false

channels:
  - web
  - telegram
```

### 4.3 Backend schema

Add Pydantic models, for example:

```text
backend/app/services/apps/schemas.py
```

Suggested models:

- `AgentAppManifest`
- `AgentAppEntry`
- `AgentAppRuntime`
- `AgentAppSurfaceConfig`
- `AgentAppSampleInput`
- `AgentAppToolConfig`

### 4.4 Manifest loader

Add loader service:

```text
backend/app/services/apps/loader.py
```

Responsibilities:

1. Load app manifest from `examples/apps/{app_id}/app.yaml`.
2. Validate manifest with Pydantic.
3. Resolve relative paths safely.
4. Provide an in-memory registry of available example apps.

### 4.5 Minimal APIs

Add:

```text
GET /api/apps
GET /api/apps/{app_id}
```

Response should not expose secrets.

---

## 5. Interaction Policy Runtime

Add a lightweight policy runtime.

This is one of the most important parts of v0.5.

Tilo must not render UI everywhere. It should decide:

```text
no_ui | mini_surface | rich_surface | ask_text
```

### 5.1 Policy file

Recommended file:

```text
examples/apps/contract-review-agent/interaction.policy.yaml
```

### 5.2 Policy example

```yaml
id: contract-review-policy
version: 0.1

budget:
  max_mini_surfaces_per_run: 3
  max_confirmations_per_run: 2
  max_memory_cards_per_run: 1

rules:
  - id: high-risk-liability-needs-confirmation
    when:
      artifact_type: contract_review
      risk_level: high
      requires_user_decision: true
      category: liability
    decision: mini_surface
    surface: MiniIssueCard
    reason: high_risk_human_confirmation_required

  - id: normal-finding-no-ui
    when:
      artifact_type: contract_review
      risk_level: medium
    decision: no_ui
    reason: agent_can_continue_autonomously

  - id: open-full-review
    when:
      user_action: open_full_review
    decision: rich_surface
    surface: ContractReviewArtifact
    reason: user_requested_details

  - id: memory-after-preference
    when:
      signal: user_preference_detected
    decision: mini_surface
    surface: MiniMemoryCard
    reason: memory_requires_user_control
```

### 5.3 Backend schema

Add:

```text
backend/app/services/interaction_policy/schemas.py
```

Suggested types:

- `InteractionPolicy`
- `InteractionRule`
- `InteractionDecision`
- `InteractionDecisionType`
- `InteractionPolicyBudget`
- `InteractionContext`

### 5.4 Policy service

Add:

```text
backend/app/services/interaction_policy/service.py
```

Core function:

```python
class InteractionPolicyService:
    def evaluate(self, context: InteractionContext) -> InteractionDecision:
        ...
```

Decision types:

```text
no_ui
mini_surface
rich_surface
ask_text
```

### 5.5 Evaluation rules

Start simple.

Use exact match and optional missing-field tolerance.

Do not build a complex expression language yet.

Rules should be evaluated in order.

First match wins.

If no rule matches:

```text
no_ui
```

### 5.6 Budget enforcement

Respect policy budgets:

- if mini surface budget exceeded -> no_ui or grouped_summary
- if memory card budget exceeded -> no_ui
- if confirmation budget exceeded -> ask_text or grouped confirmation

This prevents UI overload.

### 5.7 Tests

Add tests for:

- high-risk liability -> MiniIssueCard
- medium risk -> no_ui
- open_full_review -> rich_surface
- memory signal -> MiniMemoryCard
- unknown context -> no_ui
- budget exceeded -> no_ui or expected fallback

---

## 6. Mini Surface Registry

Add a framework-level mini surface registry.

### 6.1 Purpose

A mini surface is a lightweight UI card that can appear inline in conversation or be rendered into a channel-native representation.

The registry should define:

- component type
- description
- supported channels
- fallback behavior
- required props schema if practical

### 6.2 Suggested file structure

Frontend:

```text
frontend/components/mini-surfaces/
  registry.ts
  MiniIssueCard.tsx
  MiniApprovalCard.tsx
  MiniRevisionPreview.tsx
  MiniMemoryCard.tsx
  MiniToolPreview.tsx
  MiniChoiceCard.tsx
```

Backend type mirror if needed:

```text
backend/app/services/surfaces/registry.py
backend/app/services/surfaces/schemas.py
```

### 6.3 Initial mini surfaces

Required:

- `MiniIssueCard`
- `MiniApprovalCard`
- `MiniRevisionPreview`
- `MiniMemoryCard`
- `MiniToolPreview`
- `MiniChoiceCard`

### 6.4 Channel mapping

Each surface should declare approximate support:

```text
web: native React card
telegram: text summary + inline keyboard
text: summary + links/buttons fallback where possible
```

Do not implement all renderers in Round 1, but the registry should prepare for this.

---

## 7. Migrate Contract Review Demo to App Runtime

The current contract review demo should keep its UX, but it should consume the new app manifest and interaction policy where possible.

### 7.1 Required behavior

- Load `contract-review-agent` manifest.
- Load its sample contract fixture.
- Use policy service to decide when to show MiniIssueCard.
- Use mini surface registry to render the mini card.
- Keep deterministic and LLM modes.
- Keep existing UIInteractionEvent persistence.

### 7.2 Do not over-migrate

Do not rewrite all demo code if not necessary.

Make the runtime visible enough that developers can see the pattern.

---

## 8. Round 1 Acceptance Criteria

Round 1 is complete when:

1. `examples/apps/contract-review-agent/app.yaml` exists.
2. `examples/apps/contract-review-agent/interaction.policy.yaml` exists.
3. Backend can load and validate app manifest.
4. Backend can load and evaluate interaction policy.
5. Mini Surface Registry exists.
6. Contract Review demo uses manifest/policy/registry at least for the primary mini surface.
7. Tests cover manifest loading and policy evaluation.
8. Documentation explains how a developer can define a new agent app.

---

# Round 2 Requirements

## 9. Backend Conversation Runtime

Round 2 should make conversation state durable and reusable across web and channel adapters.

### 9.1 Models

Add backend models:

```text
ConversationSession
ConversationTurn
```

Suggested fields:

```text
ConversationSession:
- id
- app_id
- channel
- external_thread_id nullable
- user_id nullable
- status
- metadata json
- created_at
- updated_at

ConversationTurn:
- id
- session_id
- turn_type
- role nullable
- content nullable
- surface_type nullable
- surface_payload json nullable
- observation_payload json nullable
- artifact_id nullable
- interaction_id nullable
- memory_id nullable
- created_at
```

Turn types:

```text
user_message
agent_message
attachment
mini_surface
observation
memory_candidate
system_event
rich_surface_link
```

### 9.2 APIs

Add:

```text
POST /api/conversations
GET /api/conversations/{session_id}
POST /api/conversations/{session_id}/turns
GET /api/conversations/{session_id}/turns
```

Optional:

```text
POST /api/conversations/{session_id}/messages
```

### 9.3 Runtime integration

The demo should persist turns:

- user messages
- agent messages
- attachment/file chip
- mini surfaces
- observations
- memory cards

Telegram adapter should map chat id/thread id to `ConversationSession` later.

### 9.4 Tests

Add tests for:

- create session
- append turns
- retrieve turns
- observation turn links to interaction id
- session can be associated with channel

---

## 10. Rich Surface Escalation Standard

Add a common model for opening rich surfaces.

### 10.1 Surface levels

Define:

```text
message
mini_surface
rich_surface
console_debug
```

### 10.2 Rich surface target

Suggested type:

```ts
type RichSurfaceTarget = {
  type: "drawer" | "page" | "webview";
  artifactId?: string;
  url?: string;
  title?: string;
};
```

Backend equivalent if needed:

```text
RichSurfaceLink
```

### 10.3 Behavior

- `Open Full Review` can open drawer first.
- `Open Artifact` can navigate to `/artifacts/{id}`.
- Telegram renderer should use URL/WebApp button.

---

## 11. Sales Follow-up Example App

Add a second app to prove the framework is not only contract review.

Recommended location:

```text
examples/apps/sales-followup-agent/app.yaml
examples/apps/sales-followup-agent/interaction.policy.yaml
```

### 11.1 Demo idea

User asks:

```text
帮我看看这周哪些客户应该优先跟进。
```

Agent works autonomously and shows only one decision mini surface:

```text
I found 3 customers worth following up this week.
Should I draft follow-up messages?
```

Mini surface actions:

```text
[Generate follow-up drafts]
[Change priority rule]
[Open full list]
```

Memory proposal after user preference:

```text
User prefers low-pressure, relationship-first sales follow-up tone.
```

### 11.2 Purpose

This proves the same runtime can support another vertical app:

- autonomous work
- interaction policy
- mini surface
- observation
- memory
- rich surface escalation

---

## 12. Telegram Real Mapping

Use the mini surface registry to map surfaces to Telegram output.

### 12.1 Required mapping

- MiniIssueCard -> message + inline buttons
- MiniApprovalCard -> message + inline buttons
- MiniMemoryCard -> message + Remember / Not now buttons
- RichSurfaceLink -> URL or WebApp button

### 12.2 Callback handling

Telegram callback should:

1. Resolve action id.
2. Persist UIInteractionEvent.
3. Append ConversationTurn observation if session exists.
4. Trigger next agent action if supported.

Do not block Round 2 on full Telegram Web App support.

---

## 13. Documentation and Open-source Readiness

Add or update:

```text
docs/AGENT_APP_RUNTIME.md
docs/APP_MANIFEST.md
docs/INTERACTION_POLICY.md
docs/MINI_SURFACE_REGISTRY.md
examples/apps/README.md
```

README should explain:

```text
1. Clone and run.
2. Open the demo.
3. Inspect examples/apps/contract-review-agent.
4. Create your own agent app manifest.
```

The project should feel easy to try.

---

## 14. Round 2 Acceptance Criteria

Round 2 is complete when:

1. Conversation sessions and turns are persisted.
2. The demo can load previous turns after refresh or via session id.
3. Rich surface escalation has a common model.
4. Sales Follow-up example app exists.
5. Telegram callback can map to conversation observation where possible.
6. Docs explain how to build another Tilo app.
7. Tests cover conversation APIs and second app manifest/policy loading.

---

# Codex Prompts

## Round 1 Codex Prompt

```text
Read docs/V0_5_AGENT_APP_RUNTIME_REQUIREMENTS.md.

Implement Round 1: App Definition and Interaction Runtime Foundation.

Goal:
Make Tilo apps declarative and reusable.

Tasks:
1. Add Agent App Manifest schema and loader.
2. Add examples/apps/contract-review-agent/app.yaml.
3. Add examples/apps/contract-review-agent/interaction.policy.yaml.
4. Add GET /api/apps and GET /api/apps/{app_id}.
5. Add Interaction Policy schema and service.
6. Add policy decision outputs: no_ui, mini_surface, rich_surface, ask_text.
7. Add policy budget support.
8. Add Mini Surface Registry in frontend.
9. Add required mini surfaces:
   - MiniIssueCard
   - MiniApprovalCard
   - MiniRevisionPreview
   - MiniMemoryCard
   - MiniToolPreview
   - MiniChoiceCard
10. Migrate the contract review demo to use manifest/policy/registry for the primary mini surface.
11. Add tests for manifest loading, app APIs, and policy evaluation.
12. Add docs/APP_MANIFEST.md, docs/INTERACTION_POLICY.md, docs/MINI_SURFACE_REGISTRY.md, and examples/apps/README.md.

Constraints:
- Do not redesign the demo again.
- Preserve conversation-first UX.
- Preserve deterministic and LLM modes.
- Preserve UIInteractionEvent persistence.
- Keep implementation lightweight and understandable.
```

## Round 2 Codex Prompt

```text
Read docs/V0_5_AGENT_APP_RUNTIME_REQUIREMENTS.md.

Implement Round 2: Backend Conversation Runtime and Multi-app Capability.

Goal:
Make Tilo runtime persistent, channel-friendly, and app-extensible.

Tasks:
1. Add ConversationSession and ConversationTurn backend models.
2. Add APIs:
   - POST /api/conversations
   - GET /api/conversations/{session_id}
   - POST /api/conversations/{session_id}/turns
   - GET /api/conversations/{session_id}/turns
3. Make /demo/telegram persist conversation turns where possible.
4. Add common Rich Surface Escalation model.
5. Keep Open Full Review as drawer/page escalation, not default UI.
6. Add examples/apps/sales-followup-agent/app.yaml.
7. Add examples/apps/sales-followup-agent/interaction.policy.yaml.
8. Add minimal Sales Follow-up demo data or fixture.
9. Map MiniIssueCard / MiniApprovalCard / MiniMemoryCard to Telegram renderer where possible.
10. Telegram callback should append conversation observation if session exists.
11. Add tests for conversation APIs, rich surface link model, second app loading, and Telegram callback observation.
12. Update docs/AGENT_APP_RUNTIME.md and README links.

Constraints:
- Do not turn the product into a heavy dashboard.
- Conversation remains the default interface.
- Mini surfaces appear only when useful.
- Rich surfaces open intentionally.
- No secrets in frontend or logs.
```

---

## 15. Final v0.5 Definition of Done

v0.5 is done when a developer can:

1. Open `examples/apps/contract-review-agent/app.yaml`.
2. Understand how an app is defined.
3. Open `interaction.policy.yaml`.
4. Understand when UI appears and when the agent continues autonomously.
5. Run the demo.
6. See a mini surface generated from policy.
7. Click a UI action and see it become an observation.
8. See memory controlled by explicit user confirmation.
9. Inspect a second app example and recognize the same runtime pattern.

At that point, Tilo becomes more than a demo: it becomes an agent app runtime.
