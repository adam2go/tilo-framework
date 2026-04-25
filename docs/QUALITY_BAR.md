# Quality Bar

This document defines the quality bar for Tilo Framework.

Tilo should be treated as a serious open-source framework, not a one-off prototype.

## 1. General Quality Principles

Every meaningful feature should be:

- grounded in the product loop
- modular
- typed where possible
- observable through trace or UI
- safe by default
- documented when it affects architecture
- testable

## 2. Feature Completion Checklist

A feature is not done until the following questions are answered:

### Product Fit

- Does it support Agent, Memory, Skill, Tool, Artifact, or Inbox?
- Does it preserve the core loop?
- Is it useful beyond one hardcoded demo?

### Architecture

- Is business logic in services rather than route handlers?
- Are domain models explicit?
- Are JSON blobs used only where flexibility is needed?
- Does it avoid unnecessary dependencies?

### API

- Does it have clear request/response schemas?
- Does it return meaningful errors?
- Does it avoid leaking internal implementation details?

### Frontend

- Is user-facing state visible?
- Does it avoid raw JSON dumps unless in debug views?
- Does it present artifacts as product outputs?
- Does it show confirmations clearly?

### Memory

- Are memory writes explicit?
- Are generated memories unconfirmed by default?
- Can users inspect and modify memory?

### Security

- Are tool permissions respected?
- Are high-risk actions confirmation-gated?
- Are secrets protected?
- Is trace output safe?

### Tests

- Is there at least a practical test or manual verification path?
- Does it avoid breaking the end-to-end demo loop?

## 3. Minimum Testing Expectations

v0.1 should include tests for:

- health check
- creating task
- creating run
- creating artifact
- listing/rendering artifact data
- creating confirmation
- approving/rejecting confirmation
- creating memory candidate
- confirming memory
- recalling confirmed memory
- invoking a mock tool

## 4. Definition of Done for a Pull Request

A PR should be considered ready when:

1. It has a clear purpose.
2. It does not violate AGENTS.md or PROJECT_CONSTITUTION.md.
3. It does not break local startup.
4. It does not bypass core services.
5. It does not introduce hidden secrets.
6. It updates docs if architecture changes.
7. It includes tests or a manual verification note.

## 5. User-facing Quality Bar

Tilo should feel credible for professional users.

Avoid:

- awkward toy UI
- unclear buttons
- vague statuses
- endless spinners
- chat-only interactions
- broken empty states

Prefer:

- clear task state
- useful progress indicators
- structured artifact panels
- obvious confirmation actions
- transparent memory cards
- readable trace steps

## 6. Code Quality Bar

Avoid:

- giant files
- deeply nested logic
- duplicated demo logic
- magic constants everywhere
- untyped request bodies
- silent exception swallowing
- vague variable names

Prefer:

- small focused services
- typed schemas
- explicit domain naming
- clear error handling
- reusable components
- simple abstractions

## 7. Framework Integrity Bar

Demos must not bypass framework primitives.

For example, the Contract Review demo should still create:

- Task
- Run
- TraceStep
- Artifact
- Confirmation when needed
- Memory candidates

If a demo only renders a prebuilt page, it fails the framework integrity bar.
