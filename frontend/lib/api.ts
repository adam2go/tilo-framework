import type { Agent, Artifact, Confirmation, Memory, Project, Run, Task, TraceStep, Workspace } from "./types";

export type { Agent, Artifact, Confirmation, Memory, Project, Run, Task, TraceStep, Workspace };

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function getBootstrap() {
  return apiFetch<{ workspace: Workspace | null; projects: Project[]; agents: Agent[] }>("/api/bootstrap");
}

export async function sendMessage(payload: {
  workspace_id: string;
  project_id?: string;
  agent_id?: string;
  content: string;
}) {
  return apiFetch<{
    task_id: string;
    run_id: string;
    status: string;
  }>("/api/messages", {
    method: "POST",
    body: JSON.stringify({ ...payload, attachments: [] })
  });
}
