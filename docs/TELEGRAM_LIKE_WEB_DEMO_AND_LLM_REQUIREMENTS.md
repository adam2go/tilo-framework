# Telegram-like Web Demo and LLM Integration Requirements

This document defines the next critical demo milestone for Tilo.

The goal is to build a public-facing demo that proves Tilo's product idea in one flow:

```text
Chat-like entry -> Dynamic ROAM Surface -> Developer Inspector -> LLM-powered artifact generation
```

This demo is important for open-source adoption. It must be understandable, attractive, and technically real enough to prove the framework direction.

---

## 1. Current Implementation Findings

Before implementing this milestone, note the current state of the repository.

### 1.1 Environment variables already exist

`.env.example` already includes OpenAI-compatible model configuration:

```text
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4.1-mini
DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
```

It also includes Telegram-related configuration:

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
TELEGRAM_WEBHOOK_URL=
PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 1.2 Backend settings already expose model fields

`backend/app/core/config.py` already defines:

```python
openai_api_key: str = ""
openai_base_url: str = "https://api.openai.com/v1"
default_model: str = "gpt-4.1-mini"
default_embedding_model: str = "text-embedding-3-small"
```

### 1.3 Real LLM execution is not implemented yet

There is currently no real LLM client or model gateway service.

The current runtime is mostly rule-based:

- `Planner` builds a lightweight rule-based plan.
- `ArtifactTypeDetector` detects artifact type by keyword.
- `ArtifactSpecBuilder` generates demo artifact specs with hardcoded structures.
- `RunManager` executes a full loop, but it does not call a model provider.

This is acceptable for early scaffolding, but not enough for the public demo.

### 1.4 Frontend already has a ROAM landing and workspace foundation

The current frontend already has:

- landing page
- `/workspace` route
- `Console` component
- showcase/developer mode concept
- dynamic staged surface concept
- interaction events
- artifact rendering

The next step is not to start from scratch. The next step is to create a polished Telegram-like web demo and connect it to real or mockable model generation.

---

## 2. Product Goal

Build a **Telegram-like Web Demo**.

This does not mean copying Telegram exactly.

The page should feel familiar like a messaging product, but it should be more powerful because it is for developers evaluating Tilo.

Recommended concept:

```text
Left: Chat-like User Entry
Center: Dynamic ROAM Surface
Right: Developer Inspector
```

The demo should show:

1. A user starts from a chat-like interface.
2. Tilo receives the goal.
3. Tilo calls the LLM/runtime.
4. Tilo renders a dynamic artifact surface.
5. User interaction becomes durable observation.
6. Developer can inspect interaction contract, surface routing, events, and memory.

---

## 3. Demo Positioning

Use this public message:

```text
Chat is the entry. Surface is the workspace. Interaction becomes memory.
```

Do not present the demo as only:

```text
Telegram bot clone
```

It is:

```text
A Telegram-like developer demo for AI-native SaaS agents.
```

The left side looks familiar to anyone who understands Telegram-style chat.

The center and right side show what Tilo adds beyond Telegram:

- generated rich surface
- interaction contract
- durable observations
- memory governance
- artifact links
- channel-to-surface routing

---

## 4. Required Page

Create a dedicated route:

```text
/demo/telegram
```

If current routing structure makes this difficult, an acceptable alternative is:

```text
/workspace?mode=telegram-demo
```

But `/demo/telegram` is preferred because this is a public showcase.

---

## 5. Layout Requirements

The page should use a three-zone layout.

```text
┌───────────────────────────────────────────────────────────────┐
│ Header: Tilo Telegram-like Demo · ROAM Loop · GitHub · Docs    │
├─────────────────┬─────────────────────────────┬───────────────┤
│ Chat Simulator  │ Dynamic ROAM Surface         │ Dev Inspector │
│                 │                             │               │
│ Bot messages    │ Contract Review Surface      │ Contract      │
│ User messages   │ Active decision              │ Routing       │
│ Buttons         │ Rich components              │ Events        │
│ Composer        │ Artifact preview             │ Memory        │
└─────────────────┴─────────────────────────────┴───────────────┘
```

### 5.1 Left zone: Chat-like User Entry

This zone should look Telegram-like:

- rounded phone/chat panel
- blue bot header
- chat bubbles
- inline buttons
- compact composer
- bot status

But it should not be a full Telegram clone.

Required content:

1. Bot welcome message:

