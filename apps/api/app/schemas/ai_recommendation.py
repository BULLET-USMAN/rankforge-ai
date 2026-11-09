"""Pydantic schemas for AI recommendations and generation jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.ai.types import (
    RecommendationStatus,
    RecommendationType,
)


class RecommendationGenerateRequest(BaseModel):
    page_url: str = Field(..., max_length=2048, description="Target page URL for optimization")
    recommendation_type: RecommendationType = Field(
        default=RecommendationType.TITLE_OPTIMIZATION,
        description="Type of recommendation to generate",
    )
    audit_run_id: Optional[str] = Field(default=None, description="Optional audit run ID context")
    finding_id: Optional[str] = Field(
        default=None, description="Optional specific finding to address"
    )
    user_guidance: Optional[str] = Field(
        default=None, max_length=500, description="Optional user stylistic guidance"
    )


class BulkGenerateRequest(BaseModel):
    recommendation_types: List[RecommendationType] = Field(
        default=[RecommendationType.TITLE_OPTIMIZATION, RecommendationType.META_DESCRIPTION],
        description="Recommendation types to generate across pages",
    )
    audit_run_id: Optional[str] = Field(default=None, description="Optional audit run ID context")
    page_limit: int = Field(default=10, ge=1, le=20, description="Max pages to process")


class RecommendationEditRequest(BaseModel):
    suggested_value: Optional[str] = Field(
        default=None, max_length=5000, description="Manually edited suggestion"
    )
    status: Optional[RecommendationStatus] = Field(
        default=None, description="Updated proposal status"
    )
    user_guidance: Optional[str] = Field(
        default=None, max_length=500, description="User guidance notes"
    )


class RecommendationRejectRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500, description="Reason for rejection")


class RecommendationRegenerateRequest(BaseModel):
    user_guidance: Optional[str] = Field(
        default=None, max_length=500, description="Specific revision instructions"
    )


class AIRecommendationVersionRead(BaseModel):
    id: str
    version_number: int
    suggested_value: str
    explanation: Optional[str]
    user_guidance: Optional[str]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AIRecommendationRead(BaseModel):
    id: str
    organization_id: str
    website_project_id: str
    audit_run_id: Optional[str]
    source_crawl_id: Optional[str]
    source_finding_id: Optional[str]
    job_id: Optional[str]
    page_url: str
    recommendation_type: str
    status: str
    priority: str
    current_value: Optional[str]
    suggested_value: str
    explanation: str
    evidence_json: Dict[str, Any]
    limitations: Optional[str]
    alternative_suggestions: Optional[List[str]]
    prompt_template: str
    prompt_version: str
    model_identifier: str
    current_version_number: int
    created_by: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIRecommendationListResponse(BaseModel):
    items: List[AIRecommendationRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class AIGenerationJobRead(BaseModel):
    id: str
    organization_id: str
    website_project_id: str
    audit_run_id: Optional[str]
    status: str
    celery_task_id: Optional[str]
    recommendation_types: List[str]
    total_items: int
    completed_items: int
    failed_items: int
    error_message: Optional[str]
    created_by: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIUsageSummaryRead(BaseModel):
    daily_requests_used: int
    daily_requests_limit: int
    monthly_tokens_used: int
    monthly_tokens_limit: int
    monthly_estimated_cost_usd: float
    quota_status: str


class AIQuotaDetailsRead(BaseModel):
    daily_requests_limit: int
    monthly_token_limit: int
    max_batch_size: int
    max_concurrent_jobs: int
    estimated_input_cost_per_million: float
    estimated_output_cost_per_million: float
    provider: str
    model: str
