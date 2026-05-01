# Tilo v0.4 Interaction Runtime Roadmap

This roadmap defines the next small-version iteration after the realistic contract review demo.

Tilo's current state already proves the core idea:

```text
Agent by default. UI when necessary.
UI actions become observations.
Confirmed preferences can become memory.
```

The next version should turn this from a demo pattern into a reusable framework capability.

---

## 1. Current Assessment

Tilo already has meaningful foundations:

- Conversation-first Telegram-like demo
- Realistic sample contract fixture
- LLM mode and deterministic fallback
- Artifact generation
- Mini surfaces inside conversation
- UIInteractionEvent persistence
- Confirmation approval flow
- Memory creation flow
- Runtime capabilities endpoint
- Telegram channel adapter foundation
- Tests for core backend behavior

But much of the current behavior is still demo-specific.

The next milestone should move from:

```text
A good demo that proves the idea
```

to:

```text
A reusable interaction runtime that developers can build with
```

---

## 2. Product Principle

Do not make Tilo UI-heavy.

Keep this principle:

```text
Agent by default. UI when necessary.
```

The framework should help developers decide:

1. When not to show UI.
2. When to show a lightweight mini surface.
3. When to escalate to a rich surface.
4. How user interaction becomes observation.
5. How observations drive actions and memory.

---

## 3. Interaction Form Recommendation

The preferred user-facing interaction model is:

```text
Main conversation thread
  + inline mini surfaces when needed
  + optional side drawer / rich surface for details
```

Avoid making the default experience a three-column dashboard.

### 3.1 Main conversation thread

Use for:

- user goals
- agent responses
- agent progress summaries
- mini surfaces
- observation events
- memory confirmation

### 3.2 Inline mini surfaces

Use only for:

- important information
- approval
- decision
- memory confirmation
- tool call confirmation
- rich surface escalation

### 3.3 Side drawer

Use for lightweight details without leaving the conversation.

Examples:

- full clause evidence
- event trace
- interaction contract explanation
- memory candidate lifecycle

### 3.4 Rich surface / artifact page

Use for complex content:

- full contract review
- editable document
- dashboard
- comparison matrix
- long report
- multi-step workflow

Rich surfaces should open intentionally from the conversation:

```text
Open Full Review
Open Artifact
Open Rich Surface
```

---

## 4. What Should Become Framework Capability

### 4.1 Interaction Policy Engine

Current demo logic still decides UI triggers mostly in component code.

Add a lightweight interaction policy layer:

```text
event + context -> no UI | mini surface | rich surface escalation
```

Example policy output:

```json
{
  "decision": "mini_surface",
  "reason": "high_risk_human_confirmation_required",
  "surface_type": "MiniIssueCard",
  "priority": "high"
}
```

Start simple. Do not build a complex rules engine.

### 4.2 Mini Surface Registry

Move demo-specific mini surface mapping into a registry:

```text
MiniIssueCard
MiniApprovalCard
MiniRevisionPreview
MiniMemoryCard
MiniToolPreview
MiniChoiceCard
```

The registry should map:

```text
component_type -> renderer -> supported channels -> fallback
```

### 4.3 Conversation Event Model

Generalize `ChatTurn` into a reusable conversation event model.

Recommended types:

```text
user_message
agent_message
attachment
mini_surface
observation
memory_candidate
system_event
rich_surface_link
```

This can initially live in frontend types, then become backend-backed.

### 4.4 Follow-up Intent Handler

Add a lightweight follow-up intent layer:

```text
explain_risk
revise_tone
focus_clause
draft_email
open_full_review
remember_preference
general_followup
```

Use deterministic rules first and optional LLM classification later.

### 4.5 Memory Candidate Lifecycle

Make memory lifecycle explicit:

```text
candidate proposed -> user confirmed -> memory saved -> future recall
```

Do not immediately make every interaction a memory.

### 4.6 Rich Surface Escalation

Define a reusable escalation mechanism:

```text
mini surface too small -> Open Full Review -> artifact page / drawer
```

The conversation should remain the main interface.

---

## 5. Backend Gaps

### 5.1 Conversation sessions

Current demo has frontend conversation state. Add backend conversation session support.

Minimal model:

```text
ConversationSession
ConversationTurn
```

This allows:

- reloadable demo sessions
- channel continuity
- Telegram/web session mapping
- multi-turn context persistence

### 5.2 Interaction policy runtime

Implement a small service:

```text
InteractionPolicyService.evaluate(context) -> InteractionDecision
```

Inputs:

