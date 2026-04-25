from typing import Any

from sqlalchemy.orm import Session

from app.models import Run, Task, Tool
from app.services.tools.registry import ToolRegistry
from app.services.trace.recorder import TraceRecorder


class ToolInvocationService:
    def __init__(self, db: Session):
        self.db = db
        self.trace = TraceRecorder(db)
        self.registry = ToolRegistry(db)

    def invoke_direct(self, tool: Tool, payload: dict[str, Any]) -> dict[str, Any]:
        task = Task(
            workspace_id=tool.workspace_id,
            title=f"Invoke tool: {tool.name}",
            input_message=f"Direct invocation for tool {tool.name}",
            status="running",
        )
        self.db.add(task)
        self.db.flush()
        run = Run(task_id=task.id, status="running")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(task)
        self.db.refresh(run)

        output = self.registry.invoke(tool, payload, task_id=task.id, run_id=run.id)
        self.trace.record(
            run.id,
            "invoke_tool",
            f"Invoke {tool.name}",
            "Direct tool invocation was routed through ToolRegistry.",
            input_json={"tool_type": tool.type, "permission_level": tool.permission_level},
            output_json=self._safe_output(output),
        )
        run.status = "completed"
        task.status = "completed"
        run.result_summary = "Tool invocation completed." if output.get("status") != "confirmation_required" else "Tool invocation is waiting for confirmation."
        self.db.commit()
        return {"task_id": task.id, "run_id": run.id, "output": output}

    def _safe_output(self, output: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in output.items() if key.lower() not in {"api_key", "token", "password", "secret"}}
