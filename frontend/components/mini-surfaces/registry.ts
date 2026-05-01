import type { ComponentType } from "react";
import { MiniApprovalCard } from "./MiniApprovalCard";
import { MiniChoiceCard } from "./MiniChoiceCard";
import { MiniIssueCard } from "./MiniIssueCard";
import { MiniMemoryCard } from "./MiniMemoryCard";
import { MiniRevisionPreview } from "./MiniRevisionPreview";
import { MiniToolPreview } from "./MiniToolPreview";

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
  supportedChannels: Array<"web" | "telegram" | "text">;
  fallback: "text" | "rich_surface_link";
  component: ComponentType<any>;
};

export const miniSurfaceRegistry: Record<MiniSurfaceType, MiniSurfaceRegistration> = {
  MiniIssueCard: { type: "MiniIssueCard", displayName: "Important issue", supportedChannels: ["web", "telegram", "text"], fallback: "rich_surface_link", component: MiniIssueCard },
  MiniApprovalCard: { type: "MiniApprovalCard", displayName: "Approval", supportedChannels: ["web", "telegram", "text"], fallback: "text", component: MiniApprovalCard },
  MiniRevisionPreview: { type: "MiniRevisionPreview", displayName: "Revision preview", supportedChannels: ["web", "text"], fallback: "rich_surface_link", component: MiniRevisionPreview },
  MiniMemoryCard: { type: "MiniMemoryCard", displayName: "Memory candidate", supportedChannels: ["web", "telegram", "text"], fallback: "text", component: MiniMemoryCard },
  MiniToolPreview: { type: "MiniToolPreview", displayName: "Tool call preview", supportedChannels: ["web", "telegram", "text"], fallback: "text", component: MiniToolPreview },
  MiniChoiceCard: { type: "MiniChoiceCard", displayName: "Choice", supportedChannels: ["web", "telegram", "text"], fallback: "text", component: MiniChoiceCard },
};

export function getMiniSurfaceRegistration(type: MiniSurfaceType) {
  return miniSurfaceRegistry[type];
}
