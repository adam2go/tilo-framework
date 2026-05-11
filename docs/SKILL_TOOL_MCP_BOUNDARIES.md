# Skill / Tool / MCP Boundaries

Tilo is protocol-aware, not protocol-led.

The core runtime is:

```text
Goal -> Surface -> Decision -> Action -> Memory
```

Protocols and adapters are useful only when they strengthen that loop. MCP, AG-UI, ACP, A2A, and channel APIs should remain boundary layers. They must not define Tilo's product runtime.

## Definitions

### Tool

A Tool is an executable capability.

Examples:

- create a calendar draft;
- query a CRM record;
- generate a PDF;
- call an internal risk scoring service;
- send an email after confirmation.

Tools must declare permission level and execution semantics. High-risk tools require confirmation. Tool calls must be logged and must not expose secrets.

### MCP

MCP is an external tool/server adapter protocol.

MCP can expose tools to Tilo or let Tilo call external capabilities through a standard boundary. MCP is not the agent app, not the artifact contract, and not the memory lifecycle.

Use MCP for:

- connecting to external tool servers;
- adapting third-party capabilities;
- keeping tool transport separate from product runtime semantics.

Do not use MCP to define:

- when UI should appear;
- how artifact actions mutate state;
- what becomes memory;
- what the user's product workflow means.

### Skill

A Skill is a scenario bundle.

It can include:

- prompts and instructions;
- tool requirements;
- surface preferences;
- app manifest and interaction policy conventions;
- fixtures and examples;
- artifact templates;
- evaluation notes;
- best practices learned from previous runs.

A skill composes runtime pieces. It is not a competing runtime primitive and should not execute arbitrary code by itself.

## Ownership Boundaries

```text
Tool = executable capability
MCP = external tool/server adapter protocol
Skill = scenario bundle of prompts, tools, surfaces, policies, fixtures, and best practices
```

The Artifact Action Runtime owns user action semantics:

```text
User action -> ArtifactActionRuntime -> UIInteractionEvent -> ConversationTurn(observation) -> safe side effect
```

Tools may be invoked by that runtime. MCP may adapt those tools. Skills may recommend which tools and surfaces fit a scenario. None of them should bypass confirmed memory or backend-owned actions.

## Review Checklist

Before adding a new protocol, tool, or skill, ask:

1. Does this strengthen `Goal -> Surface -> Decision -> Action -> Memory`?
2. Is the executable behavior a Tool?
3. Is the external transport an adapter such as MCP?
4. Is the reusable scenario knowledge a Skill?
5. Does a user action still flow through Artifact Action Runtime?
6. Does memory remain candidate-first and user-confirmed?
