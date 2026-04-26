# Telegram Channel Adapter Plan

This document defines Tilo's first IM channel integration: Telegram.

Tilo should start with Telegram before WeChat, Slack, Discord, or other channels because Telegram provides a relatively developer-friendly path for validating the core channel strategy:

```text
Chat is the entry.
Artifact Surface is the workspace.
Interactions become observations.
```

Telegram should be used as a command, notification, lightweight approval, and rich-surface entry channel. It should not try to render every AI-native SaaS component directly inside chat.

---

## 1. Why Telegram First?

Telegram is a good first channel because it supports:

- Bot messages
- Inline keyboards
- Callback queries
- Deep links
- Telegram Web Apps
- Simple webhook-based integration
- Good developer experience
- Lower platform friction than many enterprise IM or WeChat mini-program flows

For Tilo, Telegram can validate the most important cross-channel idea:

```text
User starts from IM -> Tilo creates task/run -> Telegram shows lightweight status/actions -> rich Artifact opens in web surface -> user actions return to Tilo as observations -> memory improves future runs
```

---

## 2. Product Role of Telegram

Telegram is not the full Tilo UI.

Telegram should act as:

1. **Task entry**
   Users can send natural language goals to the bot.

2. **Run status notification**
   Tilo can notify users when a run starts, needs approval, completes, or fails.

3. **Lightweight decision layer**
   Simple approve/reject/confirm actions can happen directly through Telegram buttons.

4. **Rich surface launcher**
   Complex artifacts open as Tilo web pages or Telegram Web Apps.

5. **Observation return path**
   Button clicks and Web App events become `UIInteractionEvent` records.

Telegram should not be used for:

- full contract editing
- complex dashboard interaction
- long document review
- advanced memory management
- developer debugging

Those should open the Tilo web artifact surface.

---

## 3. Surface Capability Model for Telegram

Telegram should be treated as a Level 1.5 channel:

```text
Level 1: Chat actions
Level 2: Embedded web surface
```

Telegram can support both:

- lightweight chat cards with buttons
- rich surfaces through Telegram Web Apps or normal web links

### Recommended rendering policy

| Interaction Component | Telegram Rendering Strategy |
|---|---|
| ApprovalCard | Telegram message + inline approve/reject buttons |
| ToolCallPreview | Telegram message + approve/reject buttons + artifact link |
| MemoryCandidateCard | Telegram message + confirm/reject buttons if simple |
| RiskReviewPanel | Summary message + Open Artifact button |
| EditableDocumentPreview | Open Artifact button |
| ComparisonMatrix | Summary message + Open Artifact button |
| MetricDashboard | Summary message + Open Artifact button |
| ActionQueue | Message with limited action buttons |
| Trace / Debug | Link to Tilo Console only |

---

## 4. Telegram User Flow

### 4.1 Start bot

User opens Telegram bot and sends:

```text
/start
```

Bot replies:

```text
Welcome to Tilo.
Send me a goal, or run a demo.

[Run Contract Review Demo]
[Open Tilo Console]
[Docs]
```

### 4.2 Send goal

User sends:

```text
Review this contract and flag risky clauses around payment, liability, and termination.
```

Tilo creates:

```text
Task
Run
TraceStep
```

Bot replies:

```text
Task created. Tilo is reviewing the contract.

Status: Rendering contract review workflow...
```

### 4.3 Artifact ready

After artifact generation, bot sends:

```text
Contract Review is ready.

3 high-risk clauses found.
5 medium-risk clauses found.

Open the interactive review surface to inspect details.

[Open Review Surface]
[Approve Conservative Revision]
[Not now]
```

`Open Review Surface` should link to:

```text
/artifacts/{artifact_id}?channel=telegram&conversation_id=...
```

or a Telegram Web App URL if implemented.

### 4.4 Lightweight approval

If user clicks:

```text
Approve Conservative Revision
```

Tilo should:

1. Receive Telegram callback query.
2. Create `UIInteractionEvent`.
3. Approve or create linked `Confirmation`.
4. Continue run or create follow-up task.
5. Send status update back to Telegram.

Bot replies:

```text
Approved. Tilo is generating a conservative revision draft.
```

### 4.5 Memory confirmation

After completion, bot may send:

```text
Should Tilo remember this preference?

"User prefers conservative contract review with explicit actionable revision suggestions."

[Remember]
[Edit in Console]
[Not now]
```

If user clicks `Remember`, Tilo should:

- create `UIInteractionEvent`
- confirm memory candidate
- notify user

---

## 5. Architecture

