import { Suspense } from "react";
import { Console } from "../../components/Console";

export default function WorkspacePage() {
  return (
    <Suspense fallback={<div className="artifact-placeholder">Loading ROAM workspace...</div>}>
      <Console />
    </Suspense>
  );
}
