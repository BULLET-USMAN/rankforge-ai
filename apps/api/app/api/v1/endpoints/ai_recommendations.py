"""API endpoints for Phase 5 AI-Powered SEO Recommendations."""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rbac import RequireOrgRole
from app.db.session import get_db
from app.models.ai_generation_job import AIGenerationJob
from app.models.ai_recommendation import AIRecommendation
from app.models.organization_member import OrganizationMember
from app.models.website_project import WebsiteProject
from app.schemas.ai_recommendation import (
    AIGenerationJobRead,
    AIQuotaDetailsRead,
    AIRecommendationListResponse,
    AIRecommendationRead,
    AIRecommendationVersionRead,
    AIUsageSummaryRead,
    BulkGenerateRequest,
    RecommendationEditRequest,
    RecommendationGenerateRequest,
    RecommendationRegenerateRequest,
    RecommendationRejectRequest,
)
from app.services.ai.exceptions import (
    AIInsufficientContextError,
    AIProviderConfigurationError,
    AIQuotaExhaustedError,
    AIValidationError,
)
from app.services.ai.orchestrator import AIOptimizationOrchestrator
from app.services.ai.review_service import RecommendationReviewService
from app.services.ai.types import (
    AIJobStatus,
    RecommendationStatus,
)
from app.services.ai.usage_meter import AIUsageMeter
from app.services.website_service import WebsiteService
from services.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_website_or_404(db: Session, org_id: str, website_id: str) -> WebsiteProject:
    website = WebsiteService.get_website(db, org_id, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found in this workspace.",
        )
    return website


def _get_recommendation_or_404(db: Session, org_id: str, rec_id: str) -> AIRecommendation:
    rec = db.get(AIRecommendation, rec_id)
    if not rec or rec.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI recommendation not found in this workspace.",
        )
    return rec


# --------------------------------------------------------------------------
# 1. Single Recommendation Generation
# --------------------------------------------------------------------------
@router.post(
    "/organizations/{org_id}/websites/{website_id}/ai/generate",
    response_model=AIRecommendationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a single evidence-based AI SEO recommendation",
)
async def generate_single_recommendation(
    org_id: str,
    website_id: str,
    payload: RecommendationGenerateRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
):
    website = _get_website_or_404(db, org_id, website_id)

    try:
        recommendation = await AIOptimizationOrchestrator.generate_single_recommendation(
            db=db,
            website=website,
            rec_type=payload.recommendation_type,
            page_url=payload.page_url,
            user_id=membership.user_id,
            audit_run_id=payload.audit_run_id,
            finding_id=payload.finding_id,
            user_guidance=payload.user_guidance,
        )
        return recommendation
    except AIProviderConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except AIQuotaExhaustedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )
    except AIInsufficientContextError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except AIValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Single AI recommendation generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {exc}",
        )


