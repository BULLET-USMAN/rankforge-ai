"""AI Optimization Orchestrator coordinating generation, validation, and storage."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_generation_job import AIGenerationJob
from app.models.ai_recommendation import AIRecommendation
from app.models.ai_recommendation_version import AIRecommendationVersion
from app.models.crawled_page import CrawledPage
from app.models.seo_audit_finding import SEOAuditFinding
from app.models.seo_audit_run import SEOAuditRun
from app.models.website_project import WebsiteProject
from app.services.ai.context_builder import OptimizationContextBuilder
from app.services.ai.exceptions import (
    AIEngineException,
    AIValidationError,
)
from app.services.ai.factory import get_ai_provider
from app.services.ai.prioritizer import RecommendationPrioritizer
from app.services.ai.types import (
    AIJobStatus,
    AIProviderResponse,
    RawAIOptimizationOutput,
    RecommendationStatus,
    RecommendationType,
)
from app.services.ai.usage_meter import AIUsageMeter
from app.services.ai.validator import RecommendationValidator

logger = logging.getLogger(__name__)


class AIOptimizationOrchestrator:
    """
    Coordinates context building, provider execution, structured output validation,
    usage accounting, and database persistence.
    """

    @classmethod
    async def generate_single_recommendation(
        cls,
        db: Session,
        website: WebsiteProject,
        rec_type: RecommendationType,
        page_url: str,
        user_id: Optional[str] = None,
        audit_run_id: Optional[str] = None,
        finding_id: Optional[str] = None,
        user_guidance: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> AIRecommendation:
        """
        Executes single recommendation generation with quota check, provider call,
        validation, and persistent storage.
        """
        # Resolve audit run and finding if provided
        audit_run: Optional[SEOAuditRun] = None
        if audit_run_id:
            audit_run = db.get(SEOAuditRun, audit_run_id)

        finding: Optional[SEOAuditFinding] = None
        if finding_id:
            finding = db.get(SEOAuditFinding, finding_id)

        # 1. Build context
        request, evidence_meta = OptimizationContextBuilder.build_request(
            db=db,
            website=website,
            rec_type=rec_type,
            page_url=page_url,
            audit_run=audit_run,
            finding=finding,
            user_guidance=user_guidance,
        )

        # 2. Check quota
        AIUsageMeter.check_quotas(
            db, organization_id=website.organization_id, estimated_tokens=1500
        )

        # 3. Provider execution
        provider = get_ai_provider()
        response: AIProviderResponse = await provider.generate(request)

        if not response.parsed_output:
            raise AIValidationError("AI provider did not return structured output.")

        # 4. Independent validation & sanitization
        validated_output: RawAIOptimizationOutput = RecommendationValidator.validate_and_clean(
            output=response.parsed_output,
            rec_type=rec_type,
            evidence_meta=evidence_meta,
        )

        # 5. Prioritization
        current_val = evidence_meta.get(
            "current_title"
            if rec_type == RecommendationType.TITLE_OPTIMIZATION
            else "current_description"
        )
        priority = RecommendationPrioritizer.calculate_priority(
            rec_type=rec_type,
            finding=finding,
            current_value=current_val,
        )

        # 6. Record usage
        AIUsageMeter.record_usage(
            db=db,
            organization_id=website.organization_id,
            user_id=user_id,
            job_id=job_id,
            request_type=rec_type.value,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            model=response.model,
            provider="gemini" if "mock" not in response.model else "mock",
            status="success",
        )

        # 7. Persist recommendation
        recommendation = AIRecommendation(
            organization_id=website.organization_id,
            website_project_id=website.id,
            audit_run_id=audit_run.id if audit_run else None,
            source_crawl_id=audit_run.crawl_job_id if audit_run else None,
            source_finding_id=finding.id if finding else None,
            job_id=job_id,
            page_url=page_url,
            recommendation_type=rec_type.value,
            status=RecommendationStatus.NEEDS_REVIEW.value,
            priority=priority.value,
            current_value=current_val,
            suggested_value=validated_output.suggested_value,
            explanation=validated_output.explanation,
            evidence_json={
                "supporting_evidence": validated_output.supporting_evidence,
                "meta": evidence_meta,
            },
            limitations=validated_output.limitations,
            alternative_suggestions=validated_output.alternative_suggestions,
            prompt_template=request.prompt_template,
            prompt_version=request.prompt_version,
            model_identifier=response.model,
            current_version_number=1,
            created_by=user_id,
        )
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)

        # 8. Create version 1 entry
        version_entry = AIRecommendationVersion(
            recommendation_id=recommendation.id,
            version_number=1,
            suggested_value=validated_output.suggested_value,
            explanation=validated_output.explanation,
            user_guidance=user_guidance,
            created_by=user_id,
        )
        db.add(version_entry)
        db.commit()

        return recommendation

    @classmethod
    async def regenerate_recommendation(
        cls,
        db: Session,
        recommendation: AIRecommendation,
        user_id: Optional[str] = None,
        user_guidance: Optional[str] = None,
    ) -> AIRecommendation:
        """
        Regenerates an existing recommendation proposal incorporating user guidance.
        Creates a new version snapshot while preserving history.
        """
        website = db.get(WebsiteProject, recommendation.website_project_id)
        if not website:
            raise AIEngineException("Associated website project not found.")

        rec_type = RecommendationType(recommendation.recommendation_type)
        audit_run = (
            db.get(SEOAuditRun, recommendation.audit_run_id)
            if recommendation.audit_run_id
            else None
        )
        finding = (
            db.get(SEOAuditFinding, recommendation.source_finding_id)
            if recommendation.source_finding_id
            else None
        )

        # Build context with guidance
        request, evidence_meta = OptimizationContextBuilder.build_request(
            db=db,
            website=website,
            rec_type=rec_type,
            page_url=recommendation.page_url,
            audit_run=audit_run,
            finding=finding,
            user_guidance=user_guidance,
        )

        # Check quota
        AIUsageMeter.check_quotas(
            db, organization_id=website.organization_id, estimated_tokens=1500
        )

        provider = get_ai_provider()
        response: AIProviderResponse = await provider.generate(request)

        if not response.parsed_output:
            raise AIValidationError("AI provider did not return structured output.")

        validated_output = RecommendationValidator.validate_and_clean(
            output=response.parsed_output,
            rec_type=rec_type,
            evidence_meta=evidence_meta,
        )

        # Record usage
        AIUsageMeter.record_usage(
            db=db,
            organization_id=website.organization_id,
            user_id=user_id,
            job_id=recommendation.job_id,
            request_type=f"{rec_type.value}_regenerate",
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            model=response.model,
            provider="gemini" if "mock" not in response.model else "mock",
            status="success",
        )

        # Update recommendation
        new_version_num = (recommendation.current_version_number or 1) + 1
        recommendation.current_version_number = new_version_num
        recommendation.suggested_value = validated_output.suggested_value
        recommendation.explanation = validated_output.explanation
        recommendation.limitations = validated_output.limitations
        recommendation.alternative_suggestions = validated_output.alternative_suggestions
        recommendation.status = RecommendationStatus.NEEDS_REVIEW.value
        recommendation.approved_by = None
        recommendation.approved_at = None

        version_entry = AIRecommendationVersion(
            recommendation_id=recommendation.id,
            version_number=new_version_num,
            suggested_value=validated_output.suggested_value,
            explanation=validated_output.explanation,
            user_guidance=user_guidance,
            created_by=user_id,
        )
        db.add(version_entry)
        db.commit()
        db.refresh(recommendation)

        return recommendation

    @classmethod
    async def run_batch_job(
        cls,
        db: Session,
        job_id: str,
    ) -> None:
        """
        Executes an asynchronous bulk recommendation job with partial failure tolerance.
        """
        job = db.get(AIGenerationJob, job_id)
        if not job:
            logger.error(f"AI Generation job not found: {job_id}")
            return

        if job.status == AIJobStatus.CANCELLED.value:
            logger.info(f"AI Generation job {job_id} was cancelled before execution.")
            return

        website = db.get(WebsiteProject, job.website_project_id)
        if not website:
            job.status = AIJobStatus.FAILED.value
            job.error_message = "Website project not found."
            db.commit()
            return

        job.status = AIJobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # Gather target pages
        rec_types = [
            RecommendationType(t)
            for t in job.recommendation_types
            if t in RecommendationType._value2member_map_
        ]
        if not rec_types:
            rec_types = [RecommendationType.TITLE_OPTIMIZATION, RecommendationType.META_DESCRIPTION]

        # Fetch up to 10 crawled pages for this website
        crawled_pages_stmt = (
            select(CrawledPage.url)
            .where(
                CrawledPage.project_id == website.id,
                CrawledPage.status_code == 200,
            )
            .limit(10)
        )
        page_urls = list(db.execute(crawled_pages_stmt).scalars().all())
        if not page_urls:
            page_urls = [website.primary_url]

        total_work_items = len(page_urls) * len(rec_types)
        job.total_items = total_work_items
        job.completed_items = 0
        job.failed_items = 0
        db.commit()

        for page_url in page_urls:
            for rec_type in rec_types:
                # Check cancellation between items
                db.refresh(job)
                if job.status == AIJobStatus.CANCELLED.value:
                    logger.info(f"AI Generation job {job_id} cancelled during processing.")
                    return

                try:
                    await cls.generate_single_recommendation(
                        db=db,
                        website=website,
                        rec_type=rec_type,
                        page_url=page_url,
                        user_id=job.created_by,
                        audit_run_id=job.audit_run_id,
                        job_id=job.id,
                    )
                    job.completed_items += 1
                except Exception as e:
                    logger.warning(
                        f"Failed item in AI job {job_id} ({rec_type.value} for {page_url}): {e}"
                    )
                    job.failed_items += 1
                    # Record failed usage attempt if not already recorded
                db.commit()

        job.completed_at = datetime.now(timezone.utc)
        if job.failed_items == job.total_items and job.total_items > 0:
            job.status = AIJobStatus.FAILED.value
            job.error_message = "All recommendation generation attempts failed."
        else:
            job.status = AIJobStatus.COMPLETED.value

        db.commit()
