# Tilo Surface Protocol v1

> Status: **Normative** (Phase 0 deliverable of `docs/REFACTOR_BLUEPRINT.md`)
> Schema version string: `tilo.surface.v1`
> JSON Schema: `frontend/lib/surface.schema.json` (auto-generated)
> Pydantic models: `backend/app/schemas/surface.py`

This document is the contract between Tilo's runtime and any renderer (React, Vue, Telegram, Slack, email, server-rendered HTML, …). The runtime emits `SurfaceSpec` JSON. Renderers consume it. **Renderers MUST NOT be referenced by name from the runtime.**

---

## 1. Design philosophy

### 1.1 Surface-as-Data, not Surface-as-Component
The runtime never knows whether the consumer is React, Vue, or Telegram. It emits a structured description of *intent + content*. Renderers map block types to their own visual primitives.

### 1.2 Less UI is the default
Tilo follows this ladder, biased toward the top:

```
no_ui  >  ask_text  >  mini_surface  >  rich_surface
```

A surface should appear **only** when text alone would lose information or fidelity. App authors writing `interaction.policy.yaml` should expect to have *more* `no_ui` and `ask_text` rules than `mini_surface` rules. A policy with zero `no_ui` rules is a smell.

### 1.3 One focused decision per surface
A `SurfaceSpec` represents **one** thing the user should look at right now. Stuffing five blocks into one surface recreates SaaS-dashboard mindset. The runtime is allowed (and encouraged) to emit multiple `SurfaceTurn`s in sequence rather than one monolith.

### 1.4 Block vocabulary is closed
The block type set is **closed** in v1. Adding a new type is a protocol-version change. Open-ended `data: any` is rejected at validation time.

### 1.5 Every surface is renderable as text
Every `SurfaceSpec` has `fallback_text`. Every `Block` has `fallback_text`. A renderer that understands nothing else can always show the text. This is what makes the protocol channel-agnostic.

### 1.6 Action semantics are owned by the backend
Block actions reuse the existing `ArtifactAction` contract unchanged. The frontend renders intent and emits `executeArtifactAction(...)`. The backend interprets, validates, and persists. This is consistent with Tilo's runtime principle: *frontend renders intent, backend owns action semantics*.

---

## 2. Top-level shape

```jsonc
{
  "schema_version": "tilo.surface.v1",
  "surface_id": "srf_01HXXXX...",          // ULID/UUID, unique per emission
  "turn_id":    "trn_01HXXXX...",          // FK -> SurfaceTurn (run-scoped ordinal)
  "run_id":     "run_...",                 // FK -> Run

  "intent": "request_approval",            // closed enum, see §3
  "budget_hint": "mini",                   // "mini" | "rich"
  "block_compat": "graceful",              // "graceful" | "strict"

  "blocks": [ /* Block[]; ordered, MUST be non-empty */ ],

  "fallback_text": "Liability cap is 3 months ARR (industry: 12). Approve, negotiate, or open full review?",

  "fallbacks": {                           // OPTIONAL channel-specific hints
    "telegram": { "inline_keyboard": [[ /* button rows */ ]] },
    "slack":    { "blocks": [ /* Slack Block Kit */ ] },
    "email":    { "html": "<p>...</p>" }
  },

  "provenance": [ { "type": "task", "id": "tsk_...", "label": "..." } ],
  "memory_refs": [ "mem_..." ],

  "metadata": { /* free-form, opaque to protocol */ }
}
```

### Field rules

| Field | Required | Notes |
|---|---|---|
| `schema_version` | yes | MUST be exactly `"tilo.surface.v1"` for this version |
| `surface_id` | yes | unique, opaque |
| `turn_id` | yes | links to backend `SurfaceTurn` row |
| `run_id` | yes | for auditing and reflection |
| `intent` | yes | closed enum, see §3 |
| `budget_hint` | yes | renderer hint: `mini` = inline; `rich` = drawer/page |
| `block_compat` | yes | unknown-block policy, see §6 |
| `blocks` | yes | non-empty array; ordered |
| `fallback_text` | yes | non-empty; the text-only representation |
| `fallbacks` | no | per-channel hints; renderers may ignore |
| `provenance` | no | array of provenance refs (existing shape) |
| `memory_refs` | no | array of memory ids |
| `metadata` | no | opaque |

