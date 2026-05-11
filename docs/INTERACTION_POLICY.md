# Interaction Policy

Tilo follows this product rule:

```text
Agent by default. UI when necessary.
```

An interaction policy decides whether the runtime should continue silently, render a mini surface, open a rich surface, or ask for text.

Supported decisions:

- `no_ui`: the agent can continue without UI.
- `mini_surface`: render one lightweight inline decision card.
- `rich_surface`: open or link to a full artifact surface.
- `ask_text`: ask the user for plain text instead of showing more UI.

Policy files live next to app manifests. The contract review example is:

```text
examples/apps/contract-review-agent/interaction.policy.yaml
```

Rules are evaluated in order. First match wins. Matching is intentionally simple in Round 1: exact field matches with no expression language.

## Boundary

InteractionPolicy is a coarse routing layer. It answers:

```text
Should the runtime show no UI, ask text, render a mini surface, or open a rich surface?
```

It should not become a half-rule-engine for business semantics.

Good policy inputs:

- risk level;
- user action name;
- artifact type;
- whether a user decision is required;
- whether a memory signal was detected;
- UI budget counters.

Poor policy inputs:

- long legal reasoning;
- pricing calculations;
- CRM scoring formulas;
- permission checks;
- tool execution rules;
- multi-step domain workflows.

Those belong in runtime services, tool implementations, code hooks, or app-specific generators. The policy may route to a surface after those services produce a clear signal, but it should not try to encode the full decision in YAML.

If a future app needs complex checks, prefer an explicit code hook boundary such as:

```yaml
when:
  signal: high_risk_detected
  callable: my_app.policy_hooks.needs_liability_review
```

Callable hooks must be backend-owned, typed, tested, and treated as runtime code. They should not turn policy files into arbitrary untrusted execution.

Budgets prevent UI overload:

- `max_mini_surfaces_per_run`
- `max_confirmations_per_run`
- `max_memory_cards_per_run`

If a budget is exceeded, the service returns `no_ui` or `ask_text` depending on the kind of interaction.

Round 1.5 note: budget counters are still supplied by the caller in `InteractionContext`
(`mini_surfaces_used`, `confirmations_used`, `memory_cards_used`). They are explicit
runtime inputs, not yet durable backend-computed counters. Round 2 should derive them
from persisted conversation turns, confirmations, and UI interaction events.

The public `/demo` treats backend runtime behavior as the source of truth. Frontend code may show fallback copy, but it must not own the semantics of approvals, memory confirmation, tool invocation, or task continuation.
