# Development Workflow for Coding Agents

This document defines how Codex, Claude Code, and other coding agents should work on Tilo Framework.

## 1. Required Reading Order

Before coding, read these files in order:

1. `README.md`
2. `AGENTS.md`
3. `docs/PRODUCT_PRINCIPLES.md`
4. `docs/CODEX_SPEC.md`
5. `docs/ARCHITECTURE.md`
6. `docs/MEMORY.md`
7. `docs/ARTIFACTS.md`
8. `docs/SKILLS.md`
9. `docs/UI_UX.md`
10. `docs/TECH_STACK.md`
11. `docs/SECURITY.md`
12. `docs/DEVELOPMENT_WORKFLOW.md`

If there is any conflict, follow this priority:

```text
AGENTS.md > PRODUCT_PRINCIPLES.md > CODEX_SPEC.md > architecture/module docs > implementation convenience
```

## 2. Implementation Strategy

Implement vertical slices before polishing individual layers.

A vertical slice means:

```text
API -> database -> runtime service -> artifact/confirmation/memory -> frontend display
```

Do not build disconnected mock pages that do not use backend primitives.

## 3. First Development Milestone

The first milestone should prove:

1. backend starts
2. frontend starts
3. user can send a message
4. task is created
5. run is created
6. trace is recorded
7. artifact is generated
8. artifact renders in frontend
9. confirmation appears in inbox
10. memory candidate is created

## 4. Branch and Commit Style

If working directly on main is allowed, keep commits small and meaningful.

Recommended commit message prefixes:

- `docs:`
- `backend:`
- `frontend:`
- `runtime:`
- `memory:`
- `artifact:`
- `inbox:`
- `skill:`
- `tool:`
- `demo:`
- `test:`

## 5. Coding Agent Behavior

When coding:

- inspect existing files before editing
- avoid overwriting user changes
- prefer incremental changes
- run tests or type checks when available
- update docs when architecture changes
- preserve the product loop

## 6. When Unsure

If a requirement is ambiguous, choose the option that best preserves:

```text
Long-term memory + real execution + human confirmation + artifact delivery
```

Do not default to a plain chatbot implementation.

## 7. Refactoring Existing Code

If existing code violates core architecture, refactor it.

Examples:

- runtime logic inside one endpoint -> move to services
- artifact stored as plain Markdown -> convert to schema
- memory stored as raw chat logs -> create structured memory records
- confirmations only in UI state -> persist confirmation records

## 8. Testing Before Completion

Before declaring a task complete, verify:

- backend boots
- frontend boots
- key API endpoint works
- no obvious TypeScript/Python syntax errors
- demo flow still works

## 9. Definition of Good Work

Good work in this repo means:

- the product direction is preserved
- the architecture remains modular
- users can see value quickly
- artifacts are structured
- memory is inspectable
- confirmations are durable
- traces are safe and useful

## 10. Anti-patterns

Avoid:

- huge unstructured files
- one-off demo logic
- hardcoded data everywhere
- raw JSON UI dumps
- hidden confirmations
- memory as chat transcript only
- unnecessary infrastructure complexity
- pretending mock tools are production tools
