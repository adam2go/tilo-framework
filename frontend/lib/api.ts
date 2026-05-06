import type { Agent, Artifact, Confirmation, ConversationSession, ConversationTurn, Feedback, Memory, Project, Run, RunMetrics, SkillCandidate, Task, TraceStep, UIInteractionEvent, Workspace } from "./types";

export type { Agent, Artifact, Confirmation, ConversationSession, ConversationTurn, Feedback, Memory, Project, Run, RunMetrics, SkillCandidate, Task, TraceStep, UIInteractionEvent, Workspace };

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

export async function createConversationSession(payload: {
  app_id: string;
  workspace_id: string;
  project_id?: string | null;
  agent_id?: string | null;
  channel: string;
  external_thread_id?: string | null;
  external_user_id?: string | null;
  metadata?: Record<string, unknown>;
}) {
  return apiFetch<ConversationSession>("/api/conversations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getConversationSession(sessionId: string) {
  return apiFetch<ConversationSession>(`/api/conversations/${sessionId}`);
}

export async function getConversationTurns(sessionId: string) {
  return apiFetch<ConversationTurn[]>(`/api/conversations/${sessionId}/turns`);
}

export async function appendConversationTurn(sessionId: string, payload: {
  turn_type: string;
  role?: string | null;
  content?: string | null;
  surface_type?: string | null;
  surface_payload?: Record<string, unknown> | null;
  observation_payload?: Record<string, unknown> | null;
  artifact_id?: string | null;
  run_id?: string | null;
  task_id?: string | null;
  interaction_id?: string | null;
  confirmation_id?: string | null;
  memory_id?: string | null;
  policy_decision?: Record<string, unknown> | null;
}) {
  return apiFetch<ConversationTurn>(`/api/conversations/${sessionId}/turns`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function appendObservationForInteraction(sessionId: string, interactionId: string) {
  return apiFetch<ConversationTurn>(`/api/conversations/${sessionId}/observations/from-interaction`, {
    method: "POST",
    body: JSON.stringify({ interaction_id: interactionId })
  });
}
