"use client";

import { useEffect, useMemo, useState } from "react";
import { Play, RefreshCcw, Send } from "lucide-react";
import { AppShell, EmptyState } from "./AppShell";
import { ArtifactRenderer } from "./ArtifactRenderer";
import { apiFetch, getBootstrap, sendMessage } from "../lib/api";
import type { Agent, Artifact, Confirmation, Memory, Project, TraceStep, Workspace } from "../lib/types";

const demoPrompts = [
  "Review this contract and flag risky clauses around liability, termination, and payment terms.",
  "Which customers should sales follow up with this week?",
  "Create a competitive analysis for memory-native AI agent frameworks."
];

export function Console() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [content, setContent] = useState(demoPrompts[0]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [confirmations, setConfirmations] = useState<Confirmation[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const canSend = Boolean(workspace && content.trim() && !busy);

  useEffect(() => {
    void boot();
  }, []);

  async function boot() {
    const data = await getBootstrap();
    setWorkspace(data.workspace);
    setProject(data.projects[0] || null);
    setAgent(data.agents[0] || null);
    if (data.workspace) {
      const existing = await apiFetch<Memory[]>(`/api/memories?workspace_id=${data.workspace.id}`);
      setMemories(existing);
      const inbox = await apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${data.workspace.id}&status=pending`);
      setConfirmations(inbox);
    }
  }

  async function submit(nextContent = content) {
    if (!workspace) return;
    setBusy(true);
    setError(null);
    try {
      const response = await sendMessage({
        workspace_id: workspace.id,
        project_id: project?.id,
        agent_id: agent?.id,
        content: nextContent
      });
      const [artifacts, inbox, updatedMemories, steps] = await Promise.all([
        apiFetch<Artifact[]>(`/api/artifacts?workspace_id=${workspace.id}&task_id=${response.task_id}`),
        apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${workspace.id}&status=pending`),
        apiFetch<Memory[]>(`/api/memories?workspace_id=${workspace.id}`),
        apiFetch<TraceStep[]>(`/api/runs/${response.run_id}/trace`)
      ]);
      setArtifact(artifacts[0] || null);
      setConfirmations(inbox);
      setMemories(updatedMemories);
      setTrace(steps);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function approveConfirmation(id: string) {
    const updated = await apiFetch<Confirmation>(`/api/confirmations/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ decision: { approved_from: "console" } })
    });
    setConfirmations((items) => items.map((item) => (item.id === id ? updated : item)));
  }

  async function confirmMemory(id: string) {
    const updated = await apiFetch<Memory>(`/api/memories/${id}/confirm`, { method: "POST" });
    setMemories((items) => items.map((item) => (item.id === id ? updated : item)));
  }

  const memoryGroups = useMemo(() => {
    return {
      confirmed: memories.filter((memory) => memory.is_confirmed),
      candidates: memories.filter((memory) => !memory.is_confirmed)
    };
  }, [memories]);

  return (
    <AppShell>
      <div className="console-grid">
        <section className="chat-panel">
          <header className="section-header">
            <div>
              <span className="eyebrow">{workspace?.name || "Workspace"}</span>
              <h1>Agent Task</h1>
            </div>
            <button className="icon-button" title="Refresh context" onClick={() => void boot()}>
              <RefreshCcw size={16} />
            </button>
          </header>
          <div className="demo-row">
            {demoPrompts.map((prompt) => (
              <button
                key={prompt}
                className="text-button"
                onClick={() => {
                  setContent(prompt);
                  void submit(prompt);
                }}
              >
                <Play size={14} />
                {prompt.split(" ").slice(0, 3).join(" ")}
              </button>
            ))}
          </div>
          <textarea value={content} onChange={(event) => setContent(event.target.value)} />
          <button className="primary-button" disabled={!canSend} onClick={() => void submit()}>
            <Send size={16} />
            {busy ? "Running" : "Send Message"}
          </button>
          {error ? <div className="error-box">{error}</div> : null}
          <div className="run-strip">
            <strong>{project?.name || "No project"}</strong>
            <span>{agent?.name || "No agent"}</span>
          </div>
        </section>

        <section className="artifact-panel">
          <ArtifactRenderer artifact={artifact} />
        </section>

        <aside className="context-panel">
          <section>
            <header className="mini-header">
              <strong>Trace</strong>
              <span>{trace.length}</span>
            </header>
            {trace.length ? (
              <ol className="trace-list">
                {trace.map((step) => (
                  <li key={step.id}>
                    <strong>{step.title}</strong>
                    <span>{step.summary}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <EmptyState title="No trace yet" detail="Run a task to see visible execution steps." />
            )}
          </section>

          <section>
            <header className="mini-header">
              <strong>Inbox</strong>
              <span>{confirmations.length}</span>
            </header>
            <div className="stack-list">
              {confirmations.map((item) => (
                <div className="list-item" key={item.id}>
                  <strong>{item.title}</strong>
                  <span>{item.description}</span>
                  <button className="small-button" onClick={() => void approveConfirmation(item.id)}>
                    Approve
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section>
            <header className="mini-header">
              <strong>Memory</strong>
              <span>{memoryGroups.confirmed.length}/{memories.length}</span>
            </header>
            <div className="stack-list">
              {memoryGroups.candidates.slice(0, 3).map((memory) => (
                <div className="list-item" key={memory.id}>
                  <strong>{memory.type}</strong>
                  <span>{memory.content}</span>
                  <button className="small-button" onClick={() => void confirmMemory(memory.id)}>
                    Confirm
                  </button>
                </div>
              ))}
              {memoryGroups.confirmed.slice(0, 2).map((memory) => (
                <div className="list-item confirmed" key={memory.id}>
                  <strong>{memory.type}</strong>
                  <span>{memory.content}</span>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </AppShell>
  );
}
