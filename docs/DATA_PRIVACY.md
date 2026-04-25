# Data and Privacy Guidelines

This document defines data and privacy expectations for Tilo Framework.

## 1. Data Philosophy

Tilo is a memory-native framework. This makes data handling especially important.

Users must be able to understand and control what the system stores about them, their projects, and their decisions.

## 2. Data Categories

Tilo may store:

- user profile data
- workspace/project metadata
- agent definitions
- task inputs
- run summaries
- trace steps
- memory records
- artifacts
- confirmation decisions
- skill definitions
- tool configs

## 3. Sensitive Data

Sensitive data includes:

- API keys
- passwords
- access tokens
- private credentials
- financial information
- legal documents
- HR records
- private customer records
- personal identifiers

v0.1 should avoid unnecessary sensitive data collection.

## 4. Memory Privacy

Memory must be transparent.

Users should be able to:

- view memories
- edit memories
- delete memories
- confirm or reject memory candidates

Do not silently convert every interaction into permanent memory.

## 5. Default Memory Policy

Generated memory candidates should default to unconfirmed.

Only confirmed memories should be used for future personalized recall.

Temporary context should have expiration support.

## 6. Artifact Privacy

Artifacts may contain sensitive work outputs.

Artifacts should be scoped to workspace/project.

Do not make artifacts public by default.

## 7. Trace Privacy

Trace should help users understand execution without exposing sensitive internals.

Do not store:

- hidden chain-of-thought
- secrets
- raw credentials
- unnecessary full payloads from external tools

## 8. Tool Config Privacy

Tool configs may include credentials in the future.

For v0.1:

- keep credentials in environment variables
- do not store secrets in plain JSON configs
- do not expose secrets to frontend

## 9. Deletion

Users should eventually be able to delete:

- memories
- artifacts
- tasks/runs
- projects

For v0.1, at minimum support memory deletion.

## 10. Future Requirements

Future versions should consider:

- export user data
- delete workspace data
- secret vault
- audit logs
- encryption at rest
- per-project memory isolation
- workspace-level access controls

## 11. v0.1 Minimum Requirements

v0.1 must:

1. avoid storing secrets
2. keep memory inspectable
3. keep memory confirmable
4. allow memory deletion
5. avoid public artifact sharing by default
6. avoid hidden reasoning storage
