import { AppShell, EmptyState } from "../../components/AppShell";

export default function AgentsPage() {
  return (
    <AppShell>
      <main className="chat-panel">
        <h1>Agents</h1>
        <EmptyState title="Agent editor" detail="Agent list and editing will build on the persisted Agent model." />
      </main>
    </AppShell>
  );
}
