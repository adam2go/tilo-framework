"use client";

import { useEffect, useMemo, useState } from "react";
import { Play, RefreshCcw, Send } from "lucide-react";
import { AppShell, EmptyState } from "./AppShell";
import { ArtifactRenderer } from "./ArtifactRenderer";
import { apiFetch, getBootstrap, sendMessage } from "../lib/api";
import type { Agent, Artifact, Confirmation, Memory, Project, Skill, SkillCandidate, TraceStep, UIInteractionEvent, Workspace } from "../lib/types";

const demoPrompts = [
  "Contract ROAM: review this contract, show risks, request approval, and suggest a memory.",
  "Sales ROAM: rank follow-ups, show pipeline metrics, queue actions, and ask for approval.",
  "Competitive ROAM: compare AI agent frameworks, select positioning, and continue next steps."
];

const roamStages = ["Render", "Observe", "Act", "Memorize"];

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
  const [skills, setSkills] = useState<Skill[]>([]);
  const [skillCandidates, setSkillCandidates] = useState<SkillCandidate[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [interactions, setInteractions] = useState<UIInteractionEvent[]>([]);
  const [activeContext, setActiveContext] = useState<"memory" | "trace" | "skills" | "files">("trace");
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
      setSkills(await apiFetch<Skill[]>(`/api/skills?workspace_id=${data.workspace.id}`));
      setSkillCandidates(await apiFetch<SkillCandidate[]>(`/api/skills/candidates?workspace_id=${data.workspace.id}`));
      setInteractions(await apiFetch<UIInteractionEvent[]>(`/api/interactions?workspace_id=${data.workspace.id}`));
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
      const [artifacts, inbox, updatedMemories, steps, updatedSkills, candidates, updatedInteractions] = await Promise.all([
        apiFetch<Artifact[]>(`/api/artifacts?workspace_id=${workspace.id}&task_id=${response.task_id}`),
        apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${workspace.id}&status=pending`),
        apiFetch<Memory[]>(`/api/memories?workspace_id=${workspace.id}`),
        apiFetch<TraceStep[]>(`/api/runs/${response.run_id}/trace`),
        apiFetch<Skill[]>(`/api/skills?workspace_id=${workspace.id}`),
        apiFetch<SkillCandidate[]>(`/api/skills/candidates?workspace_id=${workspace.id}`),
        apiFetch<UIInteractionEvent[]>(`/api/interactions?workspace_id=${workspace.id}&run_id=${response.run_id}`)
      ]);
      setArtifact(artifacts[0] || null);
      setConfirmations(inbox);
      setMemories(updatedMemories);
      setTrace(steps);
      setSkills(updatedSkills);
      setSkillCandidates(candidates);
      setInteractions(updatedInteractions);
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
          <header className="section-header command-header">
            <div>
              <span className="eyebrow">{workspace?.name || "Workspace"} · ROAM Loop</span>
              <h1>Command Center</h1>
              <p>State a goal. Tilo renders an interaction surface, observes your actions, acts safely, and memorizes confirmed learning.</p>
            </div>
            <button className="icon-button" title="Refresh context" onClick={() => void boot()}>
              <RefreshCcw size={16} />
            </button>
          </header>
          <div className="roam-stage-strip">
            {roamStages.map((stage, index) => (
              <div className="roam-stage" key={stage}>
                <span>{index + 1}</span>
                <strong>{stage}</strong>
              </div>
            ))}
          </div>
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
                {prompt.split(":")[0]}
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
            <span>{agent?.name || "No agent"} · observations {interactions.length}</span>
          </div>
        </section>

        <section className="artifact-panel">
          <div className="surface-kicker">
            <span>Generated interaction surface</span>
            <strong>{artifact ? "Ready for human action" : "Waiting for a goal"}</strong>
          </div>
          <ArtifactRenderer artifact={artifact} />
        </section>

        <aside className="context-panel">
          <div className="context-tabs">
            {(["memory", "trace", "skills", "files"] as const).map((tab) => (
              <button className={activeContext === tab ? "context-tab active" : "context-tab"} key={tab} onClick={() => setActiveContext(tab)}>
                {tab[0].toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {activeContext === "trace" ? (
            <section>
              <header className="mini-header">
                <strong>Trace / Observations</strong>
                <span>{trace.length}</span>
              </header>
              {interactions.length ? (
                <div className="stack-list">
                  {interactions.slice(0, 3).map((event) => (
                    <div className="list-item confirmed" key={event.id}>
                      <strong>{event.event_type}</strong>
                      <span>{event.block_id || event.action_id || "artifact interaction"}</span>
                    </div>
                  ))}
                </div>
              ) : null}
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
          ) : null}

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

          {activeContext === "memory" ? (
            <section>
              <header className="mini-header">
                <strong>Memory</strong>
                <span>
                  {memoryGroups.confirmed.length}/{memories.length}
                </span>
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
          ) : null}

          {activeContext === "skills" ? (
            <section>
              <header className="mini-header">
                <strong>Skills</strong>
                <span>{skills.length}/{skillCandidates.length}</span>
              </header>
              <div className="stack-list">
                {skillCandidates.slice(0, 3).map((candidate) => (
                  <div className="list-item" key={candidate.id}>
                    <strong>{candidate.name}</strong>
                    <span>{candidate.status}</span>
                  </div>
                ))}
                {skills.slice(0, 3).map((skill) => (
                  <div className="list-item confirmed" key={skill.id}>
                    <strong>{skill.name}</strong>
                    <span>{skill.description || skill.trigger_description}</span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {activeContext === "files" ? (
            <section>
              <header className="mini-header">
                <strong>Files</strong>
                <span>0</span>
              </header>
              <EmptyState title="No files" detail="File context is reserved for upload-backed runs." />
            </section>
          ) : null}
        </aside>
      </div>
    </AppShell>
  );
}
