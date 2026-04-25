import { AppShell, EmptyState } from "../../../components/AppShell";

export default function ArtifactPage() {
  return (
    <AppShell>
      <main className="artifact-panel">
        <h1>Artifact</h1>
        <EmptyState title="Artifact detail" detail="Artifacts are persisted and rendered from schema in the console view." />
      </main>
    </AppShell>
  );
}
