# Tilo Demos

Three end-to-end demos showing the full Tilo loop:

```
Goal → Spec → Interactive UI → Decision → Memory
```

Each demo runs against the **3D Agent Canvas** at `http://localhost:4001/canvas`.
Pick the one that matches your role and watch the agent generate an interactive
artifact instead of a chat reply.

| Demo | Best for | Mode | Length |
|---|---|---|---|
| [PR Review](#pr-review) | engineers evaluating an AI code-review workflow | LLM | ~53s |
| [SF Trip](#sf-trip) | first-time visitors — runs **without any LLM key** | offline fixture | ~82s |
| [Sales Briefing](#sales-briefing) | revenue / ops users seeing structured outputs + confirmation | LLM | ~68s |

> All three videos live in the [`v0.1-demos` GitHub Release][release]. Permanent
> URLs — safe to embed anywhere.

[release]: https://github.com/adam2go/tilo-framework/releases/tag/v0.1-demos

---

## PR Review

**Goal sent to the agent**

> Review pull request #482 from the `feat/session-auth` branch. It replaces the
> JWT auth middleware with Redis-backed sessions across 5 files (+312 / −187 LOC).
> Flag risky changes, list verification items, and decide whether to approve the
> merge.

**What you'll see**

- A PR summary card + two real `diff` blocks (JWT → Redis session) side by side
- A 5-row findings table (security / tests / docs / compat)
- A reviewer-verification `checklist` — items the human actually has to confirm
- A high-risk `confirmation` gate before the agent merges
- A `memory_card` capturing the reviewer's review style (e.g. *"blocks merge until error-path tests exist"*)

**Watch**: [`canvas-pr-review.mp4`](https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-pr-review.mp4) (42 MB)

---

## SF Trip

**Goal sent to the agent**

> Plan a 3-day San Francisco weekend trip for 2 people in late September. Mix
> iconic landmarks, local food, and a Napa day-trip. Budget around $1500 per
> person excluding flights.

**What you'll see**

- A trip-overview card + day-by-day `timeline`
- An interactive packing `checklist` and hotel comparison `table`
- Budget breakdown via `metric` blocks
- A `rating` for the user to score the plan + a `memory_card` with the inferred preferences

**Why this demo is special**: it runs from a **baked-in fixture**, so it works
on a fresh clone with `LLM_ENABLED=false`. Use it to evaluate Tilo before
configuring any model provider.

**Watch**: [`canvas-sf-trip.mp4`](https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-sf-trip.mp4) (49 MB)

---

## Sales Briefing

**Goal sent to the agent**

> Generate a sales follow-up briefing for this week — top accounts, pending
> decisions, recommended next actions.

**What you'll see**

- Three pipeline `metric` cards (hot accounts, projected pipeline, pending decisions)
- An action `checklist` with stale-day callouts
- A draft outbound email rendered as a `card`
- A `confirmation` block — sending the email is gated on explicit human approval
- A `memory_card` learning that the user wants gated approval before any outbound action

**Watch**: [`canvas-sales-briefing.mp4`](https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-sales-briefing.mp4) (36 MB)

---

## Run them yourself

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
make install   # pip install + pnpm install
make dev       # backend :8000 + frontend :4001
```

Open `http://localhost:4001/canvas` and click one of the three sample buttons
at the bottom. See the [main README](../../README.md) for LLM provider setup.