# --------------------------------------------------------------------------
# 2. Bulk Recommendation Generation
# --------------------------------------------------------------------------
@router.post(
    "/organizations/{org_id}/websites/{website_id}/ai/bulk-generate",
    response_model=AIGenerationJobRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue asynchronous batch recommendation generation job",
)
async def bulk_generate_recommendations(
    org_id: str,
    website_id: str,
    payload: BulkGenerateRequest,
    execute_sync: bool = Query(False),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
):
    website = _get_website_or_404(db, org_id, website_id)

    # Check quota before queueing
    try:
        AIUsageMeter.check_quotas(db, organization_id=org_id, estimated_tokens=5000)
    except AIQuotaExhaustedError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))

    job = AIGenerationJob(
        organization_id=org_id,
        website_project_id=website.id,
        audit_run_id=payload.audit_run_id,
        status=AIJobStatus.QUEUED.value,
        recommendation_types=[t.value for t in payload.recommendation_types],
        created_by=membership.user_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if execute_sync:
        await AIOptimizationOrchestrator.run_batch_job(db=db, job_id=job.id)
        db.refresh(job)
    else:
        try:
            async_result = celery_app.send_task(
                "tasks.ai.execute_batch_job",
                args=[job.id],
            )
            job.celery_task_id = async_result.id
            db.commit()
            db.refresh(job)
        except Exception as exc:
            logger.warning(
                "Celery dispatch failed (%s), job %s will remain queued.", exc, job.id
            )

    return job


# --------------------------------------------------------------------------
# 3. List Website Recommendations
# --------------------------------------------------------------------------
@router.get(
    "/organizations/{org_id}/websites/{website_id}/ai/recommendations",
    response_model=AIRecommendationListResponse,
    summary="List all AI recommendations for a website with filters and pagination",
)
def list_recommendations(
    org_id: str,
    website_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    type_filter: Optional[str] = Query(None, alias="recommendation_type"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
):
    _get_website_or_404(db, org_id, website_id)

    stmt = select(AIRecommendation).where(
        AIRecommendation.organization_id == org_id,
        AIRecommendation.website_project_id == website_id,
    )

    if status_filter:
        stmt = stmt.where(AIRecommendation.status == status_filter)
    if type_filter:
        stmt = stmt.where(AIRecommendation.recommendation_type == type_filter)
    if priority_filter:
        stmt = stmt.where(AIRecommendation.priority == priority_filter)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0

    items = list(
        db.execute(
            stmt.order_by(desc(AIRecommendation.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return AIRecommendationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# --------------------------------------------------------------------------
# 4. Job Status & Cancellation
# --------------------------------------------------------------------------
@router.get(
    "/organizations/{org_id}/ai/jobs/{job_id}",
    response_model=AIGenerationJobRead,
    summary="Get background AI generation job status and progress",
)
def get_job_status(
    org_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
):
    job = db.get(AIGenerationJob, job_id)
    if not job or job.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI generation job not found in this workspace.",
        )
    return job


@router.post(
    "/organizations/{org_id}/ai/jobs/{job_id}/cancel",
    response_model=AIGenerationJobRead,
    summary="Cancel a queued or running AI generation job",
)
def cancel_job(
    org_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
):
    job = db.get(AIGenerationJob, job_id)
    if not job or job.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI generation job not found in this workspace.",
        )
    if job.status in (AIJobStatus.QUEUED.value, AIJobStatus.RUNNING.value):
        job.status = AIJobStatus.CANCELLED.value
        db.commit()
        db.refresh(job)
    return job


# --------------------------------------------------------------------------
# 5. Recommendation Detail, Edit, Approve, Reject, Regenerate
# --------------------------------------------------------------------------
@router.get(
    "/organizations/{org_id}/ai/recommendations/{recommendation_id}",
    response_model=AIRecommendationRead,
    summary="Get full recommendation details",
)
def get_recommendation(
    org_id: str,
    recommendation_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
):
    return _get_recommendation_or_404(db, org_id, recommendation_id)


@router.patch(
    "/organizations/{org_id}/ai/recommendations/{recommendation_id}",
    response_model=AIRecommendationRead,
    summary="Edit recommendation content or save as draft",
)
def edit_recommendation(
    org_id: str,
    recommendation_id: str,
    payload: RecommendationEditRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
):
    rec = _get_recommendation_or_404(db, org_id, recommendation_id)

    if payload.suggested_value is not None:
        rec = RecommendationReviewService.edit(
            db=db,
            recommendation=rec,
            new_suggested_value=payload.suggested_value,
            user_id=membership.user_id,
            user_guidance=payload.user_guidance,
        )

    if payload.status == RecommendationStatus.DRAFT:
        rec = RecommendationReviewService.save_draft(db=db, recommendation=rec)

    return rec


@router.post(
    "/organizations/{org_id}/ai/recommendations/{recommendation_id}/approve",
    response_model=AIRecommendationRead,
    summary="Approve recommendation proposal (does not publish to website)",
)
def approve_recommendation(
    org_id: str,
    recommendation_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("admin")),
):
    rec = _get_recommendation_or_404(db, org_id, recommendation_id)
    return RecommendationReviewService.approve(db=db, recommendation=rec, user_id=membership.user_id)


@router.post(
    "/organizations/{org_id}/ai/recommendations/{recommendation_id}/reject",
    response_model=AIRecommendationRead,
    summary="Reject recommendation proposal",
)
def reject_recommendation(
    org_id: str,
    recommendation_id: str,
    payload: Optional[RecommendationRejectRequest] = None,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("admin")),
):
    rec = _get_recommendation_or_404(db, org_id, recommendation_id)
    reason = payload.reason if payload else None
    return RecommendationReviewService.reject(
        db=db, recommendation=rec, user_id=membership.user_id, reason=reason
    )


@router.post(
    "/organizations/{org_id}/ai/recommendations/{recommendation_id}/regenerate",
    response_model=AIRecommendationRead,
    summary="Regenerate recommendation proposal with optional user guidance",
)
async def regenerate_recommendation(
    org_id: str,
    recommendation_id: str,
    payload: Optional[RecommendationRegenerateRequest] = None,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
):
    rec = _get_recommendation_or_404(db, org_id, recommendation_id)
    guidance = payload.user_guidance if payload else None

    try:
        updated_rec = await AIOptimizationOrchestrator.regenerate_recommendation(
            db=db,
            recommendation=rec,
            user_id=membership.user_id,
            user_guidance=guidance,
        )
        return updated_rec
    except AIQuotaExhaustedError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    except AIProviderConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        logger.exception("Recommendation regeneration failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regeneration failed: {exc}",
        )


@router.get(
    "/organizations/{org_id}/ai/recommendations/{recommendation_id}/history",
    response_model=List[AIRecommendationVersionRead],
    summary="Get full version history for a recommendation",
)
def get_recommendation_history(
    org_id: str,
    recommendation_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
):
    _get_recommendation_or_404(db, org_id, recommendation_id)
    return RecommendationReviewService.get_history(db=db, recommendation_id=recommendation_id)


# --------------------------------------------------------------------------
# 6. Usage & Quotas
# --------------------------------------------------------------------------
@router.get(
    "/organizations/{org_id}/ai/usage",
    response_model=AIUsageSummaryRead,
    summary="Get real-time organization AI usage and estimated cost",
)
def get_usage(
    org_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
):
    return AIUsageMeter.get_organization_usage_summary(db=db, organization_id=org_id)


@router.get(
    "/organizations/{org_id}/ai/quotas",
    response_model=AIQuotaDetailsRead,
    summary="Get configured AI quota limits and model details",
)
def get_quotas(
    org_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
):
    return AIQuotaDetailsRead(
        daily_requests_limit=settings.AI_DAILY_ORG_REQUEST_LIMIT,
        monthly_token_limit=settings.AI_MONTHLY_ORG_TOKEN_LIMIT,
        max_batch_size=settings.AI_MAX_BATCH_SIZE,
        max_concurrent_jobs=settings.AI_MAX_CONCURRENT_JOBS_PER_ORG,
        estimated_input_cost_per_million=settings.AI_ESTIMATED_INPUT_COST_PER_MILLION,
        estimated_output_cost_per_million=settings.AI_ESTIMATED_OUTPUT_COST_PER_MILLION,
        provider=settings.AI_PROVIDER,
        model=settings.GEMINI_MODEL,
    )