```text
Telegram Bot API
  -> Telegram Webhook Endpoint
  -> Channel Adapter
  -> Message Normalizer
  -> Tilo Event
  -> Task / Run / Interaction / Memory / Confirmation Services
  -> Telegram Response Renderer
```

Recommended backend modules:

```text
backend/app/services/channels/
  base.py
  capabilities.py
  renderer.py
  telegram/
    adapter.py
    webhook.py
    renderer.py
    types.py
```

Recommended API route:

```text
POST /api/channels/telegram/webhook
```

Optional debug route:

```text
GET /api/channels/telegram/health
```

---

## 6. Channel Adapter Interface

Add a lightweight channel adapter abstraction.

Python-style sketch:

```python
class ChannelCapability(BaseModel):
    supports_text: bool = True
    supports_buttons: bool = False
    supports_cards: bool = False
    supports_embedded_web: bool = False
    supports_file_upload: bool = False
    max_message_length: int | None = None

class ChannelAdapter(Protocol):
    channel: str
    capability: ChannelCapability

    async def receive(self, payload: dict) -> TiloChannelEvent:
        ...

    async def send(self, output: ChannelOutput) -> None:
        ...

    async def render(self, component: dict, context: dict) -> ChannelRenderResult:
        ...
```

For Telegram:

```python
telegram_capability = ChannelCapability(
    supports_text=True,
    supports_buttons=True,
    supports_cards=True,
    supports_embedded_web=True,
    supports_file_upload=True,
    max_message_length=4096,
)
```

---

## 7. Normalized Channel Event

Telegram payloads should be normalized into a Tilo channel event.

```python
class TiloChannelEvent(BaseModel):
    id: str
    channel: Literal["telegram"]
    event_type: str
    external_user_id: str
    external_chat_id: str
    text: str | None = None
    callback_data: dict | None = None
    attachments: list[dict] = []
    raw_payload: dict | None = None
```

Recommended event types:

```text
channel.message.received
channel.command.start
channel.callback.clicked
channel.webapp.event
channel.file.received
```

---

## 8. Telegram Rendering Rules

The renderer should map Tilo components into the best Telegram representation.

### 8.1 ApprovalCard

Tilo component:

```text
ApprovalCard
```

Telegram rendering:

```text
Message text + inline keyboard
```

Example:

```text
Approval needed

Generate a conservative revision draft based on 3 high-risk clauses?

[Approve] [Reject]
[Open Review Surface]
```

### 8.2 RiskReviewPanel

Telegram should not render the full panel.

Instead:

```text
Contract Review Summary

3 high-risk clauses found:
- Payment terms
- Liability limitation
- Termination rights

Open the full review surface to inspect evidence and suggested revisions.

[Open Review Surface]
[Approve Conservative Revision]
```

### 8.3 MemoryCandidateCard

Simple memory can be rendered directly:

```text
Remember this preference?

User prefers conservative contract review with actionable revision suggestions.

[Remember] [Not now]
[Edit in Console]
```

### 8.4 ToolCallPreview

For high-risk tools:

```text
Tool action requires approval

Tool: send_follow_up_email
Permission: high
Summary: Send follow-up email to 3 customers.

[Approve] [Reject]
[Open details]
```

---

## 9. Callback Data Format

Telegram callback data has length limits, so do not store large JSON directly in callback data.

Use compact callback references.

Recommended format:

```text
tilo:{action}:{short_id}
```

Examples:

```text
tilo:approve_confirmation:abc123
tilo:reject_confirmation:abc123
tilo:confirm_memory:def456
tilo:open_artifact:ghi789
```

The backend should resolve `short_id` to durable records.

Do not put secrets or large payloads in callback data.

---

## 10. Deep Links and Artifact Links

Tilo should generate links to rich surfaces.

Recommended URL shape:

```text
/artifacts/{artifact_id}?channel=telegram&chat_id={chat_id}&token={short_lived_token}
```

Security note:

- Do not expose raw user IDs or secrets without signing.
- Prefer short-lived signed tokens.
- For v0.1, if auth is not implemented, clearly mark artifact links as local/dev only.

Future Telegram Web App URL:

```text
https://your-tilo-host/app/artifacts/{artifact_id}?tgWebAppStartParam=...
```

---

## 11. Environment Variables

