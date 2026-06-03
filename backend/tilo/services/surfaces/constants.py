from enum import StrEnum


class RichSurfaceTargetType(StrEnum):
    drawer = "drawer"
    page = "page"
    webview = "webview"


class RichSurfaceSource(StrEnum):
    policy = "policy"
    user_action = "user_action"
    channel_fallback = "channel_fallback"
