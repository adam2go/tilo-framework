import type { Artifact } from "./types";
import type { FollowUpIntent } from "./demoContracts";
import type { MiniSurfaceType } from "./miniSurfaceRegistry";

export type InteractionDecisionKind = "no_ui" | "mini_surface" | "rich_surface_link" | "ask_text";

export type InteractionPolicyContext = {
  event:
    | "artifact_ready"
    | "revision_approved"
    | "followup_received"
    | "memory_candidate_proposed"
    | "open_full_review"
    | "tool_call_requested";
  artifact?: Artifact | null;
  followUpIntent?: FollowUpIntent | null;
  riskLevel?: "high" | "medium" | "low" | string | null;
  confirmationRequired?: boolean;
  memoryCandidateConfidence?: number | null;
  visibleMiniSurfaceCount?: number;
  richSurfaceOpened?: boolean;
  channel?: "web" | "telegram";
};

export type InteractionDecision = {
  decision: InteractionDecisionKind;
  reason: string;
  surfaceType?: MiniSurfaceType;
  priority?: "high" | "medium" | "low";
};

export class InteractionPolicyService {
  evaluate(context: InteractionPolicyContext): InteractionDecision {
    const visibleMiniSurfaceCount = context.visibleMiniSurfaceCount || 0;

    if (context.event === "artifact_ready") {
      if (visibleMiniSurfaceCount > 0) {
        return { decision: "no_ui", reason: "mini_surface_budget_already_used", priority: "low" };
      }
      if (context.riskLevel === "high" || hasHighRiskArtifact(context.artifact)) {
        return {
          decision: "mini_surface",
          reason: "high_risk_human_confirmation_required",
          surfaceType: "MiniIssueCard",
          priority: "high",
        };
      }
      return { decision: "rich_surface_link", reason: "artifact_ready_without_decision_point", priority: "medium" };
    }

    if (context.event === "revision_approved") {
      if (visibleMiniSurfaceCount > 1) {
        return { decision: "no_ui", reason: "revision_preview_budget_guard", priority: "low" };
      }
      return {
        decision: "mini_surface",
        reason: "approved_revision_needs_compact_preview",
        surfaceType: "MiniRevisionPreview",
        priority: "medium",
      };
    }

    if (context.event === "followup_received") {
      if (context.followUpIntent === "revise_tone" || context.followUpIntent === "remember_preference") {
        return {
          decision: "mini_surface",
          reason: "followup_expressed_reusable_preference",
          surfaceType: "MiniMemoryCard",
          priority: "medium",
        };
      }
      if (context.followUpIntent === "draft_email") {
        return {
          decision: "mini_surface",
          reason: "draft_email_requires_user_choice_before_external_action",
          surfaceType: "MiniChoiceCard",
          priority: "medium",
        };
      }
      if (context.followUpIntent === "focus_clause" || context.followUpIntent === "explain_risk") {
        return { decision: "ask_text", reason: "text_response_is_enough_for_explanation", priority: "low" };
      }
      return { decision: "no_ui", reason: "general_followup_does_not_need_ui", priority: "low" };
    }

    if (context.event === "memory_candidate_proposed") {
      return {
        decision: "mini_surface",
        reason: "memory_requires_user_control",
        surfaceType: "MiniMemoryCard",
        priority: "medium",
      };
    }

    if (context.event === "open_full_review") {
      return { decision: "rich_surface_link", reason: "user_requested_complete_artifact", priority: "medium" };
    }

    if (context.event === "tool_call_requested") {
      if (context.confirmationRequired) {
        return {
          decision: "mini_surface",
          reason: "tool_call_requires_confirmation",
          surfaceType: "MiniToolPreview",
          priority: "high",
        };
      }
      return { decision: "no_ui", reason: "safe_tool_can_run_without_ui", priority: "low" };
    }

    return { decision: "no_ui", reason: "no_policy_match", priority: "low" };
  }
}

export const interactionPolicyService = new InteractionPolicyService();

function hasHighRiskArtifact(artifact?: Artifact | null) {
  const riskReview = artifact?.schema_json.blocks.find((block) => block.id === "risk_review" || block.type === "risk_review_panel");
  const risks = (riskReview?.data.risks as Array<Record<string, unknown>> | undefined) || [];
  return risks.some((risk) => String(risk.risk_level || "").toLowerCase() === "high");
}
