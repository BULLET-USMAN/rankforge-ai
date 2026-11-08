"""Abstract base class for AI Providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.ai.types import AIProviderRequest, AIProviderResponse


class AIProviderInterface(ABC):
    """
    Contract that all AI backend providers (Gemini, Mock, etc.) must implement.
    """

    @abstractmethod
    async def generate(self, request: AIProviderRequest) -> AIProviderResponse:
        """
        Execute structured generation request.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and configured.
        """
        pass
