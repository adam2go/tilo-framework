from enum import StrEnum


class ConversationTurnType(StrEnum):
    user_message = "user_message"
    agent_message = "agent_message"
    attachment = "attachment"
    mini_surface = "mini_surface"
    observation = "observation"
    memory_candidate = "memory_candidate"
    memory_confirmed = "memory_confirmed"
    system_event = "system_event"
    rich_surface_link = "rich_surface_link"


class ConversationRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ConversationChannel(StrEnum):
    web = "web"
    telegram = "telegram"
    api = "api"
