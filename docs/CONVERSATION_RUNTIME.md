# Conversation Runtime

APIs:
- `POST /api/conversations`
- `GET /api/conversations/{session_id}`
- `POST /api/conversations/{session_id}/turns`
- `GET /api/conversations/{session_id}/turns`
- `POST /api/conversations/{session_id}/messages`
- `POST /api/conversations/{session_id}/observations/from-interaction`

Session lookup supports `channel + external_thread_id` for restore behavior.

Turn types include:
`user_message`, `agent_message`, `mini_surface`, `observation`, `rich_surface_link`, and system/memory variants.

`/demo` is the primary v1.0 public demo and uses `session_id` in the URL to restore a web conversation session. `/demo/telegram` keeps the same restore behavior as a compatibility/internal demo. If no session id is present, the page creates a conversation session and updates the URL with `history.replaceState`.

Important UI actions should write both:
- `UIInteractionEvent` for durable interaction logging
- linked `ConversationTurn(turn_type="observation")` so future agent context can see what the user did

`AgentContextBuilder` accepts `session_id` and returns recent conversation turns, recent user messages, recent agent messages, UI observations, pending confirmations, confirmed memories, active artifact summary, and the last policy decision.

`POST /api/conversations/{session_id}/messages` is the preferred conversation-native entry point. It appends the user turn and attachments, creates a `Task` and `Run` with `Run.session_id`, executes the runtime, then appends the agent response and any artifact rich surface link.

`RunManager.execute(..., session_id=...)` resolves the explicit session id first, then `run.session_id`. When a session is available, it bridges recent conversation turns and observation turns into `PromptBuilder` without turning observations into memory automatically.

Backend code should use `ConversationService` instead of creating `ConversationSession` or `ConversationTurn` rows directly. The service owns:
- `create_or_get_session`
- `find_by_external_thread`
- `append_turn`
- typed helpers for user/agent messages, attachments, mini surfaces, observations, and rich surface links
- `append_observation_for_interaction`

Context and prompt builders cap recent conversation context to 12 turns, 5 UI observations, and 500 characters per turn.

When `POST /api/interactions` receives `session_id`, the backend appends a linked observation turn and runs ORID context reflection. Reflection may create only unconfirmed memory candidates. See `docs/ORID_CONTEXT_REFLECTION.md`.

Artifact actions should use `POST /api/artifacts/{artifact_id}/actions/{action_id}`. The Artifact Action Runtime creates the `UIInteractionEvent` itself and, when `session_id` is present, appends the linked observation turn through `ConversationService.append_observation_for_interaction`.

Channel adapters should reuse the Artifact Action Runtime when a callback can resolve artifact/action context. Telegram artifact callbacks use `tilo:artifact_action:<artifact_id>|<action_id>|<block_id>`.
