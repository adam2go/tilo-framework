#!/usr/bin/env bash
# Local development launcher.
#
# Starts the backend (FastAPI on :8000) and the frontend (Next.js on :3000)
# with sensible defaults (SQLite DB, deterministic LLM mode). No Docker.
# No Redis. No Postgres.
#
# Usage:
#   bash scripts/dev.sh                    # starts both, foreground
#   bash scripts/dev.sh --backend-only     # only the FastAPI server
#   bash scripts/dev.sh --frontend-only    # only the Next.js server
#
# Press Ctrl-C to stop both.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# --- env ---------------------------------------------------------------------

if [[ ! -f .env ]]; then
  if [[ -f .env.local.example ]]; then
    echo "→ copying .env.local.example to .env"
    cp .env.local.example .env
  else
    echo "✗ no .env and no .env.local.example to copy from" >&2
    exit 1
  fi
fi
# Re-export the local-friendly defaults regardless of what .env contains so
# the dev script "just works" even when .env was generated for docker.
export DATABASE_URL="${DATABASE_URL:-sqlite:///./tilo.db}"
export LLM_ENABLED="${LLM_ENABLED:-false}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"

# --- args --------------------------------------------------------------------

START_BACKEND=true
START_FRONTEND=true
case "${1:-}" in
  --backend-only)  START_FRONTEND=false ;;
  --frontend-only) START_BACKEND=false  ;;
  --help|-h)
    sed -n '2,16p' "${BASH_SOURCE[0]}"
    exit 0
    ;;
esac

# --- helpers -----------------------------------------------------------------

log() { printf '\033[1;36m[dev]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[dev]\033[0m %s\n' "$*" >&2; }

ensure_python_venv() {
  local venv_dir="${REPO_ROOT}/.venv"
  if [[ ! -d "${venv_dir}" ]]; then
    log "creating Python venv at .venv"
    python3 -m venv "${venv_dir}"
  fi
  # shellcheck source=/dev/null
  source "${venv_dir}/bin/activate"
  if ! python -c "import fastapi" >/dev/null 2>&1; then
    log "installing backend deps into .venv"
    pip install -q --upgrade pip >/dev/null
    pip install -q \
      "fastapi>=0.110" "uvicorn[standard]>=0.27" \
      "sqlalchemy>=2.0" "pydantic>=2.6" "pydantic-settings>=2.2" \
      "PyYAML>=6.0" "httpx>=0.27" "anyio>=4.0" "watchfiles>=0.20"
  fi
}

ensure_frontend_deps() {
  if [[ ! -d "${REPO_ROOT}/frontend/node_modules" ]]; then
    log "installing frontend deps (this only runs the first time)"
    if command -v pnpm >/dev/null 2>&1; then
      (cd frontend && pnpm install --silent)
    else
      (cd frontend && npm install --silent --no-audit --no-fund)
    fi
  fi
}

# --- launchers ---------------------------------------------------------------

PIDS=()
cleanup() {
  if (( ${#PIDS[@]} > 0 )); then
    log "stopping (pids: ${PIDS[*]})"
    kill "${PIDS[@]}" 2>/dev/null || true
    wait 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if "${START_BACKEND}"; then
  ensure_python_venv
  log "starting backend on :8000"
  (cd backend && uvicorn tilo.main:app --host 127.0.0.1 --port 8000 --reload) &
  PIDS+=("$!")
fi

if "${START_FRONTEND}"; then
  ensure_frontend_deps
  log "starting frontend on :3000"
  if command -v pnpm >/dev/null 2>&1; then
    (cd frontend && pnpm dev) &
  else
    (cd frontend && npm run dev) &
  fi
  PIDS+=("$!")
fi

# Friendly summary once both have had a moment to start.
sleep 2
echo
log "ready."
"${START_BACKEND}"  && log "  backend  → http://localhost:8000/api/health"
"${START_FRONTEND}" && log "  frontend → http://localhost:3000/"
"${START_FRONTEND}" && log "  demo     → http://localhost:3000/demo"
echo

wait
