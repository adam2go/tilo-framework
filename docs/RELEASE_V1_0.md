# Tilo v1.0 Release Notes

v1.0 is the framework release for Tilo's AI-native product runtime.

Tilo is a framework for SaaS agents that can render focused interfaces, observe human decisions, act through backend-owned semantics, and memorize only confirmed learning. It is not a traditional SaaS admin console with an AI sidebar.

## Stable in v1.0

- Minimal public demo at `http://localhost:3000/demo`.
- Contract Review flow through the ROAM loop: goal -> conversation message -> task/run -> artifact -> artifact action -> observation -> memory candidate -> human confirmation.
- `artifact_spec.v1` as the renderable artifact contract.
- Backend-owned Artifact Action Runtime at `POST /api/artifacts/{artifact_id}/actions/{action_id}`.
- Conversation sessions, turns, rich surface links, and observation turns.
- Interaction policy and app manifest loading for declarative example apps.
- Deterministic local mode with no API key required.
- Memory candidates that remain unconfirmed until a user confirms them.

## Experimental

- LLM-backed contract generation when configured through backend environment variables.
- Telegram-like demo at `/demo/telegram`, retained for compatibility and deeper internal inspection.
- Skill candidate promotion and evaluation scaffolding.
- Tool invocation beyond mock/local tools.
- Rich surface patterns beyond the focused Contract Review demo.

## Quick Start

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:3000/demo
```

The primary demo should be minimal by default. Runtime details are available through `Why this UI?`, `View trace`, and `Developer mode`.

## Developer Path

Create and validate a new app:

```bash
python scripts/create_app.py my-agent
python scripts/validate_app.py examples/apps/my-agent
```

Then inspect:

- `examples/apps/my-agent/app.yaml`
- `examples/apps/my-agent/interaction.policy.yaml`
- `docs/APP_MANIFEST.md`
- `docs/INTERACTION_POLICY.md`
- `docs/ARTIFACT_ACTION_RUNTIME.md`

## Known Limitations

- Authentication, multi-tenant authorization, and production RBAC are not implemented.
- External side effects are intentionally limited; high-risk actions require confirmation or remain mock/experimental.
- The public demo is intentionally focused on Contract Review. Sales Follow-up and Competitive Analysis remain framework examples, not polished public demos.
- Developer drawers expose concise runtime summaries, not a full production observability console.
- Docker/local verification depends on local environment availability.

## Roadmap After v1.0

- Broaden channel adapters while preserving backend-owned action semantics.
- Harden permissions, audit trails, and production deployment guidance.
- Expand app scaffolding and validation without creating a marketplace prematurely.
- Improve artifact editing and versioning flows.
- Add more realistic tool integrations behind explicit confirmation gates.
