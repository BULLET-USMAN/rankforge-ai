"""Unit tests for AI Provider abstraction, Mock Provider, and Factory."""

from __future__ import annotations

import pytest

from app.services.ai.exceptions import AIProviderConfigurationError
from app.services.ai.factory import get_ai_provider, set_provider_override
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.types import (
    AIProviderRequest,
    RawAIOptimizationOutput,
    RecommendationType,
)


@pytest.mark.asyncio
async def test_mock_provider_all_recommendation_types():
    provider = MockAIProvider()
    assert await provider.health_check() is True

    templates = [
        ("seo_title_v1", RecommendationType.TITLE_OPTIMIZATION),
        ("seo_description_v1", RecommendationType.META_DESCRIPTION),
        ("seo_headings_v1", RecommendationType.HEADING_STRUCTURE),
        ("seo_content_structure_v1", RecommendationType.CONTENT_STRUCTURE),
        ("seo_internal_links_v1", RecommendationType.INTERNAL_LINKING),
        ("seo_image_alt_v1", RecommendationType.IMAGE_ALT_GUIDANCE),
    ]

    for template_name, rec_type in templates:
        req = AIProviderRequest(
            prompt_template=template_name,
            system_instruction="Test system prompt",
            user_content=(
                "Page URL: https://example.com/services/seo\n"
                "Current Title: Old Title\n"
                "Primary H1: Advanced SEO Services\n"
                "AUTHORIZED ELIGIBLE TARGET PAGES ON THIS SITE:\n"
                "- https://example.com/pricing\n"
                "- https://example.com/case-studies\n"
            ),
        )
        resp = await provider.generate(req)
        assert resp is not None
        assert resp.parsed_output is not None
        assert isinstance(resp.parsed_output, RawAIOptimizationOutput)
        assert len(resp.parsed_output.suggested_value) > 0
        assert len(resp.parsed_output.explanation) > 0
        assert resp.input_tokens > 0
        assert resp.output_tokens > 0
        assert resp.total_tokens == resp.input_tokens + resp.output_tokens


@pytest.mark.asyncio
async def test_mock_provider_user_guidance():
    provider = MockAIProvider()
    req = AIProviderRequest(
        prompt_template="seo_title_v1",
        system_instruction="Test",
        user_content=(
            "Page URL: https://example.com/test\n"
            "Primary H1: Very Long Heading That Needs Concise Phrasing\n"
            "User Guidance: Keep it concise\n"
        ),
    )
    resp = await provider.generate(req)
    assert resp.parsed_output is not None
    assert len(resp.parsed_output.suggested_value) <= 50


@pytest.mark.asyncio
async def test_gemini_provider_missing_key_raises_configuration_error():
    provider = GeminiProvider(api_key=None)
    with pytest.raises(AIProviderConfigurationError) as exc_info:
        await provider.generate(
            AIProviderRequest(
                prompt_template="seo_title_v1",
                system_instruction="sys",
                user_content="user",
            )
        )
    assert "Gemini API key is not configured" in str(exc_info.value)
    assert await provider.health_check() is False


def test_factory_provider_override():
    mock = MockAIProvider(model="test-override-model")
    set_provider_override(mock)
    assert get_ai_provider() is mock
    set_provider_override(None)
