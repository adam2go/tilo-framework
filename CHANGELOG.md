# Changelog

All notable changes to Tilo Framework are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- **`generate_batch(goals, …)`** — generate many surfaces concurrently (thread
  pool; N goals finish in ~the slowest one's time). Order preserved; per-item
  failures yield a fallback instead of aborting the batch.

### Changed
- Removed internal V1.0 build-process docs from `docs/` (history is in git +
  the CHANGELOG); dropped the stale "Active Refactor" framing in the docs index.
- Stopped tracking the `frontend/tsconfig.tsbuildinfo` build cache.

---

## [0.3.0] — 2026-06-05

### Added — robustness, providers, ergonomics
- **`base_url`** on `generate()` — use any OpenAI-compatible provider (DeepSeek,
  Groq, OpenRouter, Together, or a local Ollama/vLLM server) with one line.
- **`tilo generate "goal"` CLI** — generate a surface straight from the shell
  (`--model`, `--base-url`, `--skill`, `--document`, `--json`, `--html`, `--save`).
- **`generate_followup(prev, question)`** — multi-turn surfaces that build on a
  previous result (act on `follow_ups`).
- **JSON repair retry** — on unparseable/invalid model output, ask the model
  once to fix it before falling back (`repair=True` default; opt out per call).
- **`temperature`** and **`strict`** parameters on `generate()` and providers.
- **Actionable errors** — missing API key / SDK now raises a clear
  `TiloGenerationError` / `ImportError` with the exact fix.
- **`save_spec()` / `load_spec()`** — round-trip a spec to JSON.

### Changed — performance
- `tilo.schemas` is now a lazy package (PEP 562): the lightweight
  `import tilo` → `generate` → `ArtifactSpecV1` path no longer loads the
  54-model `domain` schema layer (+ service constants). Server code is
  unaffected (deferred to first use).

### Fixed
- `AIPPromptBuilder.parse()` handles trailing prose after the JSON object.

---

## [0.2.0] — 2026-06-05

The "one line to an interactive surface" release. `pip install tilo` is now
lighter (psycopg is optional), and ships the full generate → view experience.

### Added — one-line LLM → interactive UI
- **`tilo.generate(goal, model=…)`** — one line from any LLM to a full AIP spec;
  provider auto-detected from the model name (gpt-* → OpenAI, claude-* → Anthropic).
  The LLM authors the full surface (chart, diff, confirmation, memory_card, …),
  not just a wrapped response.
- **`tilo.prompt.AIPPromptBuilder`** — bring-your-own LLM client. `system_prompt()`,
  `user_prompt()`, `messages_openai/anthropic/langchain()`, and `parse()` (validates
  + normalises raw LLM output into an AIP spec).
- **12 built-in skills** (was 4): + incident_response, meeting_summary, bug_report,
  document_review, research_summary, onboarding_plan. `from_skill_file()` loads
  custom `skill.yaml`.
- **`generate_aip_spec()`** added to the OpenAI, Anthropic, and LangChain adapters.

### Added — zero-setup rendering
- **`tilo.view(spec)`** — opens a rendered surface in the browser (temp HTTP server).
- **`tilo.notebook(spec)`** — inline rendering in Jupyter / Colab.
- **`tilo.to_html(spec)` / `tilo.save_html(spec)`** — self-contained HTML, no CDN,
  no framework. Pure-JS renderer for all 20 block types incl. SVG charts.
- **`tilo serve` welcome page** at `/` + live **`/playground`** spec editor.
- **`tilo demo`** — opens a sample surface instantly.

### Added — adapters & examples
- **OpenAI adapter** (`tilo.adapters.openai`) — `tilo_spec_from_completion()` + `TiloCompletionHandler` for streaming; auto-maps text/JSON/tool_calls to typed AIP blocks
- **Anthropic adapter** (`tilo.adapters.anthropic_sdk`) — `tilo_spec_from_message()` + `TiloMessageHandler`; handles text, tool_use, and streaming via `on_text()` / `on_event()`
- **A2A adapter** (`tilo.adapters.a2a`) — `a2a_task_to_spec()`: A2A Task artifacts/parts → AIP blocks
- **ACP adapter** (`tilo.adapters.acp`) — `acp_message_to_spec()`: ACP MessageParts → AIP blocks
- **`generate_aip_spec()`** on the OpenAI / Anthropic / LangChain adapters
- **`tilo init` overhaul** — scaffolds a `generate()`+`view()` `hello.py`, plus `server_demo.py` for the full ROAM loop
- **`examples/integrations/`** — copy-paste ready examples (quickstart, OpenAI, Anthropic, LangChain) + a Colab notebook
- **5-minute quickstart tutorial** (`docs/tutorials/quickstart.md`) + **`docs/GENERATE.md`** reference
- **Live playground generation** — `POST /api/playground/generate` (uses the backend's configured LLM)
- GitHub issue templates, PR template, CI badge, comparison table vs LangGraph / CrewAI / AutoGPT

### Changed
- **Lighter install**: `psycopg` moved to an optional `[postgres]` extra (SQLite is the default). Added `[openai]`, `[anthropic]`, `[langchain]`, `[all]` extras.
- README now leads with the one-line `generate → view` experience and a hero screenshot.

### Fixed
- `AIPPromptBuilder.parse()` handles trailing prose after the JSON object (a common LLM pattern)
- Skill detection: `" pr"` no longer misfires on words like "production" (word-boundary match)
- Frontend `pnpm-lock.yaml` synced with the `recharts` dependency (CI `--frozen-lockfile`)

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
