"""Custom exceptions for the AI Optimization Engine."""


class AIEngineException(Exception):
    """Base exception for AI engine errors."""

    pass


class AIProviderConfigurationError(AIEngineException):
    """Raised when the AI provider or API key is not configured."""

    pass


class AIProviderUnavailableError(AIEngineException):
    """Raised when the external AI provider is temporarily unavailable or timing out."""

    pass


class AIRateLimitExceededError(AIEngineException):
    """Raised when the AI provider returns a rate limit (HTTP 429)."""

    pass


class AIQuotaExhaustedError(AIEngineException):
    """Raised when the organization's daily requests or monthly token quota is exhausted."""

    pass


class AIValidationError(AIEngineException):
    """Raised when model output fails validation or violates security rules."""

    pass


class AIInsufficientContextError(AIEngineException):
    """Raised when crawl or audit data is insufficient to safely produce a recommendation."""

    pass