```text
Welcome to Tilo. Send me a goal, or run a demo.
```

2. Demo button:

```text
Run Contract Review Demo
```

3. User goal bubble:

```text
Review this contract for payment, liability, and termination risks.
```

4. Bot response:

```text
Contract Review is ready. 3 high-risk clauses found.
```

5. Inline actions:

```text
Open Review Surface
Approve Revision
Not now
```

These buttons should map to Tilo actions/events where possible.

### 5.2 Center zone: Dynamic ROAM Surface

This is the hero area.

It should not look like a traditional dashboard.

It should show one active generated surface at a time.

Recommended stage flow:

```text
Intent -> Contract Intake -> Risk Review -> Approval -> Revision Draft -> Memory
```

For this Telegram-like demo, center should default to:

```text
Contract Review Surface
```

Required elements:

- ROAM stage strip: Render / Observe / Act / Memorize
- Contract Review Surface header
- Risk Summary
- Primary Decision
- Focused Risk Nodes
- Revision Draft Preview after approval
- Memory Candidate after revision

### 5.3 Right zone: Developer Inspector

This is what makes the demo developer-facing.

Required tabs or cards:

1. Interaction Contract
2. Channel -> Surface Routing
3. Durable Observations
4. Memory
5. Debug / Raw optional collapsed section

Required examples:

```text
when: risk.detected
condition: risk_level == high
render: RiskReviewPanel
observe: approve_revision
act: generate_revised_clause
memorize: user_preference
```

Channel routing example:

```text
ApprovalCard -> Telegram buttons
RiskReviewPanel -> Open rich surface
EditableDocument -> Open artifact page
MemoryCandidate -> Chat or surface
```

Durable observations example:

```text
channel.message.received
artifact.action.clicked
confirmation.approved
memory.candidate.proposed
```

---

## 6. Visual Requirements

The demo should be polished enough for README screenshots and a launch video.

Target feeling:

```text
Telegram familiarity + Vercel polish + Linear clarity + developer-console precision
```

Use:

- light background
- clean cards
- strong center focus
- subtle borders
- compact typography
- Telegram-like blue only in left chat area
- indigo/violet for Tilo/ROAM intelligence
- red/amber/green semantic badges

Avoid:

- traditional admin dashboard density
- full left navigation sidebar
- always-visible debug panels
- raw JSON in normal view
- too many cards visible at once
- generic Tailwind starter look

---

## 7. Interaction Requirements

### 7.1 Run demo button

When user clicks `Run Contract Review Demo`:

1. Show user goal bubble.
2. Trigger Tilo message/task flow.
3. Show bot loading message.
4. Render Contract Review Surface in the center.
5. Show developer inspector events.

### 7.2 Open Review Surface

This should focus/activate the center surface.

If an artifact exists, link to:

```text
/artifacts/{artifact_id}?channel=telegram-demo
```

If artifact page route is not ready, keep user inside `/demo/telegram` and show a visible rich surface.

### 7.3 Approve Revision

When user clicks `Approve Revision` from the chat-like panel or center ApprovalCard:

1. Persist `UIInteractionEvent`.
2. Approve linked `Confirmation` if available.
3. Move center stage to `Revision Draft`.
4. Add observation to inspector.
5. Show bot response:

```text
Approved. Tilo is generating a conservative revision draft.
```

### 7.4 Remember Preference

When user confirms memory:

1. Persist `UIInteractionEvent`.
2. Create or confirm Memory candidate.
3. Show memory in inspector.
4. Show bot response:

```text
Remembered. Future contract reviews will use this preference.
```

---

## 8. LLM Integration Requirements

The demo must support real LLM-powered generation, but it must still run without an API key.

### 8.1 Add Model Gateway / LLM Client

Add backend module:

```text
backend/app/services/models/
  client.py
  schemas.py
  prompts.py
  errors.py
```

Recommended interface:

```python
class ModelClient:
    def __init__(self, settings: Settings):
        ...

    async def chat_json(
        self,
        *,
        system: str,
        user: str,
        schema_name: str,
        temperature: float = 0.2,
    ) -> dict:
        ...

    async def chat_text(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
    ) -> str:
        ...
```

Use OpenAI-compatible Chat Completions API:

```text
POST {OPENAI_BASE_URL}/chat/completions
Authorization: Bearer {OPENAI_API_KEY}
```

