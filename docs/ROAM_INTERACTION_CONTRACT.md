# ROAM Interaction Contract

ROAM Interaction Contract is Tilo's lightweight declarative layer for defining how agents interact with humans through AI-native SaaS components.

It is not positioned as a new industry standard. At this stage, it is a practical contract format inside Tilo that helps developers build better AI-native agent applications.

ROAM Interaction Contract answers four questions:

```text
When should the agent interact with the user?
What should the UI render?
What should happen after the user acts?
What should be memorized or audited?
```

It complements existing agent protocols and frameworks instead of replacing them.

---

## 1. Why Interaction Contracts?

Most agent frameworks already provide ways to:

- call tools
- orchestrate tasks
- connect to external resources
- coordinate multiple agents
- store memory

But AI-native SaaS applications need one more layer:

```text
Agent -> UI -> Human -> Observation -> Action -> Memory
```

Without an interaction contract, an agent may:

- ask users questions at the wrong time
- execute risky actions without approval
- render inconsistent UI
- hide key decisions inside chat text
- fail to record user decisions as durable observations
- miss valuable memory signals

An interaction contract makes human-agent collaboration explicit.

---

## 2. Relationship to ROAM Loop

Tilo's core loop is:

```text
Render -> Observe -> Act -> Memorize
```

ROAM Interaction Contract maps directly to the loop:

| ROAM Stage | Contract Responsibility |
|---|---|
| Render | Define which component or artifact surface to show |
| Observe | Define which user events should be captured |
| Act | Define what the agent/runtime/tool should do after each event |
| Memorize | Define what can become memory candidates or audit records |

In short:

> ROAM is the loop. Interaction Contract is the declarative plan for how that loop interacts with humans.

---

## 3. Relationship to Skills

Interaction Contract can be packaged inside a Skill.

A future Tilo skill package may look like this:

```text
skills/
  contract-review/
    skill.yaml
    instructions.md
    tools.yaml
    mcp_servers.yaml
    interaction.contract.yaml
    artifact.schema.json
    memory.policy.yaml
    examples/
    evals/
```

This means a skill can define not only how an agent should think or which tools it can use, but also:

- when it should ask for approval
- which UI component should be rendered
- which user actions are valid
- what happens after each action
- what memory candidates should be proposed

This turns a skill from a prompt package into an AI-native SaaS capability package.

---

## 4. Relationship to MCP, A2A, and Other Agent Frameworks

ROAM Interaction Contract is designed to be compatible with existing ecosystems.

It does not replace MCP, A2A, LangGraph, LlamaIndex, CrewAI, AutoGen, or other agent frameworks.

Instead, it can sit above or beside them as the interaction layer.

### MCP

MCP connects agents to tools, data sources, and external resources.

Tilo can reference MCP tools inside Interaction Contracts.

Example:

```yaml
act:
  approve_tool_call:
    type: mcp_tool_invocation
    server: crm-mcp
    tool: send_follow_up_email
    confirmation_required: true
```

### A2A

A2A-style protocols connect agents to other agents.

Tilo can use an interaction contract to define when a human decision should trigger another agent.

Example:

```yaml
act:
  request_legal_review:
    type: agent_handoff
    protocol: a2a
    target_agent: legal-review-agent
```

### Existing Agent Frameworks

Tilo does not require developers to abandon their existing agent runtime.

An app can use:

- LangGraph for stateful agent orchestration
- LlamaIndex for retrieval
- MCP for tools
- A2A for agent collaboration
- Tilo for ROAM interaction contracts, AI-native components, artifacts, observations, and memory governance

### Simple Positioning

```text
MCP connects tools.
A2A connects agents.
Skills package capabilities.
ROAM Interaction Contract connects agents, UI, humans, and memory.
```

---

## 5. Design Principles

### 5.1 Lightweight first

Do not over-engineer the contract format.

The first version should be simple enough for developers to read and write by hand.

### 5.2 Declarative when possible

Developers should describe interaction intent, not manually code every UI state.

### 5.3 Compatible by design

Contracts should be able to reference external tools, MCP servers, A2A agents, custom handlers, and existing agent workflows.

### 5.4 Human decisions are durable

Important user actions should create durable observations, confirmations, feedback, memory candidates, or audit records.

### 5.5 Default contracts should exist

Developers should not be forced to define a contract for every small app.

Tilo should provide default contracts for common situations:

- high-risk action approval
- memory candidate confirmation
- tool call preview
- multi-option decision
- comparison review
- document revision approval

### 5.6 Custom contracts should be possible

Enterprise teams should be able to define their own rules.

Examples:

- legal approval workflow
- finance approval workflow
- HR candidate review workflow
- sales follow-up workflow
- customer support escalation workflow

---

## 6. Conceptual Contract Shape

A ROAM Interaction Contract can be represented as YAML or JSON.

Example shape:

```yaml
id: contract-review.roam
version: 0.1
name: Contract Review Interaction Contract

description: Defines human interaction points for contract review workflows.

triggers:
  - id: high-risk-clause-detected
    when:
      event: risk.detected
      condition:
        risk_level: high

    render:
      component: RiskReviewPanel
      title: High-risk clause review
      props:
        show_original_clause: true
        show_suggested_revision: true
        show_evidence: true

    observe:
      events:
        - approve_revision
        - edit_revision
        - reject_revision

    act:
      approve_revision:
        type: agent_action
        name: generate_revised_clause
      edit_revision:
        type: agent_action
        name: update_revision_instruction
      reject_revision:
        type: agent_action
        name: ask_for_review_direction

    memorize:
      approve_revision:
        candidate:
          type: user_preference
          content_template: User prefers conservative contract risk handling with actionable revision suggestions.
          requires_confirmation: true
```

