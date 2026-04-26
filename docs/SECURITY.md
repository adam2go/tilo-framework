# Security and Safety Guidelines

This document defines basic security and safety rules for Tilo Framework.

## 1. Security Philosophy

Tilo agents may eventually access files, APIs, browsers, databases, SaaS tools, and communication systems.

This makes safety a core architecture concern, not a later feature.

## 2. Permission Levels

Every tool must declare a permission level:

| Level | Meaning | Example |
|---|---|---|
| low | read-only or harmless action | mock search, read local sample data |
| medium | writes internal data or changes artifacts | update memory, edit artifact |
| high | external or risky action | send email, delete file, submit approval, run shell command |

High-risk actions must require Confirmation before execution.

## 3. Confirmation Gates

The following actions must not execute silently:

- sending external messages
- deleting files
- modifying external systems
- running shell commands
- making purchases or payments
- submitting approvals
- changing production configuration
- using secrets

For v0.1, these actions should be mocked or guarded.

## 4. Secrets

Secrets must:

- be stored in environment variables or a future vault abstraction
- never be committed to Git
- never be exposed to frontend code
- never be shown in trace output
- never be included in artifact content

## 5. Trace Safety

Trace should show execution summaries, not hidden model reasoning.

Trace may include:

- tool name
- safe input summary
- safe output summary
- status
- timestamps

Trace must not include:

- API keys
- passwords
- raw private credentials
- hidden chain-of-thought
- unredacted sensitive payloads

## 6. Prompt Injection

External content should be treated as untrusted.

External content includes:

- webpages
- uploaded documents
- emails
- chat logs
- CRM records
- browser results

Agents should not obey instructions embedded in untrusted content that attempt to override system or developer instructions.

For v0.1, document this risk and keep external actions mocked or confirmation-gated.

## 7. Memory Safety

Do not store secrets as memory.

Memory candidates extracted from documents should default to unconfirmed.

Users should be able to inspect, edit, and delete memory.

## 8. Tool Safety

All tools should go through ToolRegistry.

Tool calls should be logged.

High-risk tools should return a pending Confirmation instead of directly executing.

## 9. v0.1 Safety Requirements

v0.1 must include:

1. permission_level on tools
2. confirmation records
3. trace logging
4. secret handling via env variables
5. documented prompt injection risks
6. no real destructive external actions

## 10. Do Not Do

Do not:

- execute arbitrary shell commands without confirmation and sandboxing
- expose secrets in frontend
- treat uploaded documents as trusted instructions
- store hidden chain-of-thought
- silently execute external actions
- auto-install untrusted skills

## 11. v0.2 Safety Additions

v0.2 adds enforcement-oriented safety primitives:

- `TraceSanitizer` redacts common secret keys, credential markers, and hidden reasoning markers before trace persistence.
- `RunStateMachine` prevents arbitrary status strings and avoids runs stuck in `running` after failures.
- `ToolInvocation` persists every tool call with input, output, status, permission level, and optional `confirmation_id`.
- High-risk tools create pending confirmations and pending tool invocations instead of executing immediately.
- Mock tool responses include `mock: true` so demo data is not presented as real external data.
- Skill candidates require review and must not automatically modify approved skills or prompts.

## 12. ROAM Interaction Safety

ROAM component actions are not local-only UI state. They create durable `UIInteractionEvent` records and then call backend APIs when needed.

Safety rules:

- Interaction payloads must be sanitized before persistence.
- High-risk component actions must still create or use durable `Confirmation` records.
- Component actions must not execute external tools directly from the browser.
- Memory-related component actions should create reviewable memory candidates or call Memory confirmation APIs.
- UI observations may inform future runs, but they must not become trusted long-term memory without the memory review workflow.