---

## 3. Intent vocabulary (closed)

`intent` is a backend-internal classification of *why* this surface is being shown. Renderers may use it to choose a default visual treatment, but MUST NOT depend on it for correctness.

| intent | when to use | typical blocks | typical actions |
|---|---|---|---|
| `request_approval` | a binary or small-N decision is needed before the agent can continue | `heading`, optional `evidence`, `decision` | `approve`, `reject` |
| `collect_input` | structured fields are required to proceed | `heading`, `form` | `confirm`, `continue_task` |
| `present_result` | read-only payload for the user to consume | `heading`, `text`, `list`, `comparison`, `artifact_link` | `approve` (acknowledge), `regenerate` |
| `offer_choices` | pick one of N alternatives | `heading`, `decision` (multi-option) | `select` |
| `confirm_memory` | ask whether to remember a fact / preference | `heading`, `text`, `decision` | `create_memory`, `reject` |
| `show_progress` | long-running work status | `heading`, `progress`, optional `list` | `regenerate`, `reject` (cancel) |
| `escalate_to_rich` | inline summary that links to a full artifact | `heading`, `text`, `artifact_link` | `select`, `continue_task` |
| `ask_clarification` | open-ended text follow-up | `heading`, `text` | `continue_task` |

A composer that cannot find an appropriate intent for a planner step MUST default to `present_result` with a `fallback` block, **not** invent a new intent.

---

## 4. Block vocabulary (closed)

Every block has the common envelope:

```jsonc
{
  "id": "blk_...",
  "type": "<one of the 12 below>",
  "data": { /* type-specific shape; see below */ },
  "fallback_text": "...",                  // REQUIRED, non-empty
  "actions": [ /* ArtifactAction[]; OPTIONAL */ ],
  "state_binding": { /* OPTIONAL; existing StateBinding shape */ }
}
```

> **All shapes below are normative.** Pydantic models in `backend/app/schemas/surface.py` are the source of truth.

### 4.1 `heading`
A short title with optional severity tag.
```jsonc
{
  "type": "heading",
  "data": {
    "text": "Liability cap is unusually low",
    "severity": "high"   // optional: low | medium | high | info
  }
}
```

### 4.2 `text`
Plain prose. Renderers MAY honor inline emphasis using `**bold**` and `_italic_`. No HTML, no Markdown links, no headings.
```jsonc
{ "type": "text", "data": { "content": "Industry standard caps are 12 months ARR." } }
```

### 4.3 `evidence`
A quoted excerpt with provenance.
```jsonc
{
  "type": "evidence",
  "data": {
    "excerpt": "Vendor's aggregate liability is capped at three (3) months of fees ...",
    "source_ref": "clause-7.2",
    "source_label": "Section 7.2"   // optional
  }
}
```

### 4.4 `comparison`
Side-by-side or table-shaped delta.
```jsonc
{
  "type": "comparison",
  "data": {
    "shape": "side_by_side",   // "side_by_side" | "table"
    "left":  { "label": "Industry", "value": "12 months ARR" },
    "right": { "label": "This contract", "value": "3 months ARR", "severity": "high" },
    "rows":  []                // used when shape == "table"
  }
}
```
For `shape: "table"`, `rows` is a list of `{ label, left, right, severity? }`. `left` and `right` MUST be omitted in table shape.

