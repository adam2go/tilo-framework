import type { DemoSurfaceCopy } from "../mini-surfaces/types";
import { MiniSurfaceRenderer } from "../mini-surfaces/MiniSurfaceRenderer";
import type { MiniSurfaceType } from "../mini-surfaces/registry";
import type { Artifact } from "../../lib/types";

export function ContractReviewMiniSurfaceAdapter({
  artifact,
  copy,
  onApprove,
  onEdit,
  onFullReview,
  onMemory,
  onSkipMemory,
  primaryRisk,
  summary,
  surfaceType,
}: {
  artifact: Artifact;
  copy: DemoSurfaceCopy;
  onApprove: () => Promise<void>;
  onEdit: () => Promise<void>;
  onFullReview: () => Promise<void>;
  onMemory: () => Promise<void>;
  onSkipMemory: () => Promise<void>;
  primaryRisk?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  surfaceType: MiniSurfaceType;
}) {
  return <MiniSurfaceRenderer props={surfaceProps({ artifact, copy, onApprove, onEdit, onFullReview, onMemory, onSkipMemory, primaryRisk, summary, surfaceType })} surfaceType={surfaceType} />;
}

function surfaceProps({
  artifact,
  copy,
  onApprove,
  onEdit,
  onFullReview,
  onMemory,
  onSkipMemory,
  primaryRisk,
  summary,
  surfaceType,
}: {
  artifact: Artifact;
  copy: DemoSurfaceCopy;
  onApprove: () => Promise<void>;
  onEdit: () => Promise<void>;
  onFullReview: () => Promise<void>;
  onMemory: () => Promise<void>;
  onSkipMemory: () => Promise<void>;
  primaryRisk?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  surfaceType: MiniSurfaceType;
}) {
  if (surfaceType === "MiniIssueCard") {
    return {
      artifact,
      labels: {
        activeRisk: copy.activeRisk,
        approveRevision: copy.approveRevision,
        editDirection: copy.editDirection,
        evidence: copy.evidence,
        high: copy.high,
        low: copy.low,
        medium: copy.medium,
        openFullReview: copy.openFullReview,
        recommendedRevision: copy.recommendedRevision,
        title: copy.contractReview,
      },
      onApprove,
      onEdit,
      onFullReview,
      primaryRisk,
      summary,
    };
  }

  if (surfaceType === "MiniRevisionPreview") {
    const block = artifact.schema_json.blocks.find((item) => item.id === "editable_revision" || item.type === "editable_revision");
    return {
      after: String(block?.data.content || primaryRisk?.suggested_revision || ""),
      before: String(primaryRisk?.evidence || primaryRisk?.issue || ""),
      labels: { after: copy.after, before: copy.before, draftEmail: copy.draftEmail, makeSofter: copy.makeSofter, makeStricter: copy.makeStricter, openArtifact: copy.openArtifact },
      onFullReview,
      title: String(block?.data.heading || copy.revisionPreview),
    };
  }

  if (surfaceType === "MiniMemoryCard") {
    const block = artifact.schema_json.blocks.find((item) => item.id === "memory_candidate" || item.type === "memory_candidate");
    return {
      content: String(block?.data.content || copy.memoryPrompt),
      labels: { editDirection: copy.editDirection, notNow: copy.notNow, remember: copy.remember, title: copy.memoryCandidate, why: copy.memoryWhy },
      onMemory,
      onSkip: onSkipMemory,
    };
  }

  if (surfaceType === "MiniChoiceCard") {
    return {
      body: `${copy.followupReplies.draft_email} ${artifact.title}`,
      labels: { makeSofter: copy.makeSofter, makeStricter: copy.makeStricter, openArtifact: copy.openArtifact },
      onFullReview,
      title: copy.draftEmail,
    };
  }

  if (surfaceType === "MiniToolPreview") {
    return { body: copy.rendering, title: copy.approveRevision };
  }

  return { label: copy.approveRevision, onApprove };
}