Do not hardcode OpenAI only. The base URL and model should come from env settings.

This allows users to connect:

- OpenAI
- OpenAI-compatible gateways
- KeyHub
- NewAPI
- local OpenAI-compatible servers
- other compatible providers

### 8.2 Environment variables

Ensure `.env.example` includes:

```text
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4.1-mini
DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
LLM_ENABLED=false
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=2
```

`LLM_ENABLED=false` should keep the demo stable in local environments without a key.

### 8.3 Dependency

Add one of these options:

Option A: use `httpx`

```text
httpx>=0.27
```

Option B: use OpenAI SDK

```text
openai>=1.0
```

Recommendation: use `httpx` first for lightweight OpenAI-compatible calls.

### 8.4 Demo fallback behavior

If `LLM_ENABLED=false` or `OPENAI_API_KEY` is empty:

- use deterministic demo artifact generation
- show a small non-intrusive badge:

```text
Demo mode: deterministic artifact generation
```

If `LLM_ENABLED=true` and key exists:

- use model client to generate or refine artifact data
- show badge:

```text
LLM mode: {DEFAULT_MODEL}
```

### 8.5 Where to integrate LLM

Do not rewrite everything.

Integrate LLM in these places:

1. `Planner`
   - optional LLM plan generation
   - fallback to current rule-based plan

2. `ArtifactSpecBuilder`
   - use LLM to generate realistic contract risks, revision suggestions, summaries, and memory candidates
   - validate output against `ArtifactSpecV1`
   - fallback to current deterministic spec when invalid or unavailable

3. `MemoryExtractionService`
   - optionally use LLM to propose memory candidates
   - never auto-confirm them

4. `SkillCandidate` generation later
   - not required for this demo milestone

Recommended first step:

```text
Only add LLM enhancement to Contract Review artifact generation.
```

Keep Sales and Competitive demos deterministic for now.

### 8.6 Prompt requirements

Contract review LLM prompt should return JSON only.

Expected shape:

```json
{
  "risk_summary": {
    "high_count": 3,
    "medium_count": 2,
    "low_count": 1,
    "summary": "..."
  },
  "risks": [
    {
      "id": "risk_1",
      "clause": "Payment terms",
      "risk_level": "high",
      "issue": "...",
      "suggested_revision": "...",
      "evidence": "..."
    }
  ],
  "revision_draft": {
    "heading": "Conservative revision draft",
    "content": "...",
    "highlights": []
  },
  "memory_candidate": {
    "type": "user_preference",
    "content": "...",
    "confidence": 0.7
  }
}
```

Then convert this model output into `ArtifactSpecV1` blocks.

### 8.7 LLM safety requirements

- Never expose API keys in frontend.
- Never log API keys.
- Never store raw hidden reasoning.
- Treat model output as untrusted.
- Validate and normalize JSON before persistence.
- If model output is invalid, fallback to deterministic artifact.
- Keep trace output safe and concise.

### 8.8 Trace requirements

When LLM is used, trace should show:

```text
LLM generation requested
model: DEFAULT_MODEL
mode: json
status: success/fallback/failed
```

Do not log full prompt by default.

Do not log secrets.

---

## 9. Backend Implementation Plan

### Phase 1: Model gateway foundation

Implement:

1. Add model config fields:
   - `llm_enabled`
   - `llm_timeout_seconds`
   - `llm_max_retries`

2. Add `httpx` dependency.

3. Add `ModelClient`.

4. Add safe errors:
   - missing key
   - timeout
   - invalid JSON
   - provider error

5. Add unit tests for:
   - disabled mode
   - missing key fallback
   - invalid JSON fallback

### Phase 2: Contract Review LLM enhancement

Implement:

1. Add `ContractReviewLLMGenerator`.
2. Use LLM only when enabled.
3. Build prompt from:
   - user task
   - recalled memories
   - tool outputs if any
4. Parse JSON output.
5. Convert to `ArtifactSpecV1` blocks.
6. Validate artifact spec.
7. Fallback to deterministic current spec on error.

### Phase 3: Frontend mode indicators

Implement:

1. Add mode badge in demo:
   - `Demo mode`
   - `LLM mode: model_name`
2. Optional backend endpoint:

```text
GET /api/runtime/capabilities
```

Return:

```json
{
  "llm_enabled": false,
  "default_model": "gpt-4.1-mini",
  "telegram_enabled": false
}
```

---

