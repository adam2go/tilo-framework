# Technical Stack and Reuse Guidelines

This document defines recommended technologies and reusable building blocks for Tilo Framework v0.1.

## 1. Core Stack

### Backend

Use:

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- PostgreSQL
- pgvector
- Redis if needed

### Frontend

Use:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- lucide-react

### Model API

Use OpenAI-compatible APIs.

Environment variables:

```text
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=
DEFAULT_EMBEDDING_MODEL=
```

The model client should not be tightly coupled to one provider.

## 2. Reuse Before Reinvention

Do not build everything from scratch if a stable, lightweight library can do the job.

However, avoid heavy frameworks that hide Tilo's core domain model.

## 3. Backend Reuse Suggestions

### FastAPI

Use for API endpoints.

### SQLAlchemy

Use for database models and queries.

### Alembic

Use for migrations if database setup is implemented.

### Pydantic

Use for request and response schemas.

### httpx

Use for HTTP tools and model client requests if needed.

### OpenAI SDK or compatible client

Use for model calls. Keep a wrapper layer around it.

## 4. Agent Framework Reuse

Tilo may borrow ideas from existing agent frameworks, but should not become a thin wrapper over one framework.

Acceptable:

- using LangGraph-like state machine ideas
- using OpenAI-compatible tool calling concepts
- using MCP as tool protocol later
- using browser automation later

Avoid:

- hiding all runtime state inside a third-party framework
- making Tilo's Task/Run/Memory/Artifact concepts secondary
- coupling the core runtime to one vendor or framework

## 5. Frontend Reuse Suggestions

### shadcn/ui

Use for:

- buttons
- cards
- dialogs
- tabs
- tables
- forms
- sheets
- dropdowns

### lucide-react

Use for icons.

### Tailwind CSS

Use for layout and styling.

Do not introduce a large UI framework unless necessary.

## 6. Document and File Processing

For v0.1, keep file processing simple.

Contract review can start with pasted text or simple uploaded text files.

Future candidates:

- python-docx for Word files
- pypdf for PDFs
- mammoth for docx to HTML
- unstructured for broader parsing

Do not overbuild file parsing before the main loop works.

## 7. Vector Search

For v0.1:

- pgvector is preferred.
- If pgvector setup is too heavy, implement keyword recall first and keep embedding fields ready.

Do not block the full product loop on vector search perfection.

## 8. Tooling

Tool system should start with:

- mock_search
- mock_browser
- http_tool
- file_tool placeholder
- python_sandbox placeholder
- mcp placeholder

Real high-risk tools should not be implemented in v0.1 unless guarded by confirmation.

## 9. Testing Stack

Backend:

- pytest
- httpx test client

Frontend:

- basic TypeScript checks
- component tests optional

Prioritize integration tests for the core loop.

## 10. Formatting and Quality

Recommended:

- ruff for Python linting/formatting
- black if preferred
- eslint for frontend
- prettier for frontend

If tools are added, document commands in README.

## 11. Deployment

v0.1 should support Docker Compose with:

- backend
- frontend
- postgres
- redis optional

Do not require cloud-specific services for local development.

## 12. Dependency Discipline

Before adding a dependency, consider:

1. Does it reduce implementation complexity meaningfully?
2. Is it actively maintained?
3. Does it make the architecture harder to understand?
4. Does it lock Tilo into a narrow design?

Prefer fewer dependencies in v0.1.
