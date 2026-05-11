import { AppShell } from "../../../components/AppShell";
import { ArtifactDetail } from "../../../components/artifact/ArtifactDetail";

export default function ArtifactPage({ params, searchParams }: { params: { id: string }; searchParams?: { channel?: string; session_id?: string } }) {
  return (
    <AppShell>
      <main className="artifact-result-shell">
        <ArtifactDetail artifactId={params.id} channel={searchParams?.channel} sessionId={searchParams?.session_id || null} />
      </main>
    </AppShell>
  );
}
