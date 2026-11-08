"""Recommendation review, approval, rejection, and versioning service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_recommendation import AIRecommendation
from app.models.ai_recommendation_version import AIRecommendationVersion
from app.services.ai.exceptions import AIValidationError
from app.services.ai.security import PromptSecuritySanitizer
from app.services.ai.types import RecommendationStatus


class RecommendationReviewService:
    """
    Manages proposal status transitions, version history, manual edits,
    and audit tracking.
    """

    @classmethod
    def approve(
        cls,
        db: Session,
        recommendation: AIRecommendation,
        user_id: str,
    ) -> AIRecommendation:
        """
        Approves an AI proposal.
        CRITICAL: This merely approves a proposed recommendation. It DOES NOT modify customer websites.
        """
        recommendation.status = RecommendationStatus.APPROVED.value
        recommendation.approved_by = user_id
        recommendation.approved_at = datetime.now(timezone.utc)
        recommendation.rejected_by = None
        recommendation.rejected_at = None
        recommendation.rejection_reason = None
        db.commit()
        db.refresh(recommendation)
        return recommendation

    @classmethod
    def reject(
        cls,
        db: Session,
        recommendation: AIRecommendation,
        user_id: str,
        reason: Optional[str] = None,
    ) -> AIRecommendation:
        """
        Rejects an AI proposal with an optional explanation.
        """
        recommendation.status = RecommendationStatus.REJECTED.value
        recommendation.rejected_by = user_id
        recommendation.rejected_at = datetime.now(timezone.utc)
        recommendation.rejection_reason = reason
        db.commit()
        db.refresh(recommendation)
        return recommendation

    @classmethod
    def save_draft(
        cls,
        db: Session,
        recommendation: AIRecommendation,
    ) -> AIRecommendation:
        """
        Saves a recommendation in draft state.
        """
        recommendation.status = RecommendationStatus.DRAFT.value
        db.commit()
        db.refresh(recommendation)
        return recommendation

    @classmethod
    def edit(
        cls,
        db: Session,
        recommendation: AIRecommendation,
        new_suggested_value: str,
        user_id: str,
        user_guidance: Optional[str] = None,
    ) -> AIRecommendation:
        """
        Manually edits a recommendation proposal.
        Creates a new version record and resets status to needs_review if previously approved.
        """
        cleaned_value = PromptSecuritySanitizer.sanitize_output_value(new_suggested_value)
        if not cleaned_value:
            raise AIValidationError("Suggested value cannot be empty.")

        # Increment version
        new_version_num = (recommendation.current_version_number or 1) + 1
        recommendation.current_version_number = new_version_num
        recommendation.suggested_value = cleaned_value

        # If it was approved, require re-review
        if recommendation.status == RecommendationStatus.APPROVED.value:
            recommendation.status = RecommendationStatus.NEEDS_REVIEW.value
            recommendation.approved_by = None
            recommendation.approved_at = None

        # Add version snapshot
        version_entry = AIRecommendationVersion(
            recommendation_id=recommendation.id,
            version_number=new_version_num,
            suggested_value=cleaned_value,
            explanation=recommendation.explanation,
            user_guidance=user_guidance,
            created_by=user_id,
        )
        db.add(version_entry)
        db.commit()
        db.refresh(recommendation)
        return recommendation

    @classmethod
    def get_history(cls, db: Session, recommendation_id: str) -> List[AIRecommendationVersion]:
        """
        Fetches all versions for a given recommendation.
        """
        stmt = (
            select(AIRecommendationVersion)
            .where(AIRecommendationVersion.recommendation_id == recommendation_id)
            .order_by(AIRecommendationVersion.version_number.desc())
        )
        return list(db.execute(stmt).scalars().all())
