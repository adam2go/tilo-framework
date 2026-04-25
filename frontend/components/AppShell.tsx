"use client";

import Link from "next/link";
import { Bot, Boxes, CheckSquare, Database, FileText, FolderKanban, Home, Layers, Users } from "lucide-react";

const nav = [
  { href: "/", label: "Console", icon: Home },
  { href: "/workspaces", label: "Workspaces", icon: Boxes },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/inbox", label: "Inbox", icon: CheckSquare },
  { href: "/memories", label: "Memories", icon: Database },
  { href: "/skills", label: "Skills", icon: Layers }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">T</div>
          <div>
            <strong>Tilo</strong>
            <span>Agent Runtime</span>
          </div>
        </div>
        <nav className="nav-list">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href} className="nav-link">
                <Icon size={17} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <FolderKanban size={16} />
          <span>Demo Project</span>
        </div>
      </aside>
      <main className="main-surface">{children}</main>
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-state">
      <FileText size={22} />
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}
