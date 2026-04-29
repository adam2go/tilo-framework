export type DemoContractFixture = {
  slug: string;
  file_name: string;
  title: string;
  content: string;
  source_path: string;
};

export type FollowUpIntent =
  | "explain_risk"
  | "revise_tone"
  | "focus_clause"
  | "draft_email"
  | "remember_preference"
  | "general_followup";

export type FollowUpIntentResult = {
  intent: FollowUpIntent;
  confidence: number;
  mode: "llm" | "deterministic" | string;
  reason: string;
};

export const SAMPLE_CONTRACT_FALLBACK_FILE_NAME = "AI 客服系统定制开发与运维服务合同（问题样例）.md";
