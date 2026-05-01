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

Budgets prevent UI overload:

- `max_mini_surfaces_per_run`
- `max_confirmations_per_run`
- `max_memory_cards_per_run`

If a budget is exceeded, the service returns `no_ui` or `ask_text` depending on the kind of interaction.
