# Changelog

All notable changes to Tilo Framework are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- **OpenAI adapter** (`tilo.adapters.openai`) — `tilo_spec_from_completion()` + `TiloCompletionHandler` for streaming; auto-maps text/JSON/tool_calls to typed AIP blocks
- **Anthropic adapter** (`tilo.adapters.anthropic_sdk`) — `tilo_spec_from_message()` + `TiloMessageHandler`; handles text, tool_use, and streaming via `on_text()` / `on_event()`
- **`tilo init` overhaul** — scaffolds a complete runnable project: `.env`, `requirements.txt`, `hello.py` (end-to-end demo), `openai_agent.py`, and `README.md`
- **`examples/integrations/`** — copy-paste ready examples for OpenAI, Anthropic, and LangChain
- **5-minute quickstart tutorial** (`docs/tutorials/quickstart.md`)
- GitHub issue templates (bug report, feature request)
- GitHub PR template
- CI status badge in README
- Comparison table vs LangGraph / CrewAI / AutoGPT in README

---

## [1.0.0] — 2026-04-25

Initial public release.

### Stable
- Contract Review ROAM flow (end-to-end: goal → artifact → action → memory)
- `ArtifactSpecV1` — renderable artifact contract with typed blocks and actions
- Artifact Action Runtime — `POST /api/artifacts/{id}/actions/{action_id}` with durable `UIInteractionEvent` and `ConversationTurn(observation)`
- Conversation-native architecture — sessions, turns (user_message, agent_message, observation, mini_surface, rich_surface_link, attachment)
- Deterministic local mode — full demo without any API key
- Memory candidate lifecycle — Observation → Candidate → Human Confirmation → Confirmed Memory
- `MemoryRecallPipeline` (hybrid_v0.2) — keyword, salience, recency, scope scoring
- `ModelClient` — multi-provider LLM client (OpenAI-compatible + native Anthropic)
- Sales Follow-up Agent — second declarative example app proving portability
- `app.yaml` + `interaction.policy.yaml` declarative app model
- Baseline eval runner with surface_render_rate, action_completion_rate, memory_acceptance_rate metrics
- Docker Compose full-stack deployment
- CI pipeline (backend tests, frontend build, local demo verification)

### Experimental
- LLM-powered artifact generation (DeepSeek / OpenAI compatible)
- Telegram channel adapter
- Skill candidate promotion

### Not included (future)
- Semantic embeddings for memory recall
- ArtifactSpec core / extension tier split
- Additional example apps