### 4.5 `decision`
1..N options the user can pick.
```jsonc
{
  "type": "decision",
  "data": {
    "prompt": "How would you like to proceed?",   // optional
    "mode": "single",                              // "single" | "multi"
    "options": [
      {
        "id": "opt_approve",
        "label": "Approve as drafted",
        "value": "approve",
        "action_id": "approve_revision",          // FK to one of block.actions
        "severity": "info"                        // optional rendering hint
      },
      { "id": "opt_negotiate", "label": "Request 12 months", "value": "negotiate", "action_id": "request_higher_cap" },
      { "id": "opt_open",      "label": "Open full review",   "value": "open_rich", "action_id": "open_full" }
    ]
  }
}
```
Renderers MUST disable options whose referenced `action_id` is not present in `block.actions`.

### 4.6 `form`
Structured input fields.
```jsonc
{
  "type": "form",
  "data": {
    "fields": [
      {
        "name": "cap_months",
        "label": "Requested cap (months)",
        "kind": "number",                  // text | number | textarea | select | toggle | date
        "required": true,
        "min": 1, "max": 36,               // numeric only
        "options": [],                     // select only
        "placeholder": "12"
      }
    ],
    "submit_action_id": "submit_cap"       // FK to one of block.actions
  }
}
```
Validation rules:
- `kind: "select"` MUST include `options: [{label, value}, ...]`.
- `kind: "number"` MAY include `min`/`max`/`step`.
- Renderer MUST not submit until all `required` fields are filled.

### 4.7 `progress`
Step list, percentage, or status.
```jsonc
{
  "type": "progress",
  "data": {
    "shape": "steps",                   // "steps" | "percent" | "status"
    "percent": 0,                       // 0..100, used when shape == "percent"
    "status": "running",                // used when shape == "status"; free string
    "steps": [
      { "id": "s1", "label": "Recall memory", "state": "done" },
      { "id": "s2", "label": "Review risks",  "state": "running" },
      { "id": "s3", "label": "Draft revision", "state": "pending" }
    ]
  }
}
```
`state ∈ { pending, running, done, failed, skipped }`.

### 4.8 `list`
Simple bullet or ordered items.
```jsonc
{
  "type": "list",
  "data": {
    "ordered": false,
    "items": [
      { "text": "Liability cap caps at 3 months", "severity": "high" },
      { "text": "Termination requires 90 days notice", "severity": "medium" }
    ]
  }
}
```

### 4.9 `link`
Out-of-band navigation hint.
```jsonc
{
  "type": "link",
  "data": {
    "label": "View full clause text",
    "url": "https://example.com/...",
    "target": "drawer"                   // "drawer" | "page" | "webview" | "external"
  }
}
```

### 4.10 `editable`
A region the user can edit; submission becomes an `edit` action observation.
```jsonc
{
  "type": "editable",
  "data": {
    "kind": "rich_text",                 // "rich_text" | "structured"
    "value": "Vendor's aggregate liability is capped at twelve (12) months ...",
    "schema": null,                      // for kind=structured: a JSON schema
    "submit_action_id": "save_edit",     // FK
    "highlights": ["Increased cap to 12 months"]
  }
}
```

### 4.11 `artifact_link`
Reference a full Artifact. The mini→rich escalation path.
```jsonc
{
  "type": "artifact_link",
  "data": {
    "artifact_id": "art_...",
    "title": "Contract Review · v3",
    "summary": "12 risk findings, 4 high",
    "open_action_id": "open_full"
  }
}
```

### 4.12 `fallback`
Last-resort text-only block. Always renderable. Composers SHOULD include a `fallback` block when emitting a surface that uses any block type beyond the v0 core (`heading`, `text`, `decision`).
```jsonc
{
  "type": "fallback",
  "data": { "content": "Liability cap is 3 months ARR (industry standard: 12). Reply with 'approve' or 'negotiate'." }
}
```

---

## 5. Action contract

Block-level `actions` reuse the existing `ArtifactAction` shape **unchanged**:

