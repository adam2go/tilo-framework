export type MiniSurfaceType =
  | "MiniIssueCard"
  | "MiniApprovalCard"
  | "MiniRevisionPreview"
  | "MiniMemoryCard"
  | "MiniToolPreview"
  | "MiniChoiceCard";

export type MiniSurfaceRegistration = {
  type: MiniSurfaceType;
  displayName: string;
  supportedChannels: Array<"web" | "telegram">;
  fallback: "text" | "rich_surface_link";
};

export const miniSurfaceRegistry: Record<MiniSurfaceType, MiniSurfaceRegistration> = {
  MiniIssueCard: {
    type: "MiniIssueCard",
    displayName: "Important issue",
    supportedChannels: ["web", "telegram"],
    fallback: "rich_surface_link",
  },
  MiniApprovalCard: {
    type: "MiniApprovalCard",
    displayName: "Approval",
    supportedChannels: ["web", "telegram"],
    fallback: "text",
  },
  MiniRevisionPreview: {
    type: "MiniRevisionPreview",
    displayName: "Revision preview",
    supportedChannels: ["web"],
    fallback: "rich_surface_link",
  },
  MiniMemoryCard: {
    type: "MiniMemoryCard",
    displayName: "Memory candidate",
    supportedChannels: ["web", "telegram"],
    fallback: "text",
  },
  MiniToolPreview: {
    type: "MiniToolPreview",
    displayName: "Tool call preview",
    supportedChannels: ["web", "telegram"],
    fallback: "text",
  },
  MiniChoiceCard: {
    type: "MiniChoiceCard",
    displayName: "Choice",
    supportedChannels: ["web", "telegram"],
    fallback: "text",
  },
};

export function getMiniSurfaceRegistration(type: MiniSurfaceType) {
  return miniSurfaceRegistry[type];
}
