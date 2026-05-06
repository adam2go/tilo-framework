# Conversation Runtime

APIs:
- `POST /api/conversations`
- `GET /api/conversations/{session_id}`
- `POST /api/conversations/{session_id}/turns`
- `GET /api/conversations/{session_id}/turns`

Session lookup supports `channel + external_thread_id` for restore behavior.

Turn types include:
`user_message`, `agent_message`, `mini_surface`, `observation`, `rich_surface_link`, and system/memory variants.

`/demo/telegram` uses `session_id` in the URL to restore a session. If no session id is present, the page creates a web conversation session and updates the URL with `history.replaceState`.

Important UI actions should write both:
- `UIInteractionEvent` for durable interaction logging
- linked `ConversationTurn(turn_type="observation")` so future agent context can see what the user did

`AgentContextBuilder` accepts `session_id` and returns recent conversation turns, recent user messages, recent agent messages, UI observations, pending confirmations, confirmed memories, active artifact summary, and the last policy decision.
