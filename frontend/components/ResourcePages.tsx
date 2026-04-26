"use client";

import { useEffect, useState } from "react";
import { Check, Pencil, Rocket, Trash2, X } from "lucide-react";
import { apiFetch, getBootstrap } from "../lib/api";
import type { Confirmation, Memory, Skill, SkillCandidate, Workspace } from "../lib/types";

export function InboxPageContent() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [items, setItems] = useState<Confirmation[]>([]);

  useEffect(() => {
    void load();
  }, []);

  async function load() {
    const bootstrap = await getBootstrap();
    setWorkspace(bootstrap.workspace);
    if (bootstrap.workspace) {
      setItems(await apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${bootstrap.workspace.id}&status=`));
    }
  }

  async function decide(id: string, action: "approve" | "reject") {
    await apiFetch<Confirmation>(`/api/confirmations/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify(action === "approve" ? { decision: { source: "inbox" } } : { reason: "Rejected from inbox" })
    });
    await load();
  }

  async function edit(id: string) {
    await apiFetch<Confirmation>(`/api/confirmations/${id}/edit`, {
      method: "POST",
      body: JSON.stringify({
        decision: { source: "inbox", edited: true },
        edited_payload: { reviewed_from_inbox: true }
      })
    });
    await load();
  }

  const pending = items.filter((item) => item.status === "pending");
  const approved = items.filter((item) => item.status === "approved");
  const resolved = items.filter((item) => item.status === "rejected" || item.status === "edited");

  return (
    <section className="page-panel">
      <header className="section-header">
        <div>
          <span className="eyebrow">{workspace?.name || "Workspace"}</span>
          <h1>Inbox</h1>
        </div>
      </header>
      <div className="memory-columns">
        <ConfirmationGroup title="Pending" items={pending} onApprove={decide} onReject={decide} onEdit={edit} />
        <ConfirmationGroup title="Approved" items={approved} onApprove={decide} onReject={decide} onEdit={edit} />
        <ConfirmationGroup title="Rejected / Edited" items={resolved} onApprove={decide} onReject={decide} onEdit={edit} />
      </div>
    </section>
  );
}

