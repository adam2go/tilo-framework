#!/usr/bin/env bash
set -u

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf '✓ %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf '✗ %s\n  next: %s\n' "$1" "$2" >&2
}

need_command() {
  command -v "$1" >/dev/null 2>&1
}

http_get() {
  curl -fsS --max-time 8 "$1"
}

http_post() {
  curl -fsS --max-time 90 -H 'Content-Type: application/json' -X POST "$1" -d "$2"
}

printf 'Tilo local demo verification\n'
printf 'backend:  %s\n' "$BACKEND_URL"
printf 'frontend: %s\n\n' "$FRONTEND_URL"

if need_command docker; then
  pass "docker command available"
else
  fail "docker command unavailable" "Install Docker Desktop, then run: docker compose up --build"
fi

if ! need_command curl; then
  fail "curl unavailable" "Install curl and rerun this script."
  exit 1
fi

if ! need_command python3; then
  fail "python3 unavailable" "Install Python 3 and rerun this script."
  exit 1
fi

health_payload="$(http_get "$BACKEND_URL/api/health" 2>/dev/null || true)"
if [ "$health_payload" = '{"status":"ok"}' ]; then
  pass "backend health ok"
else
  fail "backend health failed" "Run: docker compose up --build"
fi

frontend_status="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 "$FRONTEND_URL/demo" 2>/dev/null || true)"
if [ "$frontend_status" = "200" ]; then
  pass "frontend /demo route ok"
else
  fail "frontend /demo route unavailable" "Check the frontend container logs, or run: docker compose up --build frontend"
fi

legacy_frontend_status="$(curl -L -sS -o /dev/null -w '%{http_code}' --max-time 8 "$FRONTEND_URL/demo/telegram" 2>/dev/null || true)"
if [ "$legacy_frontend_status" = "200" ]; then
  pass "compatibility redirect /demo/telegram -> /demo ok"
else
  fail "compatibility redirect /demo/telegram unavailable" "Keep /demo/telegram redirecting to /demo for old links."
fi

apps_payload="$(http_get "$BACKEND_URL/api/apps" 2>/dev/null || true)"
if printf '%s' "$apps_payload" | python3 -c 'import json,sys; data=json.load(sys.stdin); assert any(item["id"]=="contract-review-agent" for item in data); assert any(item["id"]=="sales-followup-agent" for item in data)' 2>/dev/null; then
  pass "example apps loaded"
else
  fail "example app API check failed" "Check backend logs and app manifests under examples/apps."
fi

bootstrap_payload="$(http_get "$BACKEND_URL/api/bootstrap" 2>/dev/null || true)"
workspace_id="$(printf '%s' "$bootstrap_payload" | python3 -c 'import json,sys; data=json.load(sys.stdin); print((data.get("workspace") or {}).get("id",""))' 2>/dev/null || true)"
project_id="$(printf '%s' "$bootstrap_payload" | python3 -c 'import json,sys; data=json.load(sys.stdin); projects=data.get("projects") or []; print(projects[0]["id"] if projects else "")' 2>/dev/null || true)"
agent_id="$(printf '%s' "$bootstrap_payload" | python3 -c 'import json,sys; data=json.load(sys.stdin); agents=data.get("agents") or []; print(agents[0]["id"] if agents else "")' 2>/dev/null || true)"

if [ -n "$workspace_id" ]; then
  pass "bootstrap workspace available"
else
  fail "bootstrap workspace missing" "Restart the backend so seed_defaults can create the demo workspace."
fi

session_payload=""
session_id=""
if [ -n "$workspace_id" ]; then
  session_payload="$(http_post "$BACKEND_URL/api/conversations" "{\"app_id\":\"contract-review-agent\",\"workspace_id\":\"$workspace_id\",\"project_id\":\"$project_id\",\"agent_id\":\"$agent_id\",\"channel\":\"web\",\"metadata\":{\"source\":\"verify_local_demo\"}}" 2>/dev/null || true)"
  session_id="$(printf '%s' "$session_payload" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))' 2>/dev/null || true)"
fi

if [ -n "$session_id" ]; then
  pass "conversation session created"
else
  fail "conversation session creation failed" "Check /api/conversations and backend database connectivity."
fi

message_payload=""
if [ -n "$session_id" ]; then
  printf '· checking conversation-native message endpoint; this can take up to 90s if LLM mode is enabled locally\n'
  message_payload="$(http_post "$BACKEND_URL/api/conversations/$session_id/messages" '{"content":"Review this contract and flag risky liability clauses.","attachments":[]}' 2>/dev/null || true)"
fi

if printf '%s' "$message_payload" | python3 -c 'import json,sys; data=json.load(sys.stdin); assert data.get("status") in {"completed","failed"}; assert data.get("task_id"); assert data.get("run_id")' 2>/dev/null; then
  pass "conversation-native message endpoint completed"
else
  fail "conversation-native message endpoint failed" "Check backend logs for runtime errors; deterministic mode should not require an API key."
fi

printf '\n'
if [ "$FAIL_COUNT" -eq 0 ]; then
  printf '✓ demo verification complete (%s checks passed)\n' "$PASS_COUNT"
  exit 0
fi

printf 'Demo verification finished with %s failure(s) and %s pass(es).\n' "$FAIL_COUNT" "$PASS_COUNT" >&2
exit 1
