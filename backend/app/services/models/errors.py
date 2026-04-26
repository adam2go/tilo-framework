class ModelClientError(RuntimeError):
    """Base error for safe model gateway failures."""


class ModelDisabledError(ModelClientError):
    """Raised when LLM mode is disabled or unavailable."""


class ModelTimeoutError(ModelClientError):
    """Raised when a model request times out."""


class ModelProviderError(ModelClientError):
    """Raised when the OpenAI-compatible provider returns an error."""


class ModelInvalidJSONError(ModelClientError):
    """Raised when JSON mode returns invalid or non-object JSON."""