function ConfirmationGroup({
  title,
  items,
  onApprove,
  onReject,
  onEdit
}: {
  title: string;
  items: Confirmation[];
  onApprove: (id: string, action: "approve") => Promise<void>;
  onReject: (id: string, action: "reject") => Promise<void>;
  onEdit: (id: string) => Promise<void>;
}) {
  return (
    <div className="memory-group">
      <div className="memory-group-header">
        <h2>{title}</h2>
        <span>{items.length}</span>
      </div>
      <div className="stack-list">
        {items.length ? (
          items.map((item) => {
            const riskLevel = String(item.payload_json.risk_level || item.payload_json.permission_level || item.payload_json.operation || "review");
            return (
              <article className="list-item" key={item.id}>
                <strong>{item.title}</strong>
                <span>{item.description}</span>
                <small>
                  {item.status} · risk {riskLevel} · task {item.task_id || "none"} · run {item.run_id || "none"}
                </small>
                {item.status === "pending" ? (
                  <div className="action-row">
                    <button className="small-button" onClick={() => void onApprove(item.id, "approve")}>
                      <Check size={14} />
                      Approve
                    </button>
                    <button className="small-button" onClick={() => void onReject(item.id, "reject")}>
                      <X size={14} />
                      Reject
                    </button>
                    <button className="small-button" onClick={() => void onEdit(item.id)}>
                      <Pencil size={14} />
                      Edit
                    </button>
                  </div>
                ) : null}
              </article>
            );
          })
        ) : (
          <div className="empty-state">
            <strong>No items</strong>
            <span>Confirmation cards created by runs will appear here.</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function MemoriesPageContent() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [items, setItems] = useState<Memory[]>([]);

  useEffect(() => {
    void load();
  }, []);

  async function load() {
    const bootstrap = await getBootstrap();
    setWorkspace(bootstrap.workspace);
    if (bootstrap.workspace) {
      setItems(await apiFetch<Memory[]>(`/api/memories?workspace_id=${bootstrap.workspace.id}`));
    }
  }

  async function confirm(id: string) {
    await apiFetch<Memory>(`/api/memories/${id}/confirm`, { method: "POST" });
    await load();
  }

  async function reject(id: string) {
    await apiFetch<Memory>(`/api/memories/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason: "Rejected from memory workbench" })
    });
    await load();
  }

  async function editMemory(memory: Memory) {
    const content = window.prompt("Memory content", memory.content);
    if (!content || content === memory.content) {
      return;
    }
    await apiFetch<Memory>(`/api/memories/${memory.id}/edit`, {
      method: "POST",
      body: JSON.stringify({ content, status: memory.status, is_confirmed: memory.is_confirmed })
    });
    await load();
  }

  async function deleteMemory(id: string) {
    await apiFetch<{ status: string }>(`/api/memories/${id}`, { method: "DELETE" });
    await load();
  }

  const candidates = items.filter((memory) => memory.status === "candidate" || (!memory.is_confirmed && !["rejected", "archived"].includes(memory.status)));
  const confirmed = items.filter((memory) => memory.status === "confirmed" || memory.is_confirmed);
  const rejected = items.filter((memory) => memory.status === "rejected" || memory.status === "archived");

  return (
    <section className="page-panel">
      <header className="section-header">
        <div>
          <span className="eyebrow">{workspace?.name || "Workspace"}</span>
          <h1>Memories</h1>
        </div>
      </header>
      {items.length ? (
        <div className="memory-columns">
          <MemoryGroup title="Candidates" items={candidates} onConfirm={confirm} onReject={reject} onEdit={editMemory} onDelete={deleteMemory} />
          <MemoryGroup title="Confirmed" items={confirmed} onConfirm={confirm} onReject={reject} onEdit={editMemory} onDelete={deleteMemory} />
          <MemoryGroup title="Rejected" items={rejected} onConfirm={confirm} onReject={reject} onEdit={editMemory} onDelete={deleteMemory} />
        </div>
      ) : (
        <div className="empty-state">
          <strong>No memories yet</strong>
          <span>Tilo will suggest memories after tasks are completed.</span>
        </div>
      )}
    </section>
  );
}

function MemoryGroup({
  title,
  items,
  onConfirm,
  onReject,
  onEdit,
  onDelete
}: {
  title: string;
  items: Memory[];
  onConfirm: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  onEdit: (memory: Memory) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}) {
  return (
    <div className="memory-group">
      <div className="memory-group-header">
        <h2>{title}</h2>
        <span>{items.length}</span>
      </div>
      <div className="stack-list">
        {items.map((memory) => (
          <article className={`list-item ${memory.is_confirmed ? "confirmed" : ""}`} key={memory.id}>
            <strong>{memory.type}</strong>
            <span>{memory.content}</span>
            <small>
              {memory.status} · {memory.scope_type} · confidence {memory.confidence} · salience {memory.salience} · recalled {memory.recall_count}
            </small>
            <div className="action-row">
              {!memory.is_confirmed ? (
                <button className="small-button" onClick={() => void onConfirm(memory.id)}>
                  <Check size={14} />
                  Accept
                </button>
              ) : null}
              {memory.status === "candidate" ? (
                <button className="small-button" onClick={() => void onReject(memory.id)}>
                  <X size={14} />
                  Reject
                </button>
              ) : null}
              <button className="small-button" onClick={() => void onEdit(memory)}>
                <Pencil size={14} />
                Edit
              </button>
              <button className="small-button" onClick={() => void onDelete(memory.id)}>
                <Trash2 size={14} />
                Delete
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export function SkillsPageContent() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [items, setItems] = useState<Skill[]>([]);
  const [candidates, setCandidates] = useState<SkillCandidate[]>([]);

  useEffect(() => {
    void load();
  }, []);

  async function load() {
    const bootstrap = await getBootstrap();
    setWorkspace(bootstrap.workspace);
    if (bootstrap.workspace) {
      setItems(await apiFetch<Skill[]>(`/api/skills?workspace_id=${bootstrap.workspace.id}`));
      setCandidates(await apiFetch<SkillCandidate[]>(`/api/skills/candidates?workspace_id=${bootstrap.workspace.id}`));
    }
  }

  async function approveCandidate(id: string) {
    await apiFetch<SkillCandidate>(`/api/skills/candidates/${id}/approve`, { method: "POST" });
    await load();
  }

  async function rejectCandidate(id: string) {
    await apiFetch<SkillCandidate>(`/api/skills/candidates/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason: "Rejected from skills review" })
    });
    await load();
  }

  async function promoteCandidate(id: string) {
    await apiFetch<Skill>(`/api/skills/candidates/${id}/promote`, { method: "POST" });
    await load();
  }

  return (
    <section className="page-panel">
      <header className="section-header">
        <div>
          <span className="eyebrow">{workspace?.name || "Workspace"}</span>
          <h1>Skills</h1>
        </div>
      </header>
      <section className="review-panel">
        <div className="memory-group-header">
          <h2>Review Queue</h2>
          <span>{candidates.length}</span>
        </div>
        <div className="stack-list">
          {candidates.length ? (
            candidates.map((candidate) => (
              <article className="list-item" key={candidate.id}>
                <strong>{candidate.name}</strong>
                <span>{candidate.description || candidate.trigger_description}</span>
                <small>{candidate.status} · source run {candidate.source_run_id}</small>
                <div className="action-row">
                  {candidate.status === "pending_review" ? (
                    <>
                      <button className="small-button" onClick={() => void approveCandidate(candidate.id)}>
                        <Check size={14} />
                        Approve
                      </button>
                      <button className="small-button" onClick={() => void rejectCandidate(candidate.id)}>
                        <X size={14} />
                        Reject
                      </button>
                    </>
                  ) : null}
                  {candidate.status === "approved" ? (
                    <button className="small-button" onClick={() => void promoteCandidate(candidate.id)}>
                      <Rocket size={14} />
                      Promote
                    </button>
                  ) : null}
                </div>
              </article>
            ))
          ) : (
            <div className="empty-state">
              <strong>No skill candidates</strong>
              <span>Positive feedback on completed runs can propose reusable skills for review.</span>
            </div>
          )}
        </div>
      </section>
      <div className="stack-list">
        {items.length ? (
          items.map((skill) => (
            <article className="list-item" key={skill.id}>
              <strong>{skill.name}</strong>
              <span>{skill.description || skill.trigger_description || "Reusable capability package"}</span>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <strong>No skills yet</strong>
            <span>Seeded reusable skills will appear after the backend starts.</span>
          </div>
        )}
      </div>
    </section>
  );
}
