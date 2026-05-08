# Tilo v1.0 Codex Execution Prompt

Use this prompt when asking Codex to implement v1.0.

```text
We are continuing development of Tilo Framework v1.0.

Repository:
adam2go/tilo-framework

First read:
- README.md
- README.zh-CN.md
- docs/README.md
- docs/AI_NATIVE_FRAMEWORK_PRINCIPLES.md
- docs/DEMO_SIMPLIFICATION_REDESIGN.md
- docs/V1_0_FRAMEWORK_RELEASE_PLAN.md
- docs/ROAM_LOOP.md
- docs/ARTIFACT_ACTION_RUNTIME.md
- docs/ARTIFACTS.md
- docs/CONVERSATION_RUNTIME.md
- docs/ORID_CONTEXT_REFLECTION.md
- docs/MEMORY.md
- docs/BUILD_YOUR_FIRST_TILO_APP.md
- docs/QUALITY_BAR.md

Goal:
Implement Tilo v1.0: Framework Release.

This is not a feature-dump release.
This is not SaaS plus AI features.
Tilo must be implemented as an AI-native product runtime framework.

The goal is to make Tilo feel like a coherent open-source framework with:
- one minimal public demo;
- one clear developer path;
- one stable ROAM runtime contract;
- honest release documentation.

Hard positioning constraints:
- Tilo is a framework for AI-native SaaS agents.
- Tilo is not a SaaS admin console with AI chat added.
- The user experience must be goal-first, not feature-first.
- UI appears only when it helps the user's decision.
- Runtime details are hidden by default and inspectable on demand.
- Backend runtime owns action semantics.
- Frontend renders intent.

Core principles:
- Simple surface. Powerful runtime. Inspectable internals.
- Show the product. Reveal the runtime.
- Do not make the demo look like a traditional SaaS admin dashboard.
- Do not show developer inspector, live events, renderer decisions, model diagnostics, raw traces, or JSON by default.
- Preserve ROAM: Render -> Observe -> Act -> Memorize.
- Preserve deterministic mode without API key.
- Preserve optional LLM mode if configured.
- Preserve /demo/telegram for compatibility or internal debugging.
- Use existing backend APIs where possible.
- Use Artifact Action Runtime for user actions.
- Do not add a new large app scenario before v1.0.
- Do not add fake screenshots.

Implementation review checklist:
- Does this make Tilo more AI-native, or does it recreate traditional SaaS UI?
- Is the user experience goal-first rather than feature-first?
- Does UI appear only when it helps the user's decision?
- Are runtime details hidden by default and inspectable on demand?
- Does backend runtime own action semantics?
- Does the change strengthen ROAM?
- Does memory remain confirmation-based?
- Can another channel reuse the same runtime behavior?

Implement in this order:

1. Add a new minimal public demo route.
   - Add /demo.
   - Keep /demo/telegram available.
   - The new /demo should be the primary public demo.
   - Use a single-column centered layout by default.
   - Do not use the current permanent three-column layout.

2. Build the minimal default demo experience.
   Default page should show:
   - concise product title;
   - one large input box;
   - example chips;
   - minimal helper text.

   Example chips:
   - Review a contract
   - Draft sales follow-up
   - Compare agent frameworks

   For v1.0, only the Contract Review flow needs to be fully polished.
   Other chips can be disabled, coming soon, or route to existing examples honestly.

3. Implement focused Contract Review flow.
   Required flow:
   - user submits contract review goal;
   - create or restore conversation session;
   - call conversation-native message endpoint;
   - display one focused contract review result card;
   - show primary issue and recommended action;
   - user clicks Approve Revision;
   - execute action through Artifact Action Runtime;
   - show revision draft card;
   - show optional memory prompt;
   - user can Remember or Not now.

   The default result view should show only:
   - concise summary;
   - primary issue;
   - short evidence snippet;
   - recommended revision direction;
   - 2-3 clear actions.

4. Hide framework details by default.
   Move these behind explicit drawers or links:
   - Why this UI?
   - View trace
   - Developer mode

   Hidden details can include:
   - interaction policy rule;
   - artifact action endpoint result;
   - UIInteractionEvent;
   - ConversationTurn observation;
   - memory candidate;
   - runtime mode;
   - trace steps.

   Developer mode must not turn the page into a dashboard.
   It should add subtle metadata and open drawers, not permanent side panels.

5. Use existing runtime APIs.
   Use:
   - createConversationSession / getConversationSession;
   - sendConversationMessage;
   - executeArtifactAction;
   - getConversationTurns;
   - artifact read/list APIs;
   - memory APIs;
   - trace APIs;
   - runtime capabilities API.

   Do not duplicate backend business logic in the frontend.

6. Keep deterministic mode stable.
   - /demo must work with no API key.
   - Show a small runtime mode indicator only when useful.
   - If backend is unavailable, show a friendly error state.
   - Do not expose API keys or raw prompts.

7. Preserve and reduce /demo/telegram exposure.
   - Do not break /demo/telegram tests or route.
   - It can remain as a legacy/internal showcase.
   - README should point to /demo after the new demo works.
   - /demo/telegram can be linked as an advanced/legacy demo in docs, not the primary demo.

8. Add end-to-end ROAM contract tests.
   Add or strengthen tests proving:
   - user message creates task/run/artifact;
   - artifact contains executable actions;
   - artifact action runtime executes selected action;
   - UIInteractionEvent is created;
   - ConversationTurn(observation) is appended when session_id exists;
   - ContextReflectionService can propose memory candidate;
   - memory candidate is not confirmed automatically;
   - user confirmation confirms memory;
   - prompt/context path includes recent turns and observations;
   - deterministic mode works without API key.

   At least one test should cover the full contract:
   Conversation message -> artifact -> action runtime -> observation -> memory candidate.

9. Stabilize framework contract docs.
   Update docs so they reflect actual code:
   - APP_MANIFEST.md
   - INTERACTION_POLICY.md
   - ARTIFACTS.md
   - ARTIFACT_ACTION_RUNTIME.md
   - CONVERSATION_RUNTIME.md
   - MEMORY.md
   - API_CONTRACTS.md
   - BUILD_YOUR_FIRST_TILO_APP.md
   - docs/README.md

   Remove stale references to old v0.x plans from main docs.
   Historical details should stay in IMPLEMENTATION_HISTORY.md only.

10. Update developer app path.
   Ensure this flow works and is documented:
   - python scripts/create_app.py my-agent
   - python scripts/validate_app.py examples/apps/my-agent
   - run locally
   - inspect action runtime
   - understand memory candidate lifecycle.

   Do not add new example apps before v1.0.

11. Add release notes.
   Add docs/RELEASE_V1_0.md.
   Include:
   - what Tilo is;
   - what is stable in v1.0;
   - what is experimental;
   - quick start;
   - known limitations;
   - roadmap after v1.0.

   Be honest. Do not overclaim production readiness.

12. Update README and Chinese README after /demo works.
   - Quick Start should point to http://localhost:3000/demo.
   - Keep overview hero image.
   - Mention /demo/telegram only as legacy/internal/advanced if still relevant.
   - Add a concise v1.0 positioning.
   - Add real screenshot only if captured from current UI.
   - Do not add fake screenshots.

13. Run verification.
   Try:
   - python -m pytest backend/tests
   - python scripts/validate_app.py examples/apps/contract-review-agent
   - python scripts/validate_app.py examples/apps/sales-followup-agent
   - cd frontend && pnpm install && pnpm build, if pnpm/network are available
   - bash scripts/verify_local_demo.sh, if Docker/services are available

If commands cannot run because of environment limits, report honestly. Do not claim unverified success.

Definition of Done:
- /demo is the primary public demo.
- Demo is minimal by default and hides framework internals.
- Contract review flow works end-to-end.
- Artifact actions execute through backend runtime.
- Observations and memory candidates are created through the runtime loop.
- Core framework contracts are documented and validated.
- App scaffold and validation path works.
- CI covers backend tests, app validation, and frontend build.
- README and Chinese README are updated for v1.0.
- Release notes document stable features and known limitations honestly.
- Final summary includes files changed, tests run, results, and known limitations.
```
