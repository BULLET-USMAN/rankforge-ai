"""Gemini API Provider implementation using official Google Gen AI SDK."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from app.core.config import settings
from app.services.ai.exceptions import (
    AIProviderConfigurationError,
    AIProviderUnavailableError,
    AIRateLimitExceededError,
    AIValidationError,
)
from app.services.ai.provider_interface import AIProviderInterface
from app.services.ai.types import (
    AIProviderRequest,
    AIProviderResponse,
    RawAIOptimizationOutput,
)

logger = logging.getLogger(__name__)


class GeminiProvider(AIProviderInterface):
    """
    Production Gemini integration utilizing google-genai SDK.
    Supports asynchronous execution, exponential backoff, structured output enforcement,
    and token usage tracking.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise AIProviderConfigurationError(
                "Gemini API key is not configured. Please configure GEMINI_API_KEY in environment variables."
            )
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            # Fast ping using minimal tokens
            from google.genai import types

            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self.model,
                    contents="ping",
                    config=types.GenerateContentConfig(max_output_tokens=5),
                ),
                timeout=5.0,
            )
            return response is not None
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

    async def generate(self, request: AIProviderRequest) -> AIProviderResponse:
        client = self._get_client()
        from google.genai import types

        model_name = request.model or self.model
        config = types.GenerateContentConfig(
            system_instruction=request.system_instruction,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
            response_mime_type="application/json",
            response_schema=RawAIOptimizationOutput,
        )

        max_retries = max(1, settings.AI_MAX_RETRIES)
        last_exception = None

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Submitting AI request to Gemini model={model_name} (attempt {attempt + 1}/{max_retries})"
                )
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model_name,
                        contents=request.user_content,
                        config=config,
                    ),
                    timeout=float(settings.AI_REQUEST_TIMEOUT_SECONDS),
                )

                raw_text = response.text or ""

                # Extract token usage metadata if provided by SDK
                input_tokens = 0
                output_tokens = 0
                total_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    meta = response.usage_metadata
                    input_tokens = getattr(meta, "prompt_token_count", 0) or 0
                    output_tokens = getattr(meta, "candidates_token_count", 0) or 0
                    total_tokens = getattr(meta, "total_token_count", 0) or (
                        input_tokens + output_tokens
                    )
                else:
                    # Conservative fallback estimate: 4 chars per token
                    input_tokens = len(request.user_content + request.system_instruction) // 4
                    output_tokens = len(raw_text) // 4
                    total_tokens = input_tokens + output_tokens

                # Parse and validate structured output
                try:
                    parsed_json = json.loads(raw_text)
                    parsed_output = RawAIOptimizationOutput(**parsed_json)
                except Exception as parse_err:
                    logger.error(
                        f"Failed to parse Gemini structured JSON: {parse_err}. Raw text: {raw_text[:200]}"
                    )
                    raise AIValidationError(
                        f"Invalid structured JSON received from AI provider: {parse_err}"
                    )

                return AIProviderResponse(
                    raw_text=raw_text,
                    parsed_output=parsed_output,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    model=model_name,
                    finish_reason="STOP",
                )

            except asyncio.TimeoutError:
                last_exception = AIProviderUnavailableError(
                    f"Gemini request timed out after {settings.AI_REQUEST_TIMEOUT_SECONDS}s"
                )
                logger.warning(f"Gemini timeout on attempt {attempt + 1}")
            except AIValidationError:
                raise
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                    last_exception = AIRateLimitExceededError(
                        f"Gemini API rate limit exceeded: {e}"
                    )
                elif "401" in error_str or "api_key_invalid" in error_str:
                    raise AIProviderConfigurationError(f"Invalid or revoked Gemini API key: {e}")
                else:
                    last_exception = AIProviderUnavailableError(f"Gemini API call failed: {e}")
                logger.warning(f"Gemini error on attempt {attempt + 1}: {e}")

            # Exponential backoff before next attempt
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)

        # Retries exhausted
        raise last_exception or AIProviderUnavailableError("Gemini service failed after retries")
