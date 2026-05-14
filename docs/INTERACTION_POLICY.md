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

## Design philosophy: less UI is the default

The four decisions form a deliberate ladder, biased toward the top:

```text
no_ui  >  ask_text  >  mini_surface  >  rich_surface
```

Read as: prefer to continue silently; if the user must be involved, prefer
text; if text loses fidelity, render a focused mini surface; only escalate to
a rich surface when the user explicitly opens it.

App authors writing `interaction.policy.yaml` should expect to have **more**
`no_ui` and `ask_text` rules than `mini_surface` rules. A policy with zero
`no_ui` rules is a smell — it indicates the product is recreating a
traditional always-on dashboard rather than letting the agent decide when to
appear.

Concrete heuristics:

- A binary, irreversible decision needs a `mini_surface`.
- A multi-field structured input also needs a `mini_surface` (form).
- A conversational follow-up clarification belongs in `ask_text`.
- A status acknowledgement, a continuation hint, or a "no risk found" outcome
  belongs in `no_ui`.
- Long, browsable, editable content belongs in `rich_surface`, but it should
  be reached **after** the user accepts a `mini_surface` link to it, not
  rendered up front.

## Intent vocabulary

From v1 onwards, an interaction rule MAY emit an **intent** instead of a
renderer-specific surface name. Intents are runtime semantics, not visuals:

```text
request_approval | collect_input | present_result | offer_choices |
confirm_memory   | show_progress | escalate_to_rich | ask_clarification
```

The runtime composer translates `(intent, context)` into a fully validated
`SurfaceSpec` (see `docs/SURFACE_PROTOCOL.md`). Renderers consume the spec.
Renderer component names (e.g. `MiniIssueCard`) are no longer part of the
policy contract — they are an implementation detail of one specific
renderer.

For backward compatibility during the Surface Protocol refactor, policy YAML
may still write `surface: <name>`. The runtime treats this as a legacy alias
that will be removed in a later milestone (see `docs/REFACTOR_BLUEPRINT.md`).

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
