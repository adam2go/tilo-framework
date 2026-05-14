from typing import Any

from sqlalchemy.orm import Session

from tilo.core.time import utcnow
from tilo.models import Confirmation, Run, Task, Tool, ToolInvocation
from tilo.services.agent_runtime.state_machine import RunStateMachine
from tilo.services.tools.registry import ToolRegistry
from tilo.services.trace.recorder import TraceRecorder


class ToolInvocationService:
    def __init__(self, db: Session, trace: TraceRecorder | None = None):
        self.db = db
        self.trace = trace or TraceRecorder(db)
        self.registry = ToolRegistry(db)
        self.state_machine = RunStateMachine()

    def invoke_registered(
        self,
        tool: Tool,
        payload: dict[str, Any],
        *,
        task_id: str | None,
        run_id: str,
    ) -> tuple[ToolInvocation, dict[str, Any]]:
        invocation = ToolInvocation(
            workspace_id=tool.workspace_id,
            run_id=run_id,
            tool_id=tool.id,
            tool_name=tool.name,
            tool_type=tool.type,
            permission_level=tool.permission_level,
            input_json=self._safe_payload(payload),
            status="running",
            started_at=utcnow(),
        )
        self.db.add(invocation)
        self.db.flush()

        if tool.permission_level == "high":
            output = self._create_pending_confirmation(tool, payload, task_id, run_id, invocation)
        else:
            output = self.registry.invoke(tool, payload, task_id=task_id, run_id=run_id)
            invocation.output_json = self._safe_payload(output)
            invocation.status = "completed"
            invocation.completed_at = utcnow()

        self.db.commit()
        self.db.refresh(invocation)
        return invocation, {**output, "tool_invocation_id": invocation.id}

    def invoke_direct(self, tool: Tool, payload: dict[str, Any]) -> dict[str, Any]:
        task = Task(
            workspace_id=tool.workspace_id,
            title=f"Invoke tool: {tool.name}",
            input_message=f"Direct invocation for tool {tool.name}",
        )
        self.db.add(task)
        self.db.flush()
        run = Run(task_id=task.id)
        self.db.add(run)
        self.db.flush()
        self.state_machine.transition(task, run, "running")
        self.db.commit()
        self.db.refresh(task)
        self.db.refresh(run)

        invocation, output = self.invoke_registered(tool, payload, task_id=task.id, run_id=run.id)
        self.trace.record(
            run.id,
            "invoke_tool",
            f"Invoke {tool.name}",
            self._trace_summary(invocation),
            input_json={"tool_type": tool.type, "permission_level": tool.permission_level, "tool_invocation_id": invocation.id},
            output_json=output,
            status="completed" if invocation.status == "completed" else "pending_confirmation",
        )

        if invocation.status == "pending_confirmation":
            self.state_machine.transition(task, run, "waiting_for_confirmation")
            run.result_summary = "Tool invocation is waiting for confirmation."
        else:
            self.state_machine.transition(task, run, "completed")
            run.result_summary = "Tool invocation completed."
        self.db.commit()
        return {"task_id": task.id, "run_id": run.id, "tool_invocation_id": invocation.id, "output": output}

    def _create_pending_confirmation(
        self,
        tool: Tool,
        payload: dict[str, Any],
        task_id: str | None,
        run_id: str,
        invocation: ToolInvocation,
    ) -> dict[str, Any]:
        confirmation = Confirmation(
            workspace_id=tool.workspace_id,
            task_id=task_id,
            run_id=run_id,
            type="tool_permission",
            title=f"Approve {tool.name}",
            description="High-risk tool invocation requires approval before execution.",
            payload_json={
                "tool_id": tool.id,
                "tool_invocation_id": invocation.id,
                "tool_name": tool.name,
                "tool_type": tool.type,
                "permission_level": tool.permission_level,
                "input": self._safe_payload(payload),
            },
        )
        self.db.add(confirmation)
        self.db.flush()
        invocation.status = "pending_confirmation"
        invocation.confirmation_id = confirmation.id
        invocation.output_json = {"status": "confirmation_required", "confirmation_id": confirmation.id}
        return {"status": "confirmation_required", "confirmation_id": confirmation.id}

    @staticmethod
    def _trace_summary(invocation: ToolInvocation) -> str:
        if invocation.status == "pending_confirmation":
            return "High-risk tool invocation is waiting for confirmation."
        return "Tool invocation completed through ToolInvocation ledger."

    @staticmethod
    def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
        secret_keys = {"api_key", "token", "password", "secret", "authorization"}
        return {key: "[redacted]" if key.lower() in secret_keys else value for key, value in payload.items()}
