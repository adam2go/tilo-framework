# AI-native Framework Principles

Tilo is not a traditional SaaS product with AI features added on top.

Tilo is a framework for building AI-native product experiences.

This positioning is foundational and should guide product design, runtime architecture, demo design, documentation, and implementation reviews.

---

## Core Positioning

Tilo should be understood as:

```text
A framework for AI-native SaaS agents.
```

Not:

```text
A SaaS admin console with AI chat added.
```

The value of Tilo is that the agent runtime can decide when to render focused interfaces, observe human decisions, execute safe actions, and remember confirmed learning.

---

## What AI-native Means

A Tilo app should feel like this:

```text
User describes a goal
-> agent renders the next useful surface
-> user makes a decision
-> runtime records the observation
-> action executes safely
-> confirmed learning becomes memory
```

It should not feel like this:

```text
User opens a dashboard
-> searches for the right feature
-> fills forms
-> clicks through panels
-> AI summarizes the page
```

---

## Product Principle

```text
Simple surface. Powerful runtime. Inspectable internals.
```

The default user experience should be minimal and focused. Runtime details should be available only when needed.

This means:

- the public demo should not look like an admin backend;
- inspectors should be hidden by default;
- traces, observations, policies, and memory lifecycle should be explainable on demand;
- users should feel the product outcome before seeing the machinery;
- developer mode should reveal details without turning the page into a dashboard.

---

## Runtime Principle

```text
Frontend renders intent. Backend owns action semantics.
```

Frontend components should not own the real meaning of actions. The backend runtime should interpret actions, validate them, create durable observations, execute safe side effects, and return structured results.

---

## ROAM Principle

Tilo's core loop is:

```text
Render -> Observe -> Act -> Memorize
```

A feature should strengthen this loop. If it does not, it should be questioned before entering the core framework.

---

## Anti-patterns

Avoid:

- SaaS dashboard regression;
- AI sidebar thinking;
- always-visible debug internals;
- frontend-owned action semantics;
- adding panels and settings just because they are easy to build;
- forcing users to understand the framework before they feel the product value.

---

## Review Checklist

Before merging major changes, ask:

1. Does this make Tilo more AI-native, or does it recreate traditional SaaS UI?
2. Is the user experience goal-first rather than feature-first?
3. Does UI appear only when it helps the user's decision?
4. Are runtime details hidden by default and inspectable on demand?
5. Does the backend own action semantics?
6. Does the change strengthen ROAM?
7. Does memory remain confirmation-based?
8. Can another channel reuse the same runtime behavior?

If the first answer is unclear, pause and redesign.
