from typing import Any

from sqlalchemy.orm import Session

from app.models import Confirmation, Tool


class ToolRegistry:
    def __init__(self, db: Session | None = None):
        self.db = db

    def invoke(
        self,
        tool: Tool,
        payload: dict[str, Any],
        task_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        if tool.permission_level == "high":
            if not self.db:
                return {"status": "confirmation_required", "tool_id": tool.id}
            confirmation = Confirmation(
                workspace_id=tool.workspace_id,
                task_id=task_id,
                run_id=run_id,
                type="tool_permission",
                title=f"Approve {tool.name}",
                description="High-risk tool invocation requires approval before execution.",
                payload_json={"tool_id": tool.id, "input": self._safe_payload(payload)},
            )
            self.db.add(confirmation)
            self.db.commit()
            self.db.refresh(confirmation)
            return {"status": "confirmation_required", "confirmation_id": confirmation.id}

        return self._invoke_mock(tool.type, payload)

    def _invoke_mock(self, tool_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if tool_type == "mock_search":
            query = payload.get("query", "")
            return {
                "query": query,
                "results": [
                    {"title": "Market signal", "snippet": f"Mock search result related to {query or 'the requested topic'}."},
                    {"title": "Customer context", "snippet": "Mock data source returned structured business context."},
                ],
            }
        if tool_type == "mock_browser":
            return {"url": payload.get("url", "https://example.com"), "summary": "Mock browser captured a concise page summary."}
        if tool_type in {"file", "file_tool"}:
            return {"status": "placeholder", "message": "File tools are registered but not enabled in v0.1."}
        return {"status": "unsupported", "message": f"No mock implementation for tool type {tool_type}."}

    def _safe_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        secret_keys = {"api_key", "token", "password", "secret", "authorization"}
        return {key: "[redacted]" if key.lower() in secret_keys else value for key, value in payload.items()}
