# Code Review Agent

A Tilo agent app that reviews pull request diffs for bugs, security vulnerabilities, and performance issues. It surfaces high-severity findings as focused decision cards and requires human approval before flagging a PR as merge-ready.

## What it demonstrates

- **Different domain** from `contract-review-agent` (dev tooling vs. legal)
- **Risk-gated merge approval**: security and bug findings route through `MiniIssueCard` for human decision
- **Developer-facing memory**: captures reviewer preferences (e.g., "always flag missing rate limiting")
- **AIP `diff` block type**: renders code changes inline in `CodeReviewArtifact`

## Interaction flow

```
User submits PR diff
  → Agent scans for issues
  → High severity (security / bug)  → MiniIssueCard (request_approval)
  → Medium / low severity           → no_ui (autonomous annotation)
  → User opens full review          → CodeReviewArtifact (escalate_to_rich)
  → User approves merge             → MiniApprovalCard (present_result)
  → Reviewer preference detected    → memory candidate
```

## Sample input

The included fixture (`examples/fixtures/code-review-sample.md`) contains a realistic PR diff for an authentication module refactor. It has intentional issues across three severity levels:

| Severity | Issue |
|---|---|
| High | SQL query built from unsanitised user input |
| High | JWT secret falls back to a weak hardcoded placeholder |
| Medium | No rate limiting on the login endpoint |
| Medium | N+1 query pattern in the user-lookup path |
| Low | Unused import (`logging`) |
| Low | Missing type annotation on `get_user()` return value |

## Validate

```bash
python scripts/validate_app.py examples/apps/code-review-agent
```

## Local API

```bash
# Load the app
curl http://localhost:8000/api/apps/code-review-agent

# Start a review session
curl -X POST http://localhost:8000/api/conversations \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"code-review-agent","workspace_id":"<workspace_id>","channel":"web"}'

# Submit the PR diff for review
curl -X POST http://localhost:8000/api/conversations/<session_id>/messages \
  -H 'Content-Type: application/json' \
  -d '{"content":"Review the auth module refactor PR for security and correctness.","attachments":[]}'
```