## 10. Frontend Implementation Plan

### Phase 1: Telegram-like route

Implement route:

```text
/demo/telegram
```

Build components:

```text
frontend/components/demo-telegram/
  TelegramDemoPage.tsx
  ChatSimulator.tsx
  ChatBubble.tsx
  BotInlineActions.tsx
  RichSurfacePreview.tsx
  DeveloperInspector.tsx
  ContractSnippetCard.tsx
```

### Phase 2: Chat simulator

The left panel should simulate a Telegram-like flow.

It should include:

- bot welcome
- run demo action
- user goal bubble
- bot status messages
- inline action buttons
- compact composer

### Phase 3: Rich surface preview

The center should reuse existing interaction components where possible:

- RiskSummary
- RiskReviewPanel
- ApprovalCard
- EditableDocumentPreview
- MemoryCandidateCard
- ActionQueue

Do not duplicate business logic if existing components already render these blocks.

### Phase 4: Developer inspector

Right panel should show:

- Interaction Contract
- Channel routing
- Durable observations
- Memory candidate
- Runtime mode

### Phase 5: Connect to backend

Reuse existing APIs:

- `/api/messages`
- `/api/artifacts`
- `/api/interactions`
- `/api/confirmations`
- `/api/memories`

If Telegram adapter code exists, do not require real Telegram bot token for this web demo.

This is a web simulation of Telegram-like entry, not necessarily a live Telegram bot page.

---

## 11. Acceptance Criteria

This milestone is done when:

### Demo UX

1. `/demo/telegram` exists.
2. The page visually resembles a Telegram-like chat entry, but clearly shows Tilo's richer developer capabilities.
3. User can click `Run Contract Review Demo`.
4. Left chat simulator updates with user/bot messages.
5. Center rich surface renders Contract Review workflow.
6. Right inspector shows interaction contract, routing, observations, and memory.
7. The page is good enough for README screenshots.

### Runtime

8. Demo can run without `OPENAI_API_KEY` using deterministic mode.
9. Demo can use LLM mode when `LLM_ENABLED=true` and `OPENAI_API_KEY` exists.
10. LLM output is validated and fallback-safe.
11. API keys never touch frontend.
12. Trace records LLM mode without exposing full prompt/secrets.

### Integration

13. Existing `/workspace` demo is not broken.
14. Existing Telegram adapter work is not broken.
15. Existing Artifact rendering is reused where possible.
16. Important interactions persist durable `UIInteractionEvent`, `Confirmation`, or `Memory` state where supported.

---

## 12. Suggested Codex Prompt

```text
Read docs/TELEGRAM_LIKE_WEB_DEMO_AND_LLM_REQUIREMENTS.md first.

Implement the Telegram-like Web Demo and LLM integration foundation.

This demo is critical for Tilo's public showcase.

Do not build a Telegram clone.
Build a Telegram-like developer demo:
- left: chat-like user entry
- center: Rich ROAM Surface
- right: Developer Inspector

Also implement the missing LLM integration foundation.
The current config has OPENAI_API_KEY/OPENAI_BASE_URL/DEFAULT_MODEL, but there is no real model client yet.

Implement in this order:
1. Add model runtime config: LLM_ENABLED, LLM_TIMEOUT_SECONDS, LLM_MAX_RETRIES.
2. Add lightweight OpenAI-compatible ModelClient using httpx.
3. Add fallback-safe Contract Review LLM generator.
4. Integrate LLM enhancement into Contract Review artifact generation only.
5. Add /api/runtime/capabilities endpoint.
6. Create /demo/telegram page with Telegram-like Web Demo layout.
7. Reuse existing ROAM interaction components in the rich surface.
8. Add Developer Inspector showing Interaction Contract, Channel Routing, Durable Observations, Runtime Mode.
9. Ensure demo works without API key in deterministic mode.
10. Ensure demo uses LLM mode when configured.
11. Add basic tests for model client disabled/fallback behavior and demo route if possible.

Preserve existing web workspace and Telegram adapter behavior.
Never expose API keys in frontend.
Do not log secrets or hidden model reasoning.
```

---

## 13. Summary

The demo should communicate this instantly:

```text
Tilo starts from chat-like entry,
opens a rich AI-native SaaS surface,
records user interaction as observation,
and uses model + memory to improve future work.
```

This is more important than showing every feature.

One polished Contract Review flow is better than three unfinished demos.
