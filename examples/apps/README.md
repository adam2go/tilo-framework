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

To add another app:

1. Create `examples/apps/{app_id}/app.yaml`.
2. Create `examples/apps/{app_id}/interaction.policy.yaml`.
3. Keep sample inputs inside the app directory, or under `examples/contracts` for shared contract fixtures.
4. Add only the mini surfaces needed for meaningful human decisions.
5. Verify the app appears in `GET /api/apps`.

Do not put secrets in manifests or policies.

The sales follow-up app includes minimal fixture data at:

```text
examples/apps/sales-followup-agent/fixtures/lead-summary.md
```

It is intentionally small so the same app runtime can be tested without becoming a second custom demo.
