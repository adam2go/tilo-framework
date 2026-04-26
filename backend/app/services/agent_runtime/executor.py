from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Run, Task, Tool
from app.services.tools.invocation import ToolInvocationService
from app.services.trace.recorder import TraceRecorder


class Executor:
    def __init__(self, db: Session, trace: TraceRecorder):
        self.db = db
        self.trace = trace
        self.invocations = ToolInvocationService(db, trace)

    def invoke_tools(self, task: Task, run: Run) -> list[dict[str, Any]]:
        tools = list(self.db.scalars(select(Tool).where(Tool.workspace_id == task.workspace_id)).all())
        if not tools:
            tools = [Tool(workspace_id=task.workspace_id, name="Mock Search", type="mock_search", permission_level="low")]
            self.db.add_all(tools)
            self.db.commit()

        outputs = []
        for tool in tools[:2]:
            payload = {"query": task.input_message}
            invocation, output = self.invocations.invoke_registered(tool, payload, task_id=task.id, run_id=run.id)
            outputs.append(output)
            self.trace.record(
                run.id,
                "invoke_tool",
                f"Invoke {tool.name}",
                "Tool invocation is waiting for confirmation." if output.get("status") == "confirmation_required" else "Executed a registered mock tool.",
                input_json={"tool_type": tool.type, "permission_level": tool.permission_level, "tool_invocation_id": invocation.id},
                output_json=output,
                status="pending_confirmation" if invocation.status == "pending_confirmation" else "completed",
            )
        return outputs
