# Sales Follow-up Agent Postmortem

This example was checked as a second app to validate that Tilo is a reusable framework, not a contract-review-only demo.

## What Worked Unchanged

- `app.yaml` loads through the same `AgentAppLoader` path as Contract Review.
- `interaction.policy.yaml` validates with the same policy service.
- Sample fixture path validation works without new framework code.
- Mini surface declarations reuse existing `MiniChoiceCard` and `MiniMemoryCard`.
- Rich surface declaration works as a named intent (`FollowupDraftArtifact`) without needing a polished public demo route.
- Deterministic local mode does not require an API key.

## What Still Feels Contract-review-specific

- The polished `/demo` flow is intentionally focused on Contract Review.
- The deterministic artifact generator is strongest for `contract_review`.
- Some rich artifact copy and examples still assume risk review and revisions.
- The current frontend reference surface set is better at approvals and risks than follow-up drafting.

## Policy or Artifact Gaps

- Sales follow-up needs reusable blocks for draft review, recipient context, and tone choice. Those should be extension blocks with fallback rendering first, not bespoke hardcoded panels.
- InteractionPolicy is sufficient for coarse routing (`followup_tone_needed`, `open_full_review`, `user_preference_detected`) but should not encode CRM scoring or send-time business rules.
- Tool execution for real outbound email should remain a high-risk Tool behind confirmation.

## Framework Fixes Before More Examples

1. Keep ArtifactSpec core small and make extension fallback rendering reliable.
2. Add deterministic evals that verify surface rendering, artifact action completion, and memory confirmation.
3. Document Skill / Tool / MCP boundaries so sales follow-up does not become a mix of prompts, protocol adapters, and hidden business logic.
4. Add richer app-level fixture examples only after the runtime contract remains stable across Contract Review and Sales Follow-up.

## Current Status

The app validates with:

```bash
python scripts/validate_app.py examples/apps/sales-followup-agent
```

No framework core changes were required to load or validate this app.
