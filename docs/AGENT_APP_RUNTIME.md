# Agent App Runtime (v0.5 Round 2)

Tilo keeps a conversation-first runtime. App manifest + interaction policy stay backend source of truth.

Round 2 adds durable conversation runtime objects:
- `ConversationSession`
- `ConversationTurn`
- `Run.session_id` for linking task execution back to the conversation
- `ContextReflection` for deterministic ORID reflection over selected conversation and UI signals

Channels (web/telegram) should map incoming events into the same session model when possible.

The current example apps are:
- `contract-review-agent`: contract review, mini decision cards, rich artifact drawer/page escalation.
- `sales-followup-agent`: sales follow-up drafting, tone choice, memory capture, rich draft escalation.

App manifests declare the mini and rich surfaces a policy may return. The backend validates policy outputs against those declarations so frontend code is not the primary policy authority.

The preferred app execution path is:

```text
POST /api/conversations/{session_id}/messages
  -> ConversationTurn(user_message)
  -> Task + Run(session_id)
  -> AgentContextBuilder(session_id)
  -> PromptBuilder(recent turns + observations)
  -> Artifact / confirmations / memory candidates
  -> ConversationTurn(agent_message)
  -> optional ConversationTurn(rich_surface_link)
```

UI events should pass `session_id` to `POST /api/interactions` when available. The backend owns observation turn creation and ORID context reflection.

The runtime remains intentionally small:
- conversation-first entry point
- deterministic fallback preserved
- LLM mode preserved when configured
- no secrets in manifests, policies, traces, or frontend state
