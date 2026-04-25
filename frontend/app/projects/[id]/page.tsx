import { AppShell, EmptyState } from "../../../components/AppShell";

export default function ProjectPage() {
  return (
    <AppShell>
      <main className="chat-panel">
        <h1>Project</h1>
        <EmptyState title="Project workspace" detail="Project-specific tasks, artifacts, memory, and trace views will build on this route." />
      </main>
    </AppShell>
  );
}
