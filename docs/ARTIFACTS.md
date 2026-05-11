# Artifact System

This document defines the artifact system for Tilo Framework.

## 1. Artifact Philosophy

Artifacts are the product outputs of agent work.

A Tilo agent should not only reply with text. It should generate structured, editable, renderable deliverables that can replace parts of traditional SaaS interfaces.

## 2. Why Artifacts Matter

Traditional SaaS value often comes from presenting information in useful forms:

- reports
- tables
- dashboards
- timelines
- review panels
- approval cards
- kanban boards
- customer cards
- risk lists

Tilo should let agents generate these interfaces dynamically.

## 3. Common Artifact Shape

All artifacts should share this high-level shape:

```json
{
  "artifact_type": "document",
  "title": "Artifact title",
  "blocks": [
    {
      "id": "block_1",
      "type": "markdown",
      "data": {}
    }
  ]
}
```

## 4. Artifact Block Tiers

Artifact blocks are split into a small stable core and open-ended extension blocks.

Core blocks are the lowest-common-denominator contract that every renderer should support:

```text
markdown
table
form
approval_card
risk_panel
metric
list
```

Everything else is an extension block. Extension blocks are allowed, but they must degrade gracefully through a fallback renderer. Unknown extension blocks must not crash the frontend and must not require a bespoke component before an artifact can be inspected.

Known extension blocks in the reference implementation include:

```text
rich_text
card
risk_summary
risk_review_panel
metric_dashboard
memory_candidate_card
tool_call_preview
action_queue
editable_document_preview
editable_document_placeholder
timeline
kanban
risk_item
citation
comparison_matrix
confirmation_action
```

Do not add a new block type for every business scenario. Prefer core blocks first, then extension blocks only when the interaction shape is reusable.

## 5. Supported Artifact Types for v1.0

- document
- table
- dashboard
- kanban
- timeline
- contract_review

## 6. Document Artifact

Use for reports, plans, product documents, summaries.

Recommended blocks:

- markdown
- card
- table
- list

## 7. Table Artifact

Use for comparison tables, customer lists, candidate lists, risk tables.

Shape:

```json
{
  "type": "table",
  "data": {
    "columns": [
      {"key": "name", "label": "Name"}
    ],
    "rows": [
      {"name": "Example"}
    ]
  }
}
```

## 8. Dashboard Artifact

Use for metrics, opportunity summaries, risk overviews, project status.

Recommended blocks:

- metric
- card
- list
- table

## 9. Kanban Artifact

Use for project management or task state.

Shape:

```json
{
  "type": "kanban",
  "data": {
    "columns": [
      {
        "id": "todo",
        "title": "To Do",
        "cards": []
      }
    ]
  }
}
```

## 10. Timeline Artifact

Use for travel planning, project milestones, historical analysis, execution logs.

Shape:

```json
{
  "type": "timeline",
  "data": {
    "items": [
      {
        "time": "2026-04-25",
        "title": "Milestone",
        "description": "..."
      }
    ]
  }
}
```

## 11. Contract Review Artifact

Use for the first killer demo.

Recommended schema:

```json
{
  "artifact_type": "contract_review",
  "title": "Contract Review",
  "blocks": [
    {
      "type": "card",
      "data": {
        "title": "Summary",
        "content": "..."
      }
    },
    {
      "type": "risk_item",
      "data": {
        "clause": "Payment term",
        "risk_level": "high",
        "issue": "...",
        "suggested_revision": "..."
      }
    },
    {
      "type": "confirmation_action",
      "data": {
        "title": "Generate revised version?",
        "actions": ["approve", "reject"]
      }
    }
  ]
}
```

## 12. Rendering Rules

Frontend artifact rendering must be schema-driven.

Do not hardcode demo-only HTML for each run.

Create an `ArtifactRenderer` component that dispatches by artifact type and block type.

## 13. Editing Rules

Artifacts should eventually be editable.

For v0.1, support at least:

- viewing artifacts
- updating artifact title
- updating artifact schema JSON through API
- version field for future versioning

## 14. Artifact and Confirmation

Artifacts may contain recommended actions, but durable decisions should be represented as Confirmation records.

Do not rely only on buttons inside artifact JSON without creating corresponding Confirmation objects.

## 15. v0.1 Minimum Requirements

v0.1 is acceptable if:

1. Runtime can create at least one artifact.
2. Artifacts are persisted.
3. Frontend can render document/table/dashboard or contract_review artifact.
4. Artifact renderer is schema-driven.
5. Artifact is connected to task/run.
6. Contract review demo produces a meaningful artifact.

## 16. Do Not Do

Do not:

- return only Markdown for every output
- hardcode all artifact UI per demo
- hide artifact data in chat messages
- make artifacts impossible to retrieve later
- mix confirmation state only inside artifact JSON

## 17. v0.2 Artifact Contract

Artifacts now use `artifact_spec.v1`:

```json
{
  "version": "artifact_spec.v1",
  "artifact_type": "contract_review",
  "title": "Contract Review",
  "status": "ready",
  "blocks": [],
  "actions": [],
  "provenance": [],
  "memory_refs": [],
  "run_id": "run-id"
}
```

Core v1.0 blocks are `markdown`, `table`, `form`, `approval_card`, `risk_panel`, `metric`, and `list`.

Extension blocks may use domain-specific names, but every frontend renderer must provide a fallback path. The backend schema accepts extension block types as long as the block type is present and non-empty; validation should focus on action safety and required artifact shape rather than rejecting every unknown visual block.

Artifact actions may request confirmation, but durable user decisions must be stored as `Confirmation` records. The frontend renderer dispatches by block type through a registry and renders unsupported blocks with a safe fallback.

## 18. ROAM Interaction Blocks

ROAM-compatible blocks may include actions and state bindings:

```json
{
  "id": "approval",
  "type": "approval_card",
  "data": {},
  "actions": [
    {
      "id": "approve",
      "label": "Approve",
      "action_type": "approve",
      "confirmation_required": true,
      "payload": {}
    }
  ],
  "state_binding": {
    "entity_type": "run",
    "entity_id": "run-id",
    "field": "status"
  }
}
```

Initial ROAM blocks:

- `approval_card`
- `risk_review_panel`
- `comparison_matrix`
- `metric_dashboard`
- `memory_candidate_card`
- `tool_call_preview`
- `action_queue`

Component actions should execute through `POST /api/artifacts/{artifact_id}/actions/{action_id}`. The Artifact Action Runtime writes durable `UIInteractionEvent` observations, appends conversation observation turns when `session_id` is available, and owns action semantics for confirmations, memory candidates, tool gates, task continuation, regeneration, export placeholders, and skill promotion.

See [`ARTIFACT_ACTION_RUNTIME.md`](./ARTIFACT_ACTION_RUNTIME.md).
