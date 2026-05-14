.PHONY: dev dev-backend dev-frontend build test clean install

# Quick start: run both backend and frontend in development mode
dev: dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn tilo.main:app --host 127.0.0.1 --port 8000 --reload &

dev-frontend:
	cd frontend && pnpm dev --port 3000 &

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
