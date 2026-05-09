# Contributing to Tilo Framework

Thank you for your interest in contributing to Tilo Framework.

Tilo aims to become a serious open-source framework for AI-native product runtimes. Contributions should preserve the project direction and quality bar.

## 1. Read Before Contributing

Before making significant changes, read:

1. `README.md`
2. `AGENTS.md`
3. `docs/PROJECT_CONSTITUTION.md`
4. `docs/AI_NATIVE_FRAMEWORK_PRINCIPLES.md`
5. `docs/ARCHITECTURE.md`
6. `docs/ROAM_LOOP.md`
7. `docs/QUALITY_BAR.md`
8. Relevant runtime/module docs

## 2. Project Direction

Tilo is not a chatbot wrapper.

Tilo focuses on:

- long-term memory
- real task execution
- structured artifacts
- human confirmation
- traceability
- reusable skills

## 3. Contribution Guidelines

Good contributions:

- strengthen the core product loop
- improve architecture clarity
- make memory more reliable and transparent
- make artifacts more useful and interactive
- improve safety and confirmation mechanisms
- improve developer experience
- add tests or documentation

Avoid contributions that:

- turn Tilo into a generic chatbot
- bypass Task/Run/Artifact/Memory/Confirmation primitives
- add large dependencies without strong reason
- implement demo-only logic that cannot generalize
- expose secrets or hidden reasoning

## 4. Pull Request Expectations

A good PR should include:

- clear description
- reason for change
- affected modules
- testing notes
- screenshots if UI changes
- documentation updates if architecture changes

## 5. Commit Style

Recommended prefixes:

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

## 6. Review Checklist

Before submitting, check:

- Does it preserve the core loop?
- Does it use explicit domain models?
- Does it avoid demo-only shortcuts?
- Does it keep artifacts schema-driven?
- Does it keep memory inspectable?
- Does it respect confirmation gates?
- Does it avoid exposing secrets?
- Does it include tests or a verification path?

## 7. Security Issues

Please do not open public issues for sensitive security vulnerabilities. Use a private disclosure channel when available.

Until a formal security policy is published, avoid sharing exploit details publicly.
