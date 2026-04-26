# Channel and Surface Strategy

Tilo should not assume that every AI-native SaaS interaction happens inside the web console.

Many real users will start from messaging channels such as WeChat, Telegram, Slack, Discord, email, or enterprise IM tools. At the same time, Tilo's generated AI-native SaaS surfaces may be too rich to render fully inside a chat thread.

This document defines Tilo's channel and surface strategy.

---

## 1. Core Position

Tilo should treat channels as entry points and feedback loops, not necessarily as the full UI container.

Recommended model:

```text
Messaging Channel = command, notification, lightweight approval, return path
Rich Surface = web page, mini app, webview, or hosted artifact page
Tilo Runtime = ROAM loop, interaction contract, observation, memory, tools
```

In other words:

```text
IM starts the task.
Tilo renders the rich surface.
User actions return as observations.
Tilo acts and memorizes.
```

Do not force all interaction components to fit inside a chat bubble.

---

## 2. Why This Matters

Tilo's core value is AI-native SaaS delivery:

```text
Render -> Observe -> Act -> Memorize
```

Some ROAM interactions are simple:

- approve / reject
- choose one option
- confirm memory
- quick reply

These can work inside IM.

But some interactions are rich:

- contract review panel
- editable document
- comparison matrix
- dashboard
- workflow surface
- artifact page

These should usually open a rich surface.

---

## 3. Channel Capability Levels

Tilo should classify each channel by surface capability.

### Level 0: Text-only

Examples:

- SMS
- plain email
- basic webhook chat

Capabilities:

- text input
- text output
- link to artifact page

Typical use:

```text
Notify user -> provide link -> collect simple reply
```

### Level 1: Chat actions

Examples:

- Telegram inline keyboard
- Slack buttons
- Discord buttons
- enterprise IM quick actions

Capabilities:

- message cards
- buttons
- quick approve/reject
- limited selection
- link to rich surface

Typical use:

```text
ApprovalCard -> native chat buttons
MemoryCandidateCard -> confirm/reject buttons
ToolCallPreview -> approve/reject button
```

### Level 2: Embedded web surface

Examples:

- Telegram Web Apps
- WeChat Mini Program
- WeChat H5/webview
- Slack modal/home tab patterns

Capabilities:

- richer UI
- forms
- document preview
- dashboards
- workflow surface
- persistent interaction state

Typical use:

```text
Open generated Artifact inside embedded webview or mini app
```

### Level 3: Full web app

Examples:

- Tilo Console
- hosted artifact page
- enterprise web portal

Capabilities:

- full ROAM Workspace
- advanced artifact pages
- memory review
- trace/observability
- skill management
- developer console

Typical use:

```text
Complete AI-native SaaS workflow and developer inspection
```

### Level 4: Desktop/browser runtime

Examples:

- browser extension
- desktop app
- cloud computer/sandbox UI

Capabilities:

- browser automation
- GUI automation
- local app control
- richer contextual interaction

Typical use:

```text
Agent uses GUI products and returns interaction surfaces to user
```

---

## 4. Surface Portability Model

Tilo interaction components should be portable across channels.

A component should not assume only one renderer.

Example:

```text
ApprovalCard
  -> Web renderer: full card with details and actions
  -> Telegram renderer: message + approve/reject buttons
  -> WeChat renderer: mini program card or H5 link
  -> Text renderer: summary + link + reply instructions
```

This implies Tilo needs a renderer abstraction:

```text
Interaction Contract
  -> Component intent
  -> Channel capability detection
  -> Best available renderer
  -> Fallback renderer
```

---

## 5. Relationship to ROAM Interaction Contract

ROAM Interaction Contract defines:

```text
when to interact
what to render
what events to observe
what action happens next
what can become memory
```

Channel strategy adds:

```text
where to render
how rich the surface can be
which fallback to use
how interaction events return to Tilo
```

Interaction contracts should eventually support channel hints:

```yaml
render:
  component: RiskReviewPanel
  preferred_surface: rich
  fallback_component: ApprovalCard
  fallback_text: Open the contract review page to inspect risks.
```

