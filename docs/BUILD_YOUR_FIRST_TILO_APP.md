# Build Your First Tilo App

Tilo apps are small folders that describe an agent entry point, its allowed surfaces, its interaction policy, and sample inputs.

The fastest path is to copy an existing app:

```bash
cp -R examples/apps/contract-review-agent examples/apps/my-agent
```

Then edit:

```text
examples/apps/my-agent/app.yaml
examples/apps/my-agent/interaction.policy.yaml
```

## 1. Rename The App

In `app.yaml`, set a unique id and name:

```yaml
id: my-agent
name: My Agent
entry:
  type: conversation
  default_prompt: Help me with this task.
```

Keep the entry conversation-first. Do not make users fill out forms before they see value.

## 2. Choose Surfaces

Declare only the mini and rich surfaces your policy may return:

```yaml
surfaces:
  mini:
    - MiniChoiceCard
    - MiniMemoryCard
  rich:
    - MyArtifactSurface
```

Mini surfaces appear inline in the conversation. Rich surfaces are opened intentionally, for example through Open Full Review.

## 3. Add Sample Data

Put app-specific fixtures inside the app folder, or shared fixtures under `examples/fixtures`.

```yaml
sample_inputs:
  - type: fixture
    name: sample
    path: fixtures/sample.json
```

Never put secrets in sample files, manifests, policies, frontend code, or traces.

## 4. Write The Policy

`interaction.policy.yaml` decides when UI should appear:

```yaml
id: my-agent-policy
version: "0.1"
rules:
  - id: choose-next-step
    when:
      signal: next_step_needed
    decision: mini_surface
    surface: MiniChoiceCard
    reason: user_choice_needed
  - id: open-full-artifact
    when:
      user_action: open_full_review
    decision: rich_surface
    surface: MyArtifactSurface
    reason: explicit_escalation
```

The backend validates that policy surfaces are declared in `app.yaml`.

## 5. Try The APIs

Start the backend, then inspect apps:

```bash
curl http://localhost:8000/api/apps
curl http://localhost:8000/api/apps/contract-review-agent
curl http://localhost:8000/api/apps/sales-followup-agent
```

Evaluate a policy:

```bash
curl -X POST http://localhost:8000/api/apps/sales-followup-agent/interaction-policy/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"signal":"followup_tone_needed"}'
```

Create or restore a conversation session:

```bash
curl -X POST http://localhost:8000/api/conversations \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"sales-followup-agent","workspace_id":"workspace-id","channel":"web"}'
```

Append a turn:

```bash
curl -X POST http://localhost:8000/api/conversations/session-id/turns \
  -H 'Content-Type: application/json' \
  -d '{"turn_type":"user_message","role":"user","content":"Draft a concise follow-up."}'
```

Run a conversation-native message:

```bash
curl -X POST http://localhost:8000/api/conversations/session-id/messages \
  -H 'Content-Type: application/json' \
  -d '{"content":"Draft a concise follow-up.","attachments":[]}'
```

Record a UI interaction against the session:

```bash
curl -X POST http://localhost:8000/api/interactions \
  -H 'Content-Type: application/json' \
  -d '{"workspace_id":"workspace-id","session_id":"session-id","event_type":"demo.open_full_review","payload":{"action":"open_full_review"}}'
```

With `session_id`, the backend appends the observation turn and may create an ORID reflection memory candidate. The policy remains the source of truth for UI decisions.

## 6. Optional Scaffold

You can create a minimal app folder with:

```bash
python scripts/create_app.py my-agent
```

Review the generated files before committing them.
