# Example Apps

This directory contains declarative Tilo agent app examples.

Start here:

```text
examples/apps/contract-review-agent/app.yaml
examples/apps/contract-review-agent/interaction.policy.yaml
examples/apps/sales-followup-agent/app.yaml
examples/apps/sales-followup-agent/interaction.policy.yaml
```

The manifest describes what the app is, which surfaces it can render, which sample inputs it uses, and which channels it supports.

The policy describes when UI should appear:

```text
no_ui | mini_surface | rich_surface | ask_text
```

The two included apps prove the runtime is reusable:
- `contract-review-agent` exercises risk review, approval, rich artifact escalation, and memory candidate flow.
- `sales-followup-agent` exercises a different domain with a choice card, preference memory signal, and on-demand rich draft surface.

Core runtime concepts:
- Agent App Manifest
- Interaction Policy
- Mini Surface Registry
- Conversation Runtime
- Observation Context
- ORID Context Reflection
- Memory Lifecycle

To add another app:

1. Create `examples/apps/{app_id}/app.yaml`.
2. Create `examples/apps/{app_id}/interaction.policy.yaml`.
3. Keep sample inputs inside the app directory, under `examples/contracts`, or under `examples/fixtures`.
4. Add only the mini surfaces needed for meaningful human decisions.
5. Verify the app appears in `GET /api/apps`.

Do not put secrets in manifests or policies.

The sales follow-up app includes minimal fixture data at:

```text
examples/apps/sales-followup-agent/fixtures/lead-summary.md
examples/fixtures/sales-followup-sample.json
```

It is intentionally small so the same app runtime can be tested without becoming a second custom demo.

Useful local API checks:

```bash
curl http://localhost:8000/api/apps
curl http://localhost:8000/api/apps/sales-followup-agent
curl -X POST http://localhost:8000/api/apps/sales-followup-agent/interaction-policy/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"signal":"followup_tone_needed"}'
curl -X POST http://localhost:8000/api/conversations \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"sales-followup-agent","workspace_id":"workspace-id","channel":"web"}'
curl -X POST http://localhost:8000/api/conversations/session-id/messages \
  -H 'Content-Type: application/json' \
  -d '{"content":"Draft a customer-friendly follow-up.","attachments":[]}'
curl -X POST http://localhost:8000/api/interactions \
  -H 'Content-Type: application/json' \
  -d '{"workspace_id":"workspace-id","session_id":"session-id","event_type":"sales.open_full_review","payload":{"action":"open_full_review"}}'
```