- artifact type
- risk level
- action permission level
- memory candidate confidence
- channel capability
- interaction budget

Outputs:

- no UI
- mini surface
- rich surface link
- ask text clarification

### 5.3 Contract runtime foundation

ROAM Interaction Contract exists in docs and examples. Add minimal runtime usage:

- load example contract YAML
- resolve trigger conditions
- map to mini surface type
- expose matched contract in inspector/debug view

Do not build a full standard or complex DSL yet.

### 5.4 File handling

The demo currently uses a markdown fixture and paste text. Add real file handling gradually:

1. `.txt` / `.md` upload
2. `.docx` extraction
3. PDF extraction later

For v0.4, `.docx` extraction is nice but not required if it delays interaction runtime work.

### 5.5 Channel abstraction hardening

Telegram adapter exists. Next:

- map mini surfaces to Telegram inline buttons
- map callbacks to conversation observations
- support Open Artifact URL buttons
- preserve same interaction event model across web demo and Telegram

---

## 6. Frontend Gaps

### 6.1 Avoid mixing too many surfaces

Do not put chat, side SaaS page, and inspector all as equal permanent regions.

Recommended layout:

```text
Conversation = default
Side drawer = contextual details
Artifact page = explicit escalation
Developer inspector = hidden by default
```

### 6.2 Surface placement rule

Use this rule:

```text
If the user must decide now -> inline mini surface.
If the user needs details -> side drawer.
If the user needs to work deeply -> artifact page.
```

### 6.3 Demo polish

Add:

- better typing/progress animation
- clear observation bubbles
- compact stage indicator
- memory lifecycle indicator
- replayable scripted path
- screenshot-ready state

---

## 7. Proposed v0.4 Scope

### P0: Generalize conversation + mini surface runtime

- Generalize chat turns into reusable types
- Add Mini Surface Registry
- Add Interaction Policy Service
- Keep UI minimal by default

### P1: Backend conversation persistence

- Add ConversationSession and ConversationTurn models
- Persist user messages, agent messages, mini surfaces, observations
- Load session by channel/web demo id

### P2: Contract runtime v0.1

- Load `examples/interaction-contracts/contract-review.roam.yaml`
- Match a small number of trigger conditions
- Show matched contract in inspector

### P3: Rich surface escalation

- Add side drawer for full review preview
- Keep `/artifacts/[id]` for full artifact page
- Do not show rich surface by default

### P4: Telegram real mapping

- Render MiniIssueCard / ApprovalCard into Telegram-compatible messages
- Callback -> UIInteractionEvent -> conversation observation
- URL button -> artifact page

### P5: File input improvement

- Add `.md` / `.txt` upload
- Add `.docx` extraction if easy
- Keep sample contract as default fixture

---

## 8. Suggested Codex Prompt

```text
Read docs/V0_4_INTERACTION_RUNTIME_ROADMAP.md and docs/INTERACTION_MINIMALISM_AND_AGENT_AUTONOMY.md.

Implement the next small version of Tilo as an interaction runtime, not just a demo.

Do not redesign the product into a heavy dashboard.
Keep the main interface conversation-first.

Implement in this order:
1. Generalize the demo chat turn model into reusable conversation event types.
2. Add a Mini Surface Registry for MiniIssueCard, MiniApprovalCard, MiniRevisionPreview, MiniMemoryCard, MiniToolPreview, MiniChoiceCard.
3. Add a lightweight InteractionPolicyService that decides: no_ui, mini_surface, rich_surface_link, or ask_text.
4. Use the policy service in the contract review demo instead of hardcoding every UI trigger in the component.
5. Keep UI minimal: show only one decision/info mini surface at a time by default.
6. Add explicit memory lifecycle states: candidate proposed -> confirmed -> saved.
7. Add rich surface escalation via Open Full Review, preferably drawer first and artifact page second.
8. Move developer inspector into hidden debug/drawer mode.
9. Preserve deterministic and LLM modes.
10. Preserve UIInteractionEvent persistence and Telegram adapter foundation.

Definition of done:
Tilo should feel like a reusable framework for adding UI interactions to agent loops only when human decision-making needs it.
```

---

## 9. Definition of Done

v0.4 is ready when:

1. The demo still feels simple and conversation-first.
2. Mini surfaces are reusable components, not demo-only code.
3. UI trigger decisions are handled by a policy layer.
4. User clicks become durable observations.
5. Memory lifecycle is visible and controlled.
6. Rich surfaces are available but not default.
7. The same mental model can apply to Telegram, web, and future channels.
8. Developers can understand how to build their own agent app with Tilo.
