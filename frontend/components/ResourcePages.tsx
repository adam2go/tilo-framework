"use client";

import { useEffect, useState } from "react";
import { Check, Trash2, X } from "lucide-react";
import { apiFetch, getBootstrap } from "../lib/api";
import type { Confirmation, Memory, Skill, Workspace } from "../lib/types";

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
      setItems(await apiFetch<Confirmation[]>(`/api/confirmations?workspace_id=${bootstrap.workspace.id}&status=pending`));
    }
  }

  async function decide(id: string, action: "approve" | "reject") {
    await apiFetch<Confirmation>(`/api/confirmations/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify(action === "approve" ? { decision: { source: "inbox" } } : { reason: "Rejected from inbox" })
    });
    await load();
  }

  return (
    <section className="page-panel">
      <header className="section-header">
        <div>
          <span className="eyebrow">{workspace?.name || "Workspace"}</span>
          <h1>Inbox</h1>
        </div>
      </header>
      <div className="stack-list">
        {items.length ? (
          items.map((item) => (
            <article className="list-item" key={item.id}>
              <strong>{item.title}</strong>
              <span>{item.description}</span>
              <div className="action-row">
                <button className="small-button" onClick={() => void decide(item.id, "approve")}>
                  <Check size={14} />
                  Approve
                </button>
                <button className="small-button" onClick={() => void decide(item.id, "reject")}>
                  <X size={14} />
                  Reject
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <strong>No decisions pending</strong>
            <span>Confirmation cards created by runs will appear here.</span>
          </div>
        )}
      </div>
    </section>
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

  async function deleteMemory(id: string) {
    await apiFetch<{ status: string }>(`/api/memories/${id}`, { method: "DELETE" });
    await load();
  }

  return (
    <section className="page-panel">
      <header className="section-header">
        <div>
          <span className="eyebrow">{workspace?.name || "Workspace"}</span>
          <h1>Memories</h1>
        </div>
      </header>
      <div className="stack-list">
        {items.length ? (
          items.map((memory) => (
            <article className={`list-item ${memory.is_confirmed ? "confirmed" : ""}`} key={memory.id}>
              <strong>{memory.type}</strong>
              <span>{memory.content}</span>
              <small>{memory.is_confirmed ? "Confirmed" : "Candidate"} · confidence {memory.confidence}</small>
              <div className="action-row">
                {!memory.is_confirmed ? (
                  <button className="small-button" onClick={() => void confirm(memory.id)}>
                    <Check size={14} />
                    Confirm
                  </button>
                ) : null}
                <button className="small-button" onClick={() => void deleteMemory(memory.id)}>
                  <Trash2 size={14} />
                  Delete
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <strong>No memories yet</strong>
            <span>Tilo will suggest memories after tasks are completed.</span>
          </div>
        )}
      </div>
    </section>
  );
}

export function SkillsPageContent() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [items, setItems] = useState<Skill[]>([]);

  useEffect(() => {
    void load();
  }, []);

  async function load() {
    const bootstrap = await getBootstrap();
    setWorkspace(bootstrap.workspace);
    if (bootstrap.workspace) {
      setItems(await apiFetch<Skill[]>(`/api/skills?workspace_id=${bootstrap.workspace.id}`));
    }
  }

  return (
    <section className="page-panel">
      <header className="section-header">
        <div>
          <span className="eyebrow">{workspace?.name || "Workspace"}</span>
          <h1>Skills</h1>
        </div>
      </header>
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