---

## 6. Proposed Surface Contract Extension

Add optional fields to interaction contracts or artifact actions:

```yaml
surface:
  preferred: rich_web
  allowed:
    - rich_web
    - embedded_webview
    - chat_card
    - text_link
  fallback: text_link
  requires:
    - multi_card_layout
    - document_preview
    - approval_actions
```

This lets Tilo decide whether the interaction can be rendered inside the channel or should open an artifact page.

---

## 7. Recommended Default Behavior

### Simple approval

Render inside channel if possible.

```text
ToolCallPreview / ApprovalCard -> chat card with approve/reject buttons
```

### Rich review

Send a concise message and open rich surface.

```text
RiskReviewPanel / EditableDocument / Dashboard -> link to artifact page or mini app
```

### Memory confirmation

Can render in chat or rich surface.

```text
MemoryCandidateCard -> chat approve/reject if simple, full memory review page if complex
```

### Developer inspection

Always use web console.

```text
Trace / Skills / Observations / Debug -> Tilo Console
```

---

## 8. Channel Adapter Architecture

Tilo should eventually provide channel adapters.

```text
Channel Adapter
  - receives user messages/events
  - normalizes them into Tilo events
  - sends messages/cards/links back to user
  - maps channel actions to UIInteractionEvent
```

Recommended interface:

```ts
type ChannelAdapter = {
  channel: string;
  capability: ChannelCapability;
  receive(input): Promise<TiloEvent>;
  send(output): Promise<void>;
  render(component, context): Promise<ChannelRenderResult>;
};
```

---

## 9. Suggested Initial Channels

### Phase 1: Web-first

- Tilo Console
- standalone artifact pages
- shareable artifact links

This is the fastest way to prove rich AI-native SaaS surfaces.

### Phase 2: Telegram

Telegram is a good early integration because it supports bots, inline keyboards, and Web Apps.

Use Telegram as:

- task entry
- notification
- approval buttons
- link/open web app for rich surfaces

### Phase 3: WeChat-style integration

For Chinese users, WeChat is important.

Use WeChat as:

- task entry
- notification
- approval interaction
- mini program or H5 surface for rich artifact pages

Do not expect complex SaaS components to render fully inside the chat thread.

### Phase 4: Slack/Discord/Enterprise IM

Useful for developer and enterprise teams.

Use as:

- team notification
- approval workflow
- action buttons
- links to artifact pages

---

## 10. Public Product Guidance

Do not position Tilo as only a web app.

Better positioning:

```text
Tilo lets agents render AI-native SaaS surfaces that can be launched from chat, opened as web artifacts, embedded in mini apps, or connected to enterprise channels.
```

Simpler:

```text
Chat is the entry. Artifact surfaces are the workspace. Interactions become observations.
```

---

## 11. Acceptance Criteria

Tilo's channel strategy is clear when:

1. Developers understand that IM is an entry and lightweight interaction layer.
2. Developers understand that rich components may open web/mini-app artifact surfaces.
3. Interaction contracts can express preferred and fallback surfaces.
4. Channel adapters can map channel events to UIInteractionEvent.
5. The same ROAM loop works across web, IM, and embedded surfaces.
6. Public docs do not imply that all rich UI must live inside chat bubbles.

---

## 12. Codex Prompt

```text
Read docs/CHANNEL_AND_SURFACE_STRATEGY.md and docs/ROAM_INTERACTION_CONTRACT.md.

Add the first lightweight channel and surface abstraction.

Do not implement all channels yet.

Start with:
1. Add channel capability types.
2. Add optional surface preference fields to interaction contract types/examples.
3. Add a simple renderer selection helper:
   - rich components -> artifact page link fallback
   - approval components -> chat card capable fallback
   - text-only channels -> summary + artifact link
4. Add docs/examples showing web, Telegram, and WeChat-style usage.
5. Keep the first implementation web-first.

Goal: make it clear that Tilo can be launched from IM channels while still rendering rich AI-native SaaS surfaces through web/mini-app/artifact pages.
```
