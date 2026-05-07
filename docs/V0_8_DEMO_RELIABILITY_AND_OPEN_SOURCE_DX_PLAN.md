# Tilo v0.8: Demo Reliability and Open-source Developer Experience Plan

v0.8 is the next implementation milestone after the ROAM runtime, conversation runtime, ORID reflection, and README cleanup work.

This version should not add a large new product surface. It should make Tilo credible as an open-source project:

```text
A new developer can clone it, run it, understand it, test it, and build a small app.
```

The priority is reliability, clarity, and public demo quality.

---

## 1. Why v0.8

Tilo now has strong ideas and many runtime primitives:

- ROAM Loop: Render -> Observe -> Act -> Memorize
- Agent App Manifest
- Interaction Policy
- Mini / Rich Surfaces
- ConversationSession / ConversationTurn
- UIInteractionEvent
- AgentContextBuilder / PromptBuilder
- ORID Context Reflection
- Memory Candidate lifecycle
- Telegram-like demo route
- Declarative example apps

The project now needs to feel less like an internal prototype and more like a maintainable open-source framework.

v0.8 should answer four questions:

1. Can the demo reliably run from README instructions?
2. Can tests verify the core runtime loop?
3. Can a developer understand the docs without reading old milestone plans?
4. Can someone build a small app from examples without reverse-engineering the code?

---

## 2. Product Principle

Keep the existing principle:

```text
Agent by default. UI when necessary.
```

For v0.8 add a project principle:

```text
Demo credibility beats feature breadth.
```

One reliable, polished contract-review flow is better than five half-working demos.

---

## 3. v0.8 Goals

v0.8 has five goals:

1. Make `/demo/telegram` reliable and public-demo ready.
2. Add a first-run validation path for contributors.
3. Strengthen tests around the ROAM runtime loop.
4. Clean and stabilize docs as a contributor documentation center.
5. Improve app-developer DX for creating and validating a new Tilo app.

---

## 4. P0: Verify and Harden Quick Start

### 4.1 Required behavior

The README quick start should work:

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env

