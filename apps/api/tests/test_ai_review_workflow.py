"""Tests for AI Recommendation review workflow, manual editing, and versioning."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ai_recommendation import AIRecommendation
from app.models.organization import Organization
from app.models.profile import Profile
from app.models.website_project import WebsiteProject
from app.services.ai.review_service import RecommendationReviewService
from app.services.ai.types import RecommendationStatus, RecommendationType


def test_review_workflow_and_version_history(db_session: Session):
    # Setup test org, user, website
    org = Organization(name="Review Org", slug="review-org-test")
    user = Profile(email="editor_review@example.com", full_name="SEO Editor")
    db_session.add_all([org, user])
    db_session.commit()

    website = WebsiteProject(
        organization_id=org.id,
        name="Review Site",
        domain="review.example.com",
        primary_url="https://review.example.com",
        verification_token="tok123",
    )
    db_session.add(website)
    db_session.commit()

    # Initial recommendation proposal
    rec = AIRecommendation(
        organization_id=org.id,
        website_project_id=website.id,
        page_url="https://review.example.com/about",
        recommendation_type=RecommendationType.TITLE_OPTIMIZATION.value,
        status=RecommendationStatus.NEEDS_REVIEW.value,
        current_value="About Us",
        suggested_value="About Our Mission & Expert SEO Team | ReviewSite",
        explanation="Aligns title with page content and adds brand anchor.",
        current_version_number=1,
    )
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)

    # 1. Approve recommendation
    rec = RecommendationReviewService.approve(db_session, rec, user_id=user.id)
    assert rec.status == RecommendationStatus.APPROVED.value
    assert rec.approved_by == user.id
    assert rec.approved_at is not None

    # CRITICAL CHECK: Ensure website entity was NOT modified
    db_session.refresh(website)
    assert website.primary_url == "https://review.example.com"

    # 2. Manual edit after approval -> resets to needs_review and increments version
    rec = RecommendationReviewService.edit(
        db=db_session,
        recommendation=rec,
        new_suggested_value="About Our Leadership Team | ReviewSite",
        user_id=user.id,
        user_guidance="Make it shorter",
    )
    assert rec.status == RecommendationStatus.NEEDS_REVIEW.value
    assert rec.current_version_number == 2
    assert rec.suggested_value == "About Our Leadership Team | ReviewSite"
    assert rec.approved_by is None

    # Verify version history records
    history = RecommendationReviewService.get_history(db_session, rec.id)
    assert len(history) == 1
    assert history[0].version_number == 2
    assert history[0].user_guidance == "Make it shorter"

    # 3. Reject recommendation
    rec = RecommendationReviewService.reject(db_session, rec, user_id=user.id, reason="Too generic")
    assert rec.status == RecommendationStatus.REJECTED.value
    assert rec.rejection_reason == "Too generic"
    assert rec.rejected_by == user.id

    # 4. Save as draft
    rec = RecommendationReviewService.save_draft(db_session, rec)
    assert rec.status == RecommendationStatus.DRAFT.value
