# API Contracts

This document defines API design expectations for Tilo Framework.

## 1. API Principles

Tilo APIs should be:

- explicit
- typed
- predictable
- easy for frontend and external developers to consume
- aligned with domain objects

Avoid vague generic endpoints that hide important domain concepts.

## 2. Response Shape

For v0.1, a simple response shape is acceptable.

Success:

```json
{
  "data": {},
  "error": null
}
```

Error:

```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message"
  }
}
```

If FastAPI defaults are used initially, keep errors readable and consistent where practical.

## 3. Naming

Use domain names directly:

- workspaces
- projects
- agents
- tasks
- runs
- memories
- artifacts
- confirmations
- skills
- tools
- messages

Avoid vague names such as `items`, `objects`, or `records` for core entities.

## 4. Required API Groups

### Workspaces

- `GET /api/workspaces`
- `POST /api/workspaces`
- `GET /api/workspaces/{id}`
- `PATCH /api/workspaces/{id}`

### Projects

- `GET /api/projects?workspace_id=`
- `POST /api/projects`
- `GET /api/projects/{id}`
- `PATCH /api/projects/{id}`

### Agents

- `GET /api/agents?workspace_id=`
- `POST /api/agents`
- `GET /api/agents/{id}`
- `PATCH /api/agents/{id}`

### Messages

- `POST /api/messages`

This endpoint is the conversation entry point. It should create a Task and Run.

### Tasks and Runs

- `POST /api/tasks`
- `GET /api/tasks?workspace_id=&project_id=`
- `GET /api/tasks/{id}`
- `POST /api/tasks/{id}/runs`
- `GET /api/runs/{id}`
- `GET /api/runs/{id}/trace`

### Memories

- `GET /api/memories?workspace_id=&project_id=&type=`
- `POST /api/memories`
- `PATCH /api/memories/{id}`
- `DELETE /api/memories/{id}`
- `POST /api/memories/recall`
- `POST /api/memories/{id}/confirm`

### Artifacts

- `GET /api/artifacts?workspace_id=&project_id=&task_id=`
- `GET /api/artifacts/{id}`
- `PATCH /api/artifacts/{id}`
- `POST /api/artifacts/{id}/versions`

### Confirmations

- `GET /api/confirmations?workspace_id=&status=pending`
- `GET /api/confirmations/{id}`
- `POST /api/confirmations/{id}/approve`
- `POST /api/confirmations/{id}/reject`
- `POST /api/confirmations/{id}/edit`

### Skills

- `GET /api/skills?workspace_id=`
- `POST /api/skills`
- `GET /api/skills/{id}`
- `PATCH /api/skills/{id}`

### Tools

- `GET /api/tools?workspace_id=`
- `POST /api/tools`
- `GET /api/tools/{id}`
- `PATCH /api/tools/{id}`
- `POST /api/tools/{id}/invoke`

## 5. Message API Contract

Input:

```json
{
  "workspace_id": "string",
  "project_id": "string|null",
  "agent_id": "string",
  "content": "string",
  "attachments": []
}
```

Output:

```json
{
  "task_id": "string",
  "run_id": "string",
  "status": "running"
}
```

## 6. Artifact API Contract

Artifacts must return full schema JSON:

```json
{
  "id": "string",
  "type": "contract_review",
  "title": "Contract Review",
  "schema_json": {
    "artifact_type": "contract_review",
    "title": "Contract Review",
    "blocks": []
  },
  "version": 1
}
```

## 7. Confirmation API Contract

Approve input:

```json
{
  "decision": {}
}
```

Reject input:

```json
{
  "reason": "optional"
}
```

Edit input:

```json
{
  "decision": {},
  "edited_payload": {}
}
```

## 8. Safety Requirements

- Do not expose secrets.
- Do not expose hidden reasoning.
- Do not allow high-risk tool invocation without confirmation.
- Validate workspace/project ownership when auth is implemented.

## 9. Versioning

v0.1 may use unversioned routes under `/api`.

Future public APIs may use `/api/v1`.