docker compose up --build
```

Then:

```text
http://localhost:3000/demo/telegram
curl http://localhost:8000/api/health
```

### 4.2 Add verification script

Add a script:

```text
scripts/verify_local_demo.sh
```

It should check:

- Docker Compose can start services, or clearly explain if Docker is unavailable.
- Backend health endpoint returns ok.
- Frontend route `/demo/telegram` returns a successful response.
- App manifest API returns example apps.
- Conversation API can create a session.
- Conversation-native message endpoint works if implemented.

Suggested behavior:

```bash
bash scripts/verify_local_demo.sh
```

Output should be human-readable:

```text
✓ backend health ok
✓ frontend demo route ok
✓ example apps loaded
✓ conversation session created
✓ demo verification complete
```

If a check fails, print a clear next step.

### 4.3 Acceptance criteria

- README points to the verification script.
- Script is safe to run locally.
- Script does not require an API key.
- Script supports deterministic mode.
- Failures are actionable.

---

## 5. P0: Public Demo Reliability

### 5.1 `/demo/telegram` must work without an API key

Required:

- deterministic mode works by default;
- demo shows a small mode badge;
- no broken empty states;
- no uncaught frontend error when backend is unavailable;
- no raw JSON in normal user flow.

### 5.2 Stable demo path

The default demo should be Contract Review.

Required path:

```text
Start -> Risk Review -> Approve Revision -> Revision Draft -> Memory Candidate
```

Each stage should have:

- visible chat update;
- center surface update;
- durable event or safe fallback;
- inspector update if available.

### 5.3 Reset and replay behavior

Required:

- `Reset Demo` creates a new conversation session or clearly resets local demo state.
- `Replay Demo` should follow a deterministic scripted path.
- Reload with `session_id` should restore backend turns when available.

### 5.4 Acceptance criteria

- A first-time visitor can understand the demo in 10 seconds.
- Demo path works without LLM.
- If backend call fails, user sees a helpful message instead of broken UI.
- Reset and replay do not corrupt persisted conversation history.

---

## 6. P0: Runtime Loop Tests

Add or harden tests for the real differentiator:

```text
UI action -> observation -> context -> memory candidate
```

Required backend tests:

1. Conversation session creation.
2. Conversation-native message appends user and agent turns.
3. UIInteractionEvent with session id appends observation turn.
4. AgentContextBuilder includes recent conversation turns and observations.
5. PromptBuilder receives recent conversation turns in runtime execution.
6. ORID reflection returns objective/reflective/interpretive/decisional sections.
7. Reflection-created memory candidate includes `why` and `orid_evidence`.
8. Memory candidate is not confirmed until user confirms.
9. Telegram callback still appends observation turn where session exists.
10. Example app manifest/policy validation still works.

### Acceptance criteria

- `pytest` passes for backend tests.
- Tests do not require external LLM calls.
- Tests cover deterministic mode.
- Tests fail if the ROAM context loop is silently broken.

---

## 7. P1: Developer Docs Center

### 7.1 Docs index

Keep `docs/README.md` as the documentation entry point.

It should contain only:

- Start Here
- Core Concepts
- Runtime References
- Engineering Rules
- Active Plan
- History

### 7.2 Remove or archive outdated docs

Avoid top-level docs like:

```text
V0_2_...
V0_4_...
old demo requirements
old one-off Codex prompts
```

If still useful, summarize them in:

```text
docs/IMPLEMENTATION_HISTORY.md
```

### 7.3 README consistency

README and Chinese README should match in structure:

1. Project positioning
2. Quick Start
3. What You Can Build
4. How It Works
5. Build an Agent App
6. Current Capabilities
7. Roadmap
8. Docs / Contributing

### 7.4 Acceptance criteria

- `docs/README.md` links only to existing files.
- README links only to existing files.
- Chinese README has no outdated v0.2/v0.3 language.
- Active plan is clearly v0.8.

---

## 8. P1: App Developer Experience

### 8.1 App scaffold validation

`scripts/create_app.py my-agent` should generate a minimal app that can load successfully.

Add a validation script:

```text
scripts/validate_app.py examples/apps/my-agent
```

It should check:

- `app.yaml` exists;
- `interaction.policy.yaml` exists;
- policy surfaces are declared in manifest;
- sample fixture paths are safe;
- no secrets are present;
- required fields exist.

### 8.2 Add app validation API or CLI helper

Minimum acceptable implementation is a script. API endpoint is optional.

Preferred script behavior:

```bash
python scripts/validate_app.py examples/apps/contract-review-agent
python scripts/validate_app.py examples/apps/sales-followup-agent
```

Output:

```text
✓ manifest loaded
✓ policy loaded
✓ policy surfaces declared
✓ sample paths safe
✓ app validation passed
```

### 8.3 Improve Build Your First Tilo App doc

Update `docs/BUILD_YOUR_FIRST_TILO_APP.md` to include:

- scaffold command;
- validate command;
- app API check;
- policy evaluation check;
- expected files;
- common errors.

### Acceptance criteria

- New app scaffold can be validated.
- Both existing example apps pass validation.
- Docs show the full loop: create -> validate -> run -> inspect.

---

## 9. P1: Demo Assets and README Trust

Do not add fake screenshots.

If screenshots are added, they must reflect current UI.

### Required improvements

- Keep `docs/assets/tilo-framework-overview.svg` as the project overview image.
- Add a placeholder note in README only if real screenshot is not available.
- Optionally add a script or doc section describing how to capture a screenshot after running the demo.

Suggested doc:

```text
docs/DEMO_SCREENSHOTS.md
```

It can describe:

- run local demo;
- open `/demo/telegram`;
- run contract review demo;
- capture screenshot;
- save as `docs/assets/telegram-demo.png`.

### Acceptance criteria

- No fake screenshots are committed.
- README image does not misrepresent functionality.
- If screenshot doc exists, it is honest and reproducible.

---

## 10. P2: Frontend Polish Without Scope Creep

Only do small, high-impact frontend reliability polish.

Allowed:

- loading states;
- empty states;
- error banners;
- mode badge;
- reset/replay clarity;
- mobile-ish graceful fallback if easy;
- reduced inspector noise.

Not allowed in v0.8:

- full UI redesign;
- full artifact editor;
- full workflow builder;
- new dashboard;
- new large app scenario.

Acceptance criteria:

- Demo feels stable.
- Error states are understandable.
- Inspector explains rather than overwhelms.
- No new large UI surface is introduced.

---

## 11. P2: Lightweight CI

Add GitHub Actions only if missing.

Suggested workflow:

```text
.github/workflows/ci.yml
```

Jobs:

- backend tests;
- frontend build;
- app manifest validation.

Constraints:

- no external API key required;
- deterministic mode only;
- keep runtime short.

Acceptance criteria:

- CI can run on pull requests.
- CI does not need secrets.
- CI catches broken backend tests and frontend build issues.

---

## 12. Non-goals

Do not do these in v0.8:

- add a new agent app category;
- build full Slack/Discord/WeChat adapters;
- build production auth;
- build deployment platform;
- build full model gateway;
- build advanced memory ranking;
- redesign the whole frontend;
- create fake launch screenshots.

---

## 13. Testing Commands

Codex should try to run:

```bash
python -m pytest backend/tests
```

If frontend dependencies are available:

```bash
cd frontend
pnpm install
pnpm build
```

If Docker is available:

```bash
docker compose up --build
bash scripts/verify_local_demo.sh
```

If a command cannot run because the environment lacks Docker, network, pnpm, or dependencies, report that honestly.

---

## 14. Definition of Done

v0.8 is complete when:

1. README quick start is verified or has a clear verification script.
2. `/demo/telegram` works without an API key.
3. Demo reset/replay behavior is reliable.
4. Backend tests cover the ROAM runtime loop.
5. Docs folder has a clear index and fewer stale milestone docs.
6. App scaffold and validation workflow are documented.
7. Example apps validate successfully.
8. No fake screenshot or misleading README asset is added.
9. CI exists or the reason for not adding it is documented.
10. Codex final summary includes commands run, results, and limitations.
