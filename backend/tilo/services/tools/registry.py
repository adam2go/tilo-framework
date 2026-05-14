from typing import Any

from sqlalchemy.orm import Session

from tilo.models import Tool


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
        _ = (task_id, run_id)
        if tool.permission_level == "high":
            return {"status": "confirmation_required", "tool_id": tool.id, "mock": True}

        return self._invoke_mock(tool.type, payload)

    def _invoke_mock(self, tool_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if tool_type == "mock_search":
            query = payload.get("query", "")
            return {
                "mock": True,
                "query": query,
                "results": [
                    {"title": "Market signal", "snippet": f"Mock search result related to {query or 'the requested topic'}."},
                    {"title": "Customer context", "snippet": "Mock data source returned structured business context."},
                ],
            }
        if tool_type == "mock_browser":
            return {"mock": True, "url": payload.get("url", "https://example.com"), "summary": "Mock browser captured a concise page summary."}
        if tool_type in {"file", "file_tool"}:
            return {"mock": True, "status": "placeholder", "message": "File tools are registered but not enabled in v0.1."}
        return {"mock": True, "status": "unsupported", "message": f"No mock implementation for tool type {tool_type}."}
