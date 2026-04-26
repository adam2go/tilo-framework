import { AppShell } from "../../../components/AppShell";
import { ArtifactDetail } from "../../../components/artifact/ArtifactDetail";

export default function ArtifactPage({ params }: { params: { id: string } }) {
  return (
    <AppShell>
      <main className="artifact-result-shell">
        <ArtifactDetail artifactId={params.id} />
      </main>
    </AppShell>
  );
}
