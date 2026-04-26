# Interoperability

Tilo is designed to work with existing agent frameworks and protocols.

Tilo does not ask developers to abandon their current agent stack. Instead, Tilo focuses on a specific missing layer:

```text
Agent ↔ UI ↔ Human ↔ Observation ↔ Memory
```

This is the role of the ROAM Loop and ROAM Interaction Contract.

---

## 1. Positioning

Tilo's interoperability position is simple:

```text
MCP connects tools.
A2A connects agents.
Skills package capabilities.
Existing agent frameworks orchestrate reasoning and execution.
Tilo connects agents, UI, humans, observations, and memory.
```

Tilo should be seen as an AI-native SaaS interaction layer, not a replacement for every agent framework.

---

## 2. With MCP

MCP is useful for connecting agents to external tools, resources, and data sources.

Tilo can reference MCP tools from interaction contracts.

Example:

```yaml
act:
  approve_tool_call:
    type: mcp_tool_invocation
    server: crm-mcp
    tool: send_follow_up_email
    confirmation_required: true
```

In this model:

- MCP provides the external tool connection.
- Tilo renders the human approval UI.
- The user approves or rejects the action.
- Tilo records the interaction as durable observation.
- The runtime invokes the MCP tool only after approval.

---

## 3. With A2A-style Agent Protocols

A2A-style protocols are useful for agent-to-agent collaboration.

Tilo can use interaction contracts to decide when a human action should trigger a handoff to another agent.

Example:

```yaml
act:
  request_legal_review:
    type: agent_handoff
    protocol: a2a
    target_agent: legal-review-agent
```

In this model:

- A2A connects agents.
- Tilo decides when human review or agent handoff should happen.
- Tilo renders a clear interaction surface for the human.
- The handoff remains traceable.

---

## 4. With Skills

Tilo treats skills as capability packages.

A future Tilo skill package may include:

```text
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

This allows a skill to define:

- how the agent should behave
- which tools it can use
- which MCP servers it can call
- which UI interactions should appear
- what user decisions should be observed
- what memory candidates should be proposed
- how the skill should be evaluated

---

## 5. With Existing Agent Frameworks

Tilo can sit beside existing agent frameworks.

Examples:

| Framework Layer | Possible Role |
|---|---|
| LangGraph | stateful agent orchestration |
| LlamaIndex | retrieval and knowledge workflows |
| CrewAI / AutoGen | multi-agent coordination |
| MCP | tool and resource integration |
| A2A-style protocols | agent collaboration |
| Tilo | ROAM interaction, artifact UI, observations, memory governance |

Tilo should not force all logic into its own runtime.

A developer should be able to use their preferred agent framework, then use Tilo to handle:

- rendering AI-native SaaS components
- capturing user interaction as observation
- confirmation gates
- artifact delivery
- memory review
- interaction-driven self-improvement

---

## 6. Design Rule

When integrating with external frameworks or protocols, preserve this boundary:

```text
External framework: reasoning, orchestration, retrieval, tools, agents
Tilo: interaction contract, generated UI, observation, confirmation, memory governance
```

This keeps Tilo focused and interoperable.

---

## 7. Public Messaging

Use lightweight wording:

```text
Tilo provides a declarative interaction contract layer for AI-native SaaS agents. It is designed to work with existing agent ecosystems such as MCP, A2A-style agent collaboration, skills, and orchestration frameworks.
```

Avoid overclaiming:

```text
Tilo defines the universal standard for agent UI.
```

Tilo should earn broader adoption through practical examples, not premature standard language.