---

## 7. Example: High-risk Tool Call

```yaml
id: high-risk-tool-call-approval
version: 0.1
name: High-risk Tool Call Approval

triggers:
  - id: before-high-risk-tool-call
    when:
      event: tool.invoke.requested
      condition:
        tool_permission_level: high

    render:
      component: ToolCallPreview
      title: Approve external action
      props:
        show_tool_name: true
        show_payload_summary: true
        show_permission_level: true

    observe:
      events:
        - approve_tool_call
        - reject_tool_call
        - edit_payload

    act:
      approve_tool_call:
        type: tool_invocation
        confirmation_required: true
      reject_tool_call:
        type: cancel_action
      edit_payload:
        type: update_tool_payload

    memorize:
      approve_tool_call:
        candidate:
          type: decision
          content_template: User approved this category of tool action after reviewing payload summary.
          requires_confirmation: false
```

---

## 8. Example: Sales Follow-up Decision

```yaml
id: sales-follow-up.roam
version: 0.1
name: Sales Follow-up Interaction Contract

triggers:
  - id: follow-up-recommendations-ready
    when:
      event: recommendations.generated
      condition:
        recommendation_type: sales_follow_up

    render:
      component: DecisionTable
      title: Review follow-up recommendations
      props:
        allow_multi_select: true
        show_reasoning_summary: true
        show_customer_priority: true

    observe:
      events:
        - select_recommendation
        - approve_selected
        - reject_recommendation

    act:
      approve_selected:
        type: agent_action
        name: prepare_follow_up_messages
      reject_recommendation:
        type: feedback
        feedback_type: not_useful

    memorize:
      approve_selected:
        candidate:
          type: user_preference
          content_template: User prioritizes follow-ups based on urgency and near-term revenue impact.
          requires_confirmation: true
```

---

## 9. Developer Experience Levels

Tilo should support three levels of developer experience.

### Level 1: Zero-config defaults

Developers only build an agent. Tilo chooses default interaction contracts.

Examples:

| Situation | Default Component |
|---|---|
| high-risk action | ApprovalCard |
| tool invocation | ToolCallPreview |
| memory candidate | MemoryCandidateCard |
| multi-option choice | DecisionTable |
| comparison task | ComparisonMatrix |
| document revision | EditableDocument |

### Level 2: Declarative contracts

Developers add `interaction.contract.yaml` to customize behavior.

This is the recommended path for most serious apps.

### Level 3: Custom components and handlers

Advanced teams can register custom components and custom contract handlers.

Use cases:

- legal SaaS
- finance approval systems
- HR review platforms
- healthcare or compliance workflows
- internal enterprise agent platforms

---

## 10. Contract Runtime Responsibilities

A future Interaction Contract Runtime should:

1. Match trigger events.
2. Evaluate conditions.
3. Select render component.
4. Validate component props.
5. Record observe events.
6. Route user actions to agent actions, tool invocations, feedback, memory candidates, or confirmations.
7. Enforce confirmation gates.
8. Emit UIInteractionEvent.
9. Connect observations to memory extraction.
10. Keep everything traceable.

---

## 11. Minimal v0.1 Contract Runtime

The first implementation does not need a full engine.

Start with:

- a few built-in default contracts
- a lightweight YAML/JSON schema
- a resolver that maps event + condition to component
- component registry integration
- durable UIInteractionEvent logging
- memory/confirmation integration

Do not build a complex rules engine too early.

---

## 12. Relationship to Artifact Spec

Artifact Spec defines what gets rendered.

Interaction Contract defines why and when it gets rendered, and what happens next.

```text
Interaction Contract -> selects component and actions
Artifact Spec -> carries renderable blocks and actions
Component Registry -> renders the actual frontend component
Observation Store -> records what the user did
Memory Engine -> turns confirmed observations into memory
```

---

## 13. Public Positioning

Use lightweight language publicly:

```text
Tilo provides a declarative interaction contract layer for AI-native SaaS agents.
```

Avoid overclaiming:

```text
Tilo defines the new universal standard for agent UI.
```

A better explanation:

```text
ROAM Interaction Contract is a practical way to describe when agents should render UI, what humans can do, how the agent should continue, and what should become memory.
```

---

## 14. Suggested README Copy

```text
ROAM Interaction Contract

Tilo includes a lightweight declarative interaction contract layer. It defines when an agent should render a human interaction, which AI-native component should appear, what events should be observed, what action should happen next, and what can become memory.

It is designed to work with existing agent ecosystems: use MCP for tools, A2A for agent collaboration, existing frameworks for orchestration, and Tilo for the human-facing ROAM interaction layer.
```

---

## 15. Codex Prompt

```text
Read docs/ROAM_INTERACTION_CONTRACT.md.

Implement the first lightweight ROAM Interaction Contract foundation.

Do not build a complex standard or rules engine.

Start with:
1. Add example interaction contracts under examples/interaction-contracts/.
2. Add a minimal contract schema or TypeScript/Pydantic types if appropriate.
3. Add default contract mappings:
   - high-risk action -> ApprovalCard
   - tool invocation -> ToolCallPreview
   - memory candidate -> MemoryCandidateCard
   - comparison output -> ComparisonMatrix
   - document revision -> EditableDocumentPreview
4. Connect contracts to existing Artifact actions and UIInteractionEvent where possible.
5. Update README and docs to explain compatibility with MCP, A2A, Skills, and existing agent frameworks.

Keep the implementation lightweight and practical.
```
