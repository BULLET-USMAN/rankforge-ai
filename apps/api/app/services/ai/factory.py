"""Factory for instantiating the configured AI Provider."""

from __future__ import annotations

import os
from typing import Optional

from app.core.config import settings
from app.services.ai.exceptions import AIProviderConfigurationError
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.provider_interface import AIProviderInterface

_override_provider: Optional[AIProviderInterface] = None


def set_provider_override(provider: Optional[AIProviderInterface]) -> None:
    """Override AI provider for test suites."""
    global _override_provider
    _override_provider = provider


def get_ai_provider() -> AIProviderInterface:
    """
    Returns the configured AI Provider instance.
    Enforces that Gemini API key is present when AI_PROVIDER is 'gemini'.
    """
    global _override_provider
    if _override_provider is not None:
        return _override_provider

    provider_type = (settings.AI_PROVIDER or "gemini").lower()

    if provider_type == "mock" or os.environ.get("PYTEST_CURRENT_TEST"):
        return MockAIProvider()

    if provider_type == "gemini":
        if not settings.GEMINI_API_KEY:
            raise AIProviderConfigurationError(
                "Gemini API key is not configured. Please configure GEMINI_API_KEY in environment variables."
            )
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)

    raise AIProviderConfigurationError(f"Unsupported AI_PROVIDER: {provider_type}")
