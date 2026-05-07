# ORID Context Reflection

v0.7 adds a small deterministic reflection layer for turning selected conversation and UI signals into reviewable memory candidates.

ORID does not replace ROAM. ROAM remains the product/runtime loop; ORID sits inside Observe -> Act/Memorize to interpret raw interactions before proposing the next action.

It is not a model reasoning transcript and it does not auto-confirm memory.

## ORID Shape

`ContextReflectionService` separates signals into:

- Objective: factual events and user messages only.
- Reflective: observed preference or behavior signals.
- Interpretive: cautious meaning inferred from the signals.
- Decisional: next runtime action, usually `propose_memory` or `none`.

Objective facts must stay factual. Do not put inferred preferences, hidden reasoning, or speculative claims in Objective.

## Triggers

Reflection runs when an interaction is linked to a conversation session:

```text
POST /api/interactions
  session_id provided
    -> UIInteractionEvent
    -> ConversationTurn(observation)
    -> ContextReflection
    -> optional Memory(status=candidate)
```

Telegram callbacks use the same observation/reflection path after the channel event is normalized.

## Memory Candidates

Reflection may create a `Memory` only as:

```text
status = candidate
is_confirmed = false
source_type = context_reflection
```

`structured_payload` includes:

- `source`
- `session_id`
- `why`
- `orid_evidence`

The user must still confirm, edit, or reject the candidate before recall treats it as durable memory.

## Current Deterministic Rules

- Approval plus revision signals can propose a contract revision preference.
- Tone feedback can propose a tone or negotiation-style preference.
- Repeated Open Full Review or Open Artifact actions can propose an evidence-detail preference.
- `confirm_memory` does not create a duplicate candidate.
- `reject_memory`, `skip_memory`, and `not_now` suppress immediate duplicate proposals.

## Safety

Reflection uses sanitized interaction payloads and keeps candidates reviewable. Do not store secrets, API keys, tokens, passwords, hidden chain-of-thought, or untrusted document claims as confirmed memory.
