# Tilo v0.8 Codex Execution Prompt

Use this prompt when asking Codex to implement v0.8.

```text
We are continuing development of Tilo Framework v0.8.

Repository:
adam2go/tilo-framework

First read:
- README.md
- README.zh-CN.md
- docs/README.md
- docs/V0_8_DEMO_RELIABILITY_AND_OPEN_SOURCE_DX_PLAN.md
- docs/ROAM_LOOP.md
- docs/CONVERSATION_RUNTIME.md
- docs/ORID_CONTEXT_REFLECTION.md
- docs/MEMORY.md
- docs/BUILD_YOUR_FIRST_TILO_APP.md
- docs/QUALITY_BAR.md

Goal:
Implement v0.8: Demo Reliability and Open-source Developer Experience.

This is not a big feature release.
This version should make Tilo credible as an open-source project:
A new developer can clone it, run it, understand it, test it, and build a small app.

Core principles:
- Demo credibility beats feature breadth.
- Do not add a new large product surface.
- Do not redesign the whole frontend.
- Do not add a new app category.
- Do not create fake screenshots.
- Preserve deterministic mode.
- Preserve optional LLM mode if already implemented.
- Preserve the ROAM Loop: Render -> Observe -> Act -> Memorize.
- Preserve conversation-first UX.
- Preserve backend interaction policy as source of truth.
- Keep changes small, reliable, and well-tested.

Implement in this order:

1. Verify and harden Quick Start.
   - Confirm README commands are accurate:
     git clone, cp .env.example .env, docker compose up --build.
   - Add scripts/verify_local_demo.sh.
   - The script should check backend health, frontend /demo/telegram route, example app loading, conversation session creation, and conversation-native message endpoint if implemented.
   - Script must not require an API key.
   - Script should print clear pass/fail messages and actionable next steps.

2. Harden /demo/telegram reliability.
   - Ensure deterministic mode works without OPENAI_API_KEY.
   - Add or improve visible runtime mode badge.
   - Ensure no broken empty states.
   - Add helpful frontend error banner if backend is unavailable.
   - Ensure default Contract Review demo path works:
     Start -> Risk Review -> Approve Revision -> Revision Draft -> Memory Candidate.
   - Reset Demo should create a new session or clearly reset local demo state.
   - Replay Demo should follow a deterministic scripted path.
   - Reload with session_id should restore backend turns when available.
   - Do not add a new large UI surface.

3. Strengthen backend tests around the ROAM runtime loop.
   Required tests:
   - Conversation session creation.
   - Conversation-native message appends user and agent turns.
   - UIInteractionEvent with session_id appends observation turn.
   - AgentContextBuilder includes recent conversation turns and observations.
   - PromptBuilder receives recent conversation turns in runtime execution.
   - ORID reflection returns objective, reflective, interpretive, decisional sections.
   - Reflection-created memory candidate includes why and orid_evidence.
   - Memory candidate remains unconfirmed until user confirms.
   - Telegram callback appends observation turn where session exists.
   - Example app manifest/policy validation still works.

4. Stabilize docs as a contributor documentation center.
   - Keep docs/README.md as the docs entry point.
   - Ensure docs/README.md links only to existing files.
   - Ensure README.md and README.zh-CN.md have matching structure:
     Project positioning -> Quick Start -> What You Can Build -> How It Works -> Build an Agent App -> Current Capabilities -> Roadmap -> Docs / Contributing.
   - Remove stale references to old V0_2/V0_3 milestone docs.
   - Do not reintroduce old one-off Codex prompt files.
   - Keep historical context only in docs/IMPLEMENTATION_HISTORY.md.

5. Improve app developer experience.
   - Ensure scripts/create_app.py my-agent still works.
   - Add scripts/validate_app.py.
   - validate_app.py should check:
     app.yaml exists,
     interaction.policy.yaml exists,
     required manifest fields exist,
     policy surfaces are declared in manifest,
     sample fixture paths are safe,
     no obvious secrets are present.
   - Validate existing apps:
     examples/apps/contract-review-agent
     examples/apps/sales-followup-agent
   - Update docs/BUILD_YOUR_FIRST_TILO_APP.md with create -> validate -> run -> inspect flow.

6. Add demo screenshot guidance, not fake screenshots.
   - Do not add fake screenshots.
   - If useful, add docs/DEMO_SCREENSHOTS.md describing how to capture real screenshots after running the demo.
   - Keep docs/assets/tilo-framework-overview.svg as project overview image.

7. Add lightweight CI if missing.
   - Add .github/workflows/ci.yml if no CI exists.
   - Jobs should include backend tests, frontend build if feasible, and app manifest validation.
   - CI must not require external API keys or secrets.
   - Keep CI deterministic and reasonably fast.

8. Run tests and report honestly.
   Try:
   - python -m pytest backend/tests
   - cd frontend && pnpm install && pnpm build, if pnpm/network is available
   - bash scripts/verify_local_demo.sh, if Docker/services are available

If commands cannot run because the environment lacks Docker, network, pnpm, or dependencies, say so clearly in the final summary. Do not claim unverified success.

Definition of Done:
- README quick start is accurate and supported by a verification script.
- /demo/telegram works without an API key.
- Demo reset/replay behavior is reliable.
- Backend tests cover the ROAM runtime loop.
- docs/ has a clear index and fewer stale milestone docs.
- App scaffold and validation workflow are documented.
- Existing example apps validate successfully.
- No fake screenshot or misleading README asset is added.
- CI exists or the reason for not adding it is documented.
- Final summary includes files changed, tests run, results, and known limitations.
```
