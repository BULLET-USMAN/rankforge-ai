"""Type definitions and schemas for the AI optimization engine."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendationType(str, Enum):
    TITLE_OPTIMIZATION = "title_optimization"
    META_DESCRIPTION = "meta_description"
    HEADING_STRUCTURE = "heading_structure"
    CONTENT_STRUCTURE = "content_structure"
    INTERNAL_LINKING = "internal_linking"
    IMAGE_ALT_GUIDANCE = "image_alt_guidance"


class RecommendationStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    OUTDATED = "outdated"


class RecommendationPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AIJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Structured AI output schema enforced by Gemini via response_schema
class RawAIOptimizationOutput(BaseModel):
    """
    Schema for structured JSON returned by the AI provider.
    Validated independently by the application layer.
    """
    suggested_value: str = Field(
        ...,
        description="The proposed SEO improvement, revised title, description, or structured heading recommendations.",
        max_length=5000,
    )
    explanation: str = Field(
        ...,
        description="Clear, professional explanation of why this change improves technical SEO or search appearance.",
        max_length=2000,
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Specific factual observations from the page and audit that support this proposal.",
    )
    limitations: Optional[str] = Field(
        default=None,
        description="Any uncertainties, missing data caveats, or notes for the human reviewer.",
        max_length=1000,
    )
    alternative_suggestions: Optional[List[str]] = Field(
        default=None,
        description="1-3 optional alternative variations for the user to select from.",
    )


class InternalLinkSuggestion(BaseModel):
    target_url: str = Field(..., description="Target internal page URL")
    suggested_anchor_text: str = Field(..., description="Recommended descriptive anchor text")
    context_sentence: str = Field(..., description="Context where link should be placed")
    relevance_reason: str = Field(..., description="Why these two pages are semantically related")


class AIProviderRequest(BaseModel):
    prompt_template: str
    prompt_version: str = "1.0"
    system_instruction: str
    user_content: str
    model: str = "gemini-2.5-flash"
    max_output_tokens: int = 2048
    temperature: float = 0.2


class AIProviderResponse(BaseModel):
    raw_text: str
    parsed_output: Optional[RawAIOptimizationOutput] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: str
    finish_reason: Optional[str] = None
