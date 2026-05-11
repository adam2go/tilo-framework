# Tilo Priority Action Plan

This plan turns the v1.0 direction into concrete open-source priorities.

The goal is not to add more concepts. The goal is to make Tilo easier to understand, easier to run, easier to integrate, and easier to maintain.

---

## Principle

Tilo should stay:

```text
AI-native product runtime, not SaaS plus AI.
```

Protocol support, channels, tools, and UI components are useful only if they strengthen the core loop:

```text
Goal -> Surface -> Decision -> Action -> Memory
```

---

## P0: Make the project immediately understandable and runnable

### P0-1: README first screen conversion

Status: in progress.

Required direction:

- First screen should explain what Tilo is in less than 30 seconds.
- The first message should not be a long framework comparison.
- The first differentiators should be concrete:
  - confirmed memory;
  - backend-owned action semantics.
- ROAM can remain in docs, but it should not hide the practical value.

Target README structure:

```text
One-line positioning
Quick local command
What is Tilo?
What's actually new?
Quick Start
Integration modes
Build an app
Runtime model
Roadmap focus
```

Acceptance criteria:

- A new developer can answer: "When would I use Tilo?"
- A new developer can run the demo without reading multiple docs.
- The README foregrounds confirmed memory and Artifact Action Runtime.

---

### P0-2: Demo verification should never rot

Status: partially implemented.

Required direction:

- `scripts/verify_local_demo.sh` must stay aligned with the primary `/demo` route.
- CI should validate backend tests, frontend build, app validation, and local demo verification where feasible.
- README should show expected verification output.

Acceptance criteria:

- `bash scripts/verify_local_demo.sh` checks `/demo`, not legacy routes.
- GitHub Actions includes a local demo verification job.
- Deterministic mode does not require an API key.

---

### P0-3: Make the real differentiators obvious

Status: in progress.

README and docs should clearly state:

1. **Confirmed memory**

```text
Observation -> Memory Candidate -> Human Confirmation -> Confirmed Memory
```

Why it matters:

- avoids uncontrolled memory writes;
- keeps users in control;
- supports auditability;
- reduces evaluation pollution.

2. **Backend-owned action semantics**

```text
User action -> ArtifactActionRuntime -> UIInteractionEvent -> ConversationTurn(observation) -> safe side effect
```

Why it matters:

- avoids frontend-owned business logic;
- keeps channels consistent;
- supports audit and replay;
- makes the project a framework, not a demo.

---

## P1: Prove the framework abstraction

### P1-1: Run a second complete example app

Priority example:

```text
sales-followup-agent
```

Rule:

```text
Do not change framework code first.
```

If the second app needs framework changes, document the abstraction gap before changing the framework.

Required output:

```text
examples/apps/sales-followup-agent/POSTMORTEM.md
```

The postmortem should answer:

- Which abstractions worked unchanged?
- Which abstractions felt contract-review-specific?
- Which policy or artifact gaps appeared?
- What should be fixed in the framework before adding more examples?

---

### P1-2: Clarify Skill / Tool / MCP boundaries

Current risk:

```text
Skill, Tool, and MCP may become overlapping concepts.
```

Recommended decision:

```text
Tool = executable capability
MCP = external tool/server adapter protocol
Skill = scenario bundle of prompts, tools, surfaces, policies, and fixtures
```

Skill should be a composition unit, not a competing runtime primitive.

Required output:

```text
docs/SKILL_TOOL_MCP_BOUNDARIES.md
```

Then update `docs/SKILLS.md` accordingly.

---

### P1-3: Add baseline runtime evals

Tilo's philosophy should be measurable.

Start with three metrics:

```text
surface_render_rate
artifact_action_completion_rate
memory_candidate_acceptance_rate
```

Suggested output:

```text
evals/baseline_report.md
```

The report should run on the contract-review demo first.

---

### P1-4: Split ArtifactSpec blocks into core and extension tiers

Current risk:

```text
Too many block types become a renderer maintenance burden.
```

Core blocks should be small and stable:

```text
markdown
table
form
approval_card
risk_panel
metric
list
```

Everything else should be an extension block with schema support and fallback rendering.

Required output:

- update `docs/ARTIFACTS.md`;
- update frontend renderer registry;
- add fallback renderer for extension blocks.

---

### P1-5: Decide InteractionPolicy expression boundary

Do not let policy become an unclear half-rule-engine.

Recommended direction:

```text
Keep policy as a coarse routing layer.
Use code hooks for complex decisions.
```

Potential syntax:

```yaml
when:
  callable: my_module.complex_check
```

Required output:

- document the boundary in `docs/INTERACTION_POLICY.md`;
- optionally add callable hook support;
- avoid pretending YAML policy can express every business rule.

---

## P2: Community readiness and internal simplification

### P2-1: Contributing path

Improve `CONTRIBUTING.md` and create good-first-issue candidates.

Do this after README and demo conversion are stable.

---

### P2-2: Service simplification

Do not mechanically merge everything into three giant services.

Instead:

- remove thin wrappers;
- keep true runtime boundaries;
- name services by stable concepts;
- document service ownership in `docs/ARCHITECTURE.md`.

Target clarity:

```text
Conversation runtime
Artifact runtime
Artifact action runtime
Memory lifecycle
App manifest / policy loading
```

---

### P2-3: Confirmed memory story

Tilo's most shareable idea is confirmed memory.

Potential article:

```text
Why your AI agent's memory is broken — and how confirmed memory fixes it
```

Do this after the demo and README clearly show the concept.

---

## What not to do before the framework is clearer

Avoid:

- adding new domain objects;
- adding new public demo routes;
- adding new channels before the runtime contract is stable;
- chasing protocol hype before Tilo's own core loop is proven;
- building a plugin marketplace;
- expanding docs with more new terms;
- keeping dead demo code for compatibility.

---

## Current immediate implementation checklist

1. README first screen: done / keep refining.
2. Chinese README parity: done / keep refining.
3. CI local demo verification: next.
4. Remove remaining dead demo code: continue with repository search and build validation.
5. Add Skill / Tool / MCP decision doc.
6. Add ArtifactSpec core/extension doc.
7. Add baseline eval metrics.
8. Validate sales-followup-agent as a real second app.
