# Next Demo Polish and Runtime Plan

This plan defines the next milestone after the Telegram-like LLM demo implementation.

The current implementation has the right foundation:

```text
Chat-like entry -> Rich ROAM Surface -> Developer Inspector -> LLM mode / deterministic fallback
```

The next goal is not to add many more features. The goal is to make the demo feel polished, credible, and public-launch ready.

---

## 1. Current Status

The current codebase already includes:

- `/demo/telegram` route
- Telegram-like demo page
- Chat simulator
- Rich ROAM surface preview
- Developer inspector
- Runtime capabilities endpoint
- OpenAI-compatible model client
- Contract Review LLM generator
- deterministic fallback mode
- Telegram channel adapter foundation
- smoke tests for model fallback, runtime, Telegram callback, and interaction events

This is enough to prove the concept technically.

The next milestone should improve product quality and developer trust.

---

## 2. Product Goal

Make `/demo/telegram` a public showcase page that communicates this within 5 seconds:

```text
Chat is the entry.
Surface is the workspace.
Interaction becomes memory.
```

A visitor should understand:

1. Tilo can start from a chat-like channel.
2. Rich interactions belong in a ROAM surface, not in a chat bubble.
3. UI actions become durable observations.
4. Confirmed observations can become memory.
5. Real LLM mode is supported through backend-only OpenAI-compatible config.

---

## 3. P0: Polish the Showcase Experience

### 3.1 Make the center surface the visual hero

The center panel should dominate attention.

Improve:

- larger visual hierarchy for active stage
- clearer active risk node
- better action placement
- reduce visual noise around secondary risks
- use stage-specific empty/loading/success states

Avoid:

- long scrolling list as the main experience
- too many equal-weight cards
- dashboard-like density

### 3.2 Improve stage transition feel

The demo should feel dynamic.

Required stages:

```text
Intent -> Risk Review -> Approval -> Revision Draft -> Memory
```

For each stage:

- show active stage clearly
- show what changed from the previous stage
- add subtle transition or status change
- update chat messages and live events

### 3.3 Make left chat feel more real

Add staged messages:

```text
User: Review this contract...
Bot: I found 3 high-risk clauses. Opening the rich review surface.
User: Approve Revision
Bot: Approved. I’m generating a conservative revision draft.
Bot: Should I remember this review preference?
User: Remember this preference
Bot: Remembered. Future reviews will use it.
```

Add:

- typing/loading state
- replay demo button
- reset demo state
- disabled states that explain why an action is not available

### 3.4 Reduce right inspector weight

Default visible cards:

- Live Events
- Renderer Decision
- Runtime Mode

Collapse or de-emphasize:

- Interaction Contract
- raw counts
- debug details

The inspector should support understanding, not compete with the main surface.

---

## 4. P1: Make the Demo More Real

### 4.1 Add contract input mode

Add a toggle:

```text
Use sample contract
Paste your own contract
```

If the user pastes contract text:

- include it in the message content
- pass it into the LLM prompt
- show a small Contract Snippet card in the surface
- keep deterministic fallback working

Do not implement file upload yet.

### 4.2 Improve LLM output grounding

Contract review LLM output should include:

- risk summary
- exactly 3 primary risks for the demo surface
- evidence text
- suggested revisions
- revision draft
- memory candidate

Normalize output so the demo stays visually stable even when the model returns too much detail.

### 4.3 Add model diagnostics without exposing secrets

Show:

```text
Provider: deepseek / custom / openai
Model: DEFAULT_MODEL
Mode: LLM or deterministic
Fallback: yes/no
```

Never show:

- API keys
- raw request headers
- full hidden prompt
- raw model response by default

---

## 5. P2: Make Interaction Contract Realer

The Developer Inspector should eventually read from a real example contract instead of hardcoded text.

Target:

```text
examples/interaction-contracts/contract-review.roam.yaml
  -> loaded or mirrored through backend
  -> displayed in Inspector
  -> used to explain render/observe/act/memorize mapping
```

Minimal implementation:

- add a static JSON endpoint or import helper for example contracts
- display the actual contract trigger/render/observe/act/memorize fields
- keep it read-only

Do not build a complex rules engine yet.

---

## 6. P3: README and Launch Assets

Add real assets:

```text
docs/assets/telegram-like-llm-demo.png
docs/assets/telegram-like-llm-demo.gif
```

Update README:

- show screenshot near top
- add one-command quick start
- add deterministic mode setup
- add LLM mode setup
- link to `/demo/telegram`

Do not add fake screenshots.

---

## 7. P4: Testing and Reliability

Add focused tests for:

- runtime capabilities response
- model client fallback
- contract review LLM normalization
- demo message flow if possible
- interaction event persistence
- memory confirmation flow
- Telegram callback short-id resolution

Also add a lightweight CI workflow if missing.

---

## 8. Suggested Codex Prompt

```text
Read docs/NEXT_DEMO_POLISH_AND_RUNTIME_PLAN.md.

Polish the current /demo/telegram implementation into a public showcase.

Do not add a lot of new features.
Focus on making the demo more impressive, stable, and understandable.

Implement in order:
1. Make the center Rich ROAM Surface the visual hero.
2. Improve stage transitions: Intent -> Risk Review -> Approval -> Revision Draft -> Memory.
3. Make the left chat flow more realistic with typing/loading, staged bot messages, replay/reset.
4. Reduce right inspector visual weight; keep Live Events, Renderer Decision, Runtime Mode most visible; collapse Interaction Contract by default.
5. Add sample/paste contract input mode.
6. Normalize LLM contract review output so the demo stays visually stable.
7. Add safe model diagnostics, no secrets.
8. Prepare README screenshot/GIF asset hooks, but do not add fake screenshots.
9. Preserve deterministic fallback and LLM mode.
10. Preserve existing Telegram adapter and workspace behavior.

Definition of done:
A first-time visitor can understand the product in 5 seconds and the page is ready for README screenshots and a short launch video.
```

---

## 9. Definition of Done

This milestone is complete when:

- `/demo/telegram` feels like a polished public demo.
- The center surface is clearly the hero.
- The chat flow feels alive.
- The inspector explains rather than overwhelms.
- The demo can run without a key.
- The demo can use real LLM mode.
- No secrets are exposed.
- A screenshot of the page is good enough for README and X launch posts.