Add to `.env.example`:

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
TELEGRAM_WEBHOOK_URL=
PUBLIC_APP_URL=http://localhost:3000
```

Optional:

```text
TELEGRAM_WEBAPP_URL=
```

Security:

- Never commit actual bot tokens.
- Validate webhook secret if configured.
- Do not log raw tokens.

---

## 12. Minimal Implementation Scope

Do not overbuild Telegram integration in the first PR.

### Phase 1: Local foundation

Implement:

1. Channel capability types.
2. Telegram adapter skeleton.
3. Telegram webhook route.
4. Message normalization for text messages and callback queries.
5. Renderer for:
   - plain text
   - approval buttons
   - artifact link buttons
6. Mapping from Telegram message to Tilo task creation.
7. Mapping from Telegram callback to `UIInteractionEvent`.
8. `.env.example` update.
9. Docs update.

Do not implement:

- full Telegram Web App yet
- payment
- group chat advanced permissions
- file upload parsing beyond placeholder
- production-grade auth
- complex conversation state machine

### Phase 2: Rich surface launch

Implement:

1. Open Artifact button.
2. Short-lived token placeholder or signed link helper.
3. Channel context passed to artifact page.
4. Telegram-specific return actions if needed.

### Phase 3: Web App integration

Implement later:

1. Telegram Web App launch.
2. Web App init data validation.
3. Web App event return to backend.

---

## 13. Required User Stories

### Story 1: Start demo from Telegram

As a user, I can open the Telegram bot, click `Run Contract Review Demo`, and receive a contract review summary with a link to the full artifact surface.

### Story 2: Approve from Telegram

As a user, I can approve a simple action directly from Telegram, and Tilo records it as a durable observation.

### Story 3: Open rich surface

As a user, I can open the full Artifact Surface from Telegram when the interaction is too complex for chat.

### Story 4: Confirm memory

As a user, I can confirm a simple memory candidate from Telegram, and Tilo remembers it for future runs.

---

## 14. Backend Acceptance Criteria

- `POST /api/channels/telegram/webhook` exists.
- Telegram payloads are normalized into `TiloChannelEvent`.
- Text messages can create a Task/Run or trigger existing message flow.
- Callback queries can create `UIInteractionEvent`.
- Callback queries can approve confirmation or confirm memory when IDs are resolvable.
- Renderer can produce Telegram-compatible message payloads.
- No secrets are logged.
- Missing token/config fails gracefully.

---

## 15. Frontend Acceptance Criteria

- Artifact links can include channel context.
- Artifact page can display a small banner like:

```text
Opened from Telegram
```

- If action came from Telegram, UI should still reflect updated confirmation/memory status.
- No Telegram-only assumptions should leak into generic Artifact components.

---

## 16. Example Interaction Contract Surface Hints

Update or support surface hints like:

```yaml
render:
  component: RiskReviewPanel
  preferred_surface: rich_web
  fallback_component: ApprovalCard
  fallback_text: Open the contract review page to inspect risks.

surface:
  preferred: rich_web
  allowed:
    - rich_web
    - telegram_chat_card
    - text_link
  fallback: text_link
```

For simple approvals:

```yaml
render:
  component: ApprovalCard

surface:
  preferred: telegram_chat_card
  allowed:
    - telegram_chat_card
    - rich_web
    - text_link
  fallback: text_link
```

---

## 17. Codex Implementation Prompt

```text
Read docs/TELEGRAM_CHANNEL_ADAPTER_PLAN.md and docs/CHANNEL_AND_SURFACE_STRATEGY.md.

Implement the first Telegram Channel Adapter foundation for Tilo.

Telegram is the first IM channel.

Do not try to render all AI-native SaaS components inside Telegram chat.
Use Telegram for task entry, lightweight approvals, notifications, and links to rich Artifact Surfaces.

Implement Phase 1 only:
1. Channel capability types.
2. Telegram adapter skeleton.
3. Telegram webhook route: POST /api/channels/telegram/webhook.
4. Normalize Telegram text messages and callback queries into TiloChannelEvent.
5. Renderer for plain text, approval buttons, and artifact link buttons.
6. Allow Telegram text messages to trigger the existing Tilo message/task flow if possible.
7. Allow Telegram callback queries to persist UIInteractionEvent and approve confirmation / confirm memory when IDs are resolvable.
8. Add TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, TELEGRAM_WEBHOOK_URL, PUBLIC_APP_URL to .env.example.
9. Add or update tests for message normalization and callback parsing.

Preserve existing web-first ROAM surface behavior.
Do not build Telegram Web App in this phase.
Do not store secrets in logs.
```

---

## 18. Summary

Telegram should prove this channel model:

```text
IM is the entry and lightweight decision layer.
Artifact Surface is the rich workspace.
Tilo Runtime connects both through ROAM observations and memory.
```

If this works well, WeChat, Slack, Discord, and enterprise IM adapters can follow the same pattern.
