import { AppShell, EmptyState } from "../../components/AppShell";

export default function WorkspacesPage() {
  return (
    <AppShell>
      <main className="chat-panel">
        <h1>Workspaces</h1>
        <EmptyState title="Workspace management" detail="The default workspace is seeded by the backend for the first vertical slice." />
      </main>
    </AppShell>
  );
}
