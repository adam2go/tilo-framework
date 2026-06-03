.PHONY: dev dev-backend dev-frontend build test clean install

# Ports — keep these in sync with README and .env.example (NEXT_PUBLIC_API_URL).
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 4001

# Quick start: run backend and frontend together. Ctrl-C stops both.
# (Uses a subshell trap so children don't get orphaned if you kill the make.)
dev:
	@echo "▸ backend  → http://127.0.0.1:$(BACKEND_PORT)"
	@echo "▸ frontend → http://localhost:$(FRONTEND_PORT)/canvas"
	@trap 'kill 0' INT TERM EXIT; \
	  (cd backend && uvicorn tilo.main:app --host 127.0.0.1 --port $(BACKEND_PORT) --reload) & \
	  (cd frontend && pnpm dev --port $(FRONTEND_PORT)) & \
	  wait

dev-backend:
	cd backend && uvicorn tilo.main:app --host 127.0.0.1 --port $(BACKEND_PORT) --reload

dev-frontend:
	cd frontend && pnpm dev --port $(FRONTEND_PORT)

# Install everything
install:
	cd backend && pip install -e ".[test]"
	cd frontend && pnpm install

# Run all tests
test:
	cd backend && python -m pytest tests/ -q
	cd frontend && pnpm lint

# Build frontend for production
build:
	cd frontend && pnpm build

# Clean generated files
clean:
	rm -rf backend/tilo/__pycache__ backend/.pytest_cache
	rm -rf frontend/.next frontend/node_modules/.cache
