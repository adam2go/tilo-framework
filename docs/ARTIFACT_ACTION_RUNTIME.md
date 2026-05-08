# Artifact Action Runtime

v0.9 makes artifact actions a backend runtime capability.

Principle:

```text
Frontend renders intent. Backend owns action semantics.
```

The frontend should not decide how to approve confirmations, confirm memory, invoke tools, or continue a task. It sends the artifact action request and renders the returned `ActionResult`.

## Endpoint

```text
POST /api/artifacts/{artifact_id}/actions/{action_id}
```

Request:

```json
{
  "block_id": "optional-block-id",
  "session_id": "optional-conversation-session-id",
  "run_id": "optional-run-id",
  "source": "web",
  "payload": {},
  "idempotency_key": "optional-client-key"
}
```

Response:

```json
{
  "status": "completed",
  "action_id": "approve_revision",
  "artifact_id": "artifact-id",
  "block_id": "block-id",
  "interaction_event_id": "event-id",
  "conversation_turn_id": "turn-id",
  "confirmation_id": null,
  "memory_id": null,
  "tool_invocation_id": null,
  "task_id": null,
  "run_id": null,
  "artifact_version_id": null,
  "message": "Action completed.",
  "next_actions": [],
  "warnings": []
}
```

Statuses are `completed`, `pending_confirmation`, `rejected`, `failed`, and `noop`.

## Resolution

Action lookup is deterministic:

1. If `block_id` is provided, search that block's `actions`.
2. Search artifact-level `actions`.
3. If the same action id appears in multiple blocks, `block_id` is required.

Unknown actions return a clear `404` or `422`. Unsupported action types return a safe `failed`/`noop` result rather than a server error.

## Supported Actions

- `approve` / `confirm` / `reject`: resolve `confirmation_id` or `state_binding.entity_type=confirmation` and update the Confirmation. Memory bindings confirm or reject Memory candidates.
- `create_memory`: creates an unconfirmed memory candidate only.
- `continue_task`: requires `session_id` and uses the conversation-native message path.
- `invoke_tool`: high-risk or `confirmation_required` actions return `pending_confirmation`.
- `regenerate`: returns a truthful `noop` until a real regenerate path exists.
- `export`: returns a truthful `noop`; JSON can be read from the artifact API.
- `promote_skill`: promotes a bound skill candidate when that flow exists.
- `select` / `edit`: records the action as a durable observation.

## ROAM Linkage

Every action creates a `UIInteractionEvent`. When `session_id` is provided, the runtime appends a linked `ConversationTurn(turn_type="observation")`.

For approve, confirm, reject, select, and edit actions, the runtime may run `ContextReflectionService`. Reflection errors are returned as warnings and do not break the action. Reflection can create only unconfirmed memory candidates.

## Safety

- Request payloads are sanitized before persistence.
- API keys, tokens, passwords, authorization headers, raw long contract text, and hidden reasoning must not be stored.
- High-risk tools are never silently executed.
- Memory is never auto-confirmed by `create_memory`.

## Frontend Usage

Use `frontend/lib/artifactActions.ts`:

```ts
await executeArtifactAction({
  artifactId,
  actionId,
  blockId,
  sessionId,
  payload: { choice: "approve" },
});
```

Components should render `ActionResult.status` and `ActionResult.message`. Direct calls to confirmations, memories, tools, or skills should be reserved for documented fallbacks.

## Channel Adapters

Channel adapters should call the same endpoint or service when a callback can resolve `artifact_id`, `action_id`, and optional `block_id`.

Telegram supports artifact action callback refs shaped like:

```text
tilo:artifact_action:<artifact_id>|<action_id>|<block_id>
```

If a callback lacks artifact action context, the adapter should preserve its existing behavior.
