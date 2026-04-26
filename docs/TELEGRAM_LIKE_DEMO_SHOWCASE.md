# Telegram-like LLM Demo Showcase

This document describes the current public demo direction for Tilo.

The demo proves the core product thesis:

```text
Chat is the entry. Surface is the workspace. Interaction becomes memory.
```

It shows how a user can start from a chat-like interface, trigger an LLM-powered agent run, inspect a generated rich ROAM surface, approve actions, and create durable observations and memory.

---

## 1. Demo Route

Recommended route:

```text
/demo/telegram
```

The demo is not a Telegram clone. It is a Telegram-like developer showcase for Tilo.

---

## 2. Current Demo Shape

The current demo uses a three-zone layout:

```text
Left   : Telegram-like chat entry
Center : Dynamic ROAM Surface
Right  : Developer Inspector
```

### Left: Chat-like entry

The left panel shows the user-facing IM experience:

- bot welcome message
- user goal
- bot status update
- run demo action
- open review surface action
- approve revision action
- remember preference action

This demonstrates that IM/chat can be the task entry and lightweight decision layer.

### Center: Dynamic ROAM Surface

The center panel is the rich workspace.

For the Contract Review demo, it renders:

- LLM/runtime mode badge
- ROAM stage strip
- risk summary
- active risk node
- recommended revision
- secondary risk cards
- approval actions
- memory action

This demonstrates that rich SaaS interactions should not be forced into chat bubbles.

### Right: Developer Inspector

The right panel shows developer-facing runtime transparency:

- Interaction Contract
- Channel -> Surface Routing
- Renderer Decision
- Live Events
- Runtime Mode
- Durable Observations

This explains why each UI element exists and how user interactions become structured events.

---

## 3. LLM Mode

The demo supports both deterministic mode and LLM mode.

### Deterministic mode

Used when no model API key is configured.

```text
LLM_ENABLED=false
```

The demo remains fully runnable for local open-source users.

### LLM mode

Used when OpenAI-compatible model settings are configured.

```text
LLM_ENABLED=true
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
DEFAULT_MODEL=...
```

The current demo has been verified with an OpenAI-compatible provider setup and can show a badge such as:

```text
LLM mode: deepseek · deepseek-v4-pro
```

The model output should be validated and converted into `artifact_spec.v1` blocks.

---

## 4. Why This Demo Matters

This demo is the first concrete public proof that Tilo is not just another agent framework.

It shows three things at once:

1. **Channel entry**
   Users can start from a familiar chat-like surface.

2. **Rich surface delivery**
   Complex AI-native SaaS components are rendered in a dedicated workspace.

3. **Developer observability**
   Interaction contracts, routing, observations, memory, and runtime mode are visible.

---

## 5. Public Messaging

Use these messages when explaining the demo:

```text
Chat is the entry. Surface is the workspace. Interaction becomes memory.
```

```text
Tilo lets agents start from chat, render rich SaaS surfaces, observe user actions, and turn confirmed decisions into memory.
```

```text
The interface is no longer a passive display layer. It becomes part of the agent loop.
```

```text
MCP connects tools. A2A connects agents. Tilo connects agents, UI, humans, observations, and memory.
```

---

## 6. Current Demo Quality Bar

The demo is good enough to communicate the core idea when it shows:

- chat-like entry on the left
- LLM-powered contract review in the center
- developer inspector on the right
- live event flow
- model runtime mode
- approval and memory actions

Before public launch, the README should include a real screenshot or short GIF.

Recommended asset path:

```text
docs/assets/telegram-like-llm-demo.png
```

Do not add fake screenshots. Use a real current UI screenshot.

---

## 7. Next Improvements

Suggested next improvements:

1. Add screenshot/GIF to README.
2. Improve first-run empty state.
3. Make active risk node selection interactive.
4. Add a small event animation when user clicks approval.
5. Add copy-to-contract example snippet.
6. Add a one-command demo setup section.
7. Add public deployment instructions.

---

## 8. Demo Setup Notes

Minimum local setup:

```bash
cp .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:3000/demo/telegram
```

For deterministic mode:

```text
LLM_ENABLED=false
```

For LLM mode:

```text
LLM_ENABLED=true
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
DEFAULT_MODEL=...
```

Never expose API keys to the frontend.
