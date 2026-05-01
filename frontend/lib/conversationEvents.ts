export type ConversationEventType =
  | "user_message"
  | "agent_message"
  | "attachment"
  | "mini_surface"
  | "observation"
  | "memory_candidate"
  | "system_event"
  | "rich_surface_link";

export type ConversationEventStatus = "typing" | "rendering";

export type ConversationEvent =
  | {
      id: string;
      type: "user_message" | "agent_message" | "observation" | "system_event" | "rich_surface_link";
      content: string;
      status?: ConversationEventStatus;
      metadata?: Record<string, unknown>;
    }
  | {
      id: string;
      type: "attachment";
      fileName: string;
      detail: string;
      metadata?: Record<string, unknown>;
    }
  | {
      id: string;
      type: "mini_surface" | "memory_candidate";
      surface: string;
      metadata?: Record<string, unknown>;
    };

export function isPendingConversationEvent(event: ConversationEvent) {
  return "status" in event && (event.status === "typing" || event.status === "rendering");
}

export function settlePendingConversationEvents(events: ConversationEvent[]): ConversationEvent[] {
  return events.map((event) => (isPendingConversationEvent(event) ? { ...event, status: undefined } : event));
}