```jsonc
{
  "id": "approve_revision",
  "label": "Approve",
  "action_type": "approve",            // existing closed enum
  "confirmation_required": true,
  "confirmation_id": null,
  "payload": { "operation": "approve_revision" },
  "state_binding": { "entity_type": "confirmation", "entity_id": "...", "field": null }
}
```

Supported `action_type`s in v1 (unchanged from `artifact_spec.v1`):
`approve | reject | edit | select | continue_task | regenerate | invoke_tool | create_memory | promote_skill | export | confirm`.

Adding new action types is a **separate** protocol bump and not in scope for this refactor.

---

## 6. Versioning & forward compatibility

### 6.1 Schema version
`schema_version` is a literal string. Renderers MUST refuse versions they do not understand and emit `surface.render_failed` with `reason: "unknown_schema_version"`.

### 6.2 Unknown blocks
- `block_compat: "graceful"` (default and recommended): an unknown `type` is rendered as `block.fallback_text`. The renderer emits `surface.block_fallback_used` with `block_id`.
- `block_compat: "strict"`: an unknown `type` aborts rendering. The renderer emits `surface.render_failed` with `reason: "unknown_block_type"` and `block_id`.

### 6.3 Unknown intents
A renderer that does not recognize an `intent` MUST still render. Intent affects defaults only.

### 6.4 Adding fields
New optional fields MAY be added in a minor version bump (e.g. `tilo.surface.v1.1`). Required field changes require a major bump (`v2`).

---

## 7. Validation rules (normative)

A `SurfaceSpec` is **valid** iff:

1. `schema_version == "tilo.surface.v1"`.
2. `intent` is in §3.
3. `blocks` is non-empty.
4. Every block's `type` is in §4.
5. Every block's `data` matches its type-specific shape per §4.
6. Every `fallback_text` (top-level and per block) is a non-empty string.
7. Every `decision.option.action_id` either references an action present in the same block's `actions`, or is the literal value `"__noop__"` (used when the option does not trigger a backend action, e.g. "Cancel" purely client-side).
8. Every `form.submit_action_id`, `editable.submit_action_id`, `artifact_link.open_action_id` references an action present in the same block's `actions`.
9. `budget_hint ∈ {"mini", "rich"}`.
10. `block_compat ∈ {"graceful", "strict"}`.

The Pydantic model in `backend/app/schemas/surface.py` enforces all 10 rules. The exported JSON Schema enforces 1-6 and 9-10; rules 7-8 require cross-block validation and are enforced post-load.

---

## 8. Channel fallbacks

`fallbacks` is purely advisory. Renderers MAY ignore unknown keys.

### 8.1 `telegram.inline_keyboard`
Format matches Telegram Bot API:
```jsonc
{ "inline_keyboard": [[ { "text": "Approve", "callback_data": "act:approve_revision" } ]] }
```

### 8.2 `slack.blocks`
Slack Block Kit array. Tilo runtime does not validate Slack-specific shape; it is treated opaquely.

### 8.3 `email.html`
A standalone HTML fragment. Renderers SHOULD treat as untrusted and sanitize.

---

## 9. Mapping from existing `artifact_spec.v1`

For the duration of the refactor (per ADR-8), `artifact_spec.v1` and `surface_spec.v1` coexist. Mapping rules:

| `artifact_spec.v1` block type | Surface Protocol equivalent |
|---|---|
| `markdown` | `text` (or `fallback` if it contains links/headings) |
| `risk_summary` | `heading` + `list` (severity per item) |
| `approval_card` | one `decision` block with two options |
| `risk_review_panel` | `heading` + `list` of `evidence` blocks; one `decision` per item |
| `metric_dashboard` | `heading` + `list` (each metric → list item) |
| `editable_document_preview` | `editable` |
| `memory_candidate_card` | `heading` + `decision` (intent: `confirm_memory`) |
| `tool_call_preview` | `heading` + `text` + `decision` |
| `action_queue` | `list` (each item → list entry) |
| `comparison_matrix` | `comparison` (table shape) |
| `confirmation_action` | `decision` |
| `kanban`, `timeline`, `metric`, `risk_item`, `risk_panel` | `list` with `severity`, optional `evidence` |

