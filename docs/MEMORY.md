# Memory System

This document defines the memory principles and implementation requirements for Tilo Framework.

## 1. Memory Philosophy

Tilo memory is not chat history.

Memory is a structured, inspectable, user-confirmable long-term context layer that helps agents understand users, projects, decisions, and reusable procedures over time.

## 2. Memory Types

Tilo v0.1 should support these memory types:

| Type | Description | Example |
|---|---|---|
| user_preference | User-specific preferences | The user prefers concise, conclusion-first product documents. |
| project_fact | Stable project context | The current project is building an AI-native SaaS agent framework. |
| decision | A decision made by the user or team | The project will use Apache 2.0. |
| task_experience | Lessons from a completed task | Contract review artifacts should include risk cards. |
| procedural | Reusable method or process | For competitor research, include market map, table, and opportunity summary. |
| temporary | Short-lived context | User is currently testing a local demo. |

## 3. Memory Fields

Each memory should include:

- id
- workspace_id
- project_id nullable
- user_id nullable
- type
- content
- source_type
- source_id
- confidence
- is_confirmed
- expires_at nullable
- embedding nullable
- created_at
- updated_at

## 4. Memory Scope

Memory should be scoped.

Recommended scopes:

- Global user memory
- Workspace memory
- Project memory
- Task/run memory
- Skill/procedural memory

Recall should prefer the most relevant scope:

```text
current project -> workspace -> user global
```

## 5. Memory Lifecycle

```text
Raw interaction
  -> Candidate extraction
  -> Classification
  -> Confidence scoring
  -> Conflict detection
  -> User confirmation
  -> Durable memory write
  -> Future recall
```

For v0.1, conflict detection can be simple, but the system should keep the field and design space.

## 6. Candidate Extraction

After each run, generate memory candidates from:

- user input
- final task result
- artifact content
- confirmation decisions
- user edits

Memory candidates must default to:

```text
is_confirmed = false
```

Do not silently store every model-generated statement as confirmed memory.

## 7. Confirmation

Users should be able to approve, edit, or reject memory candidates.

Confirmed memories can be used in future recall.

Rejected memories should not be recalled.

## 8. Recall

Memory recall should support:

- keyword filtering
- type filtering
- scope filtering
- semantic search when embeddings are available

For v0.1, a simple hybrid recall is acceptable:

1. Filter by workspace/project.
2. Filter confirmed memories.
3. Search by type and keyword.
4. Optionally use vector similarity.

## 9. Memory Transparency

The frontend should include a Memory Panel.

Users should be able to see:

- what the agent remembers
- why it was remembered
- where it came from
- whether it is confirmed
- when it was created

Users should be able to edit or delete memories.

## 10. Memory Safety

Do not store sensitive secrets as memory.

Do not store API keys, passwords, tokens, or private credentials.

If external documents contain untrusted content, treat extracted memory as unconfirmed until reviewed.

## 11. v0.1 Minimum Requirements

v0.1 is acceptable if:

1. Memory records can be created.
2. Memory records can be listed and edited.
3. Memory candidates are created after a task run.
4. User can confirm memory candidates.
5. Confirmed memories can be recalled in a future run.
6. Memory is visible in the frontend.

## 12. Do Not Do

Do not:

- implement memory as only chat transcripts
- automatically trust all extracted facts
- hide memory from the user
- make memory impossible to edit
- store hidden chain-of-thought
- store secrets