The deterministic composer in Phase 2 implements this mapping for backward compatibility.

---

## 10. Worked example: contract review approval (mini surface)

```jsonc
{
  "schema_version": "tilo.surface.v1",
  "surface_id": "srf_01HX0",
  "turn_id":    "trn_01HX0",
  "run_id":     "run_abc",
  "intent": "request_approval",
  "budget_hint": "mini",
  "block_compat": "graceful",

  "blocks": [
    {
      "id": "blk_h",
      "type": "heading",
      "data": { "text": "Liability cap unusually low", "severity": "high" },
      "fallback_text": "High-severity finding: liability cap unusually low."
    },
    {
      "id": "blk_e",
      "type": "evidence",
      "data": {
        "excerpt": "Vendor's aggregate liability is capped at three (3) months of fees ...",
        "source_ref": "clause-7.2",
        "source_label": "Section 7.2"
      },
      "fallback_text": "Section 7.2 caps liability at 3 months of fees."
    },
    {
      "id": "blk_c",
      "type": "comparison",
      "data": {
        "shape": "side_by_side",
        "left":  { "label": "Industry",      "value": "12 months ARR" },
        "right": { "label": "This contract", "value": "3 months ARR", "severity": "high" }
      },
      "fallback_text": "Industry: 12 months ARR. This contract: 3 months ARR."
    },
    {
      "id": "blk_d",
      "type": "decision",
      "data": {
        "prompt": "How should I proceed?",
        "mode": "single",
        "options": [
          { "id": "o1", "label": "Approve as drafted",  "value": "approve",   "action_id": "approve_revision" },
          { "id": "o2", "label": "Request 12 months",   "value": "negotiate", "action_id": "request_higher_cap" },
          { "id": "o3", "label": "Open full review",    "value": "open_rich", "action_id": "open_full" }
        ]
      },
      "fallback_text": "Reply: approve / negotiate / open full review.",
      "actions": [
        { "id": "approve_revision",   "label": "Approve",     "action_type": "approve", "confirmation_required": true,  "payload": { "operation": "approve_revision" } },
        { "id": "request_higher_cap", "label": "Negotiate",   "action_type": "select",  "confirmation_required": false, "payload": { "operation": "negotiate", "target_months": 12 } },
        { "id": "open_full",          "label": "Open Review", "action_type": "select",  "confirmation_required": false, "payload": { "operation": "open_rich" } }
      ]
    }
  ],

  "fallback_text": "Liability cap is 3 months ARR (industry: 12). Approve, negotiate, or open full review?",

  "fallbacks": {
    "telegram": {
      "inline_keyboard": [
        [
          { "text": "✅ Approve",   "callback_data": "act:approve_revision" },
          { "text": "🤝 Negotiate", "callback_data": "act:request_higher_cap" }
        ],
        [ { "text": "📄 Open full review", "callback_data": "act:open_full" } ]
      ]
    }
  },

  "provenance": [ { "type": "task", "id": "tsk_xyz", "label": "Review AI services contract" } ],
  "memory_refs": []
}
```

---

## 11. Non-goals (v1)

The following are deliberately **out of scope** for `tilo.surface.v1`:

- Streaming partial blocks (a surface is atomic).
- Animations / motion specs.
- Layout primitives (rows, columns, grid). Renderers own layout.
- Theming. Renderers own theming.
- Inline media (images, video). Use `link` with `target: "external"` until v2.
- Inline tool execution UIs beyond what `decision`/`form` covers.

---

## 12. Change log

- v1 — initial release as part of `docs/REFACTOR_BLUEPRINT.md` Phase 0.
