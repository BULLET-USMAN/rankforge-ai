"""AIRecommendation database model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIRecommendation(Base):
    """
    Evidence-grounded, reviewable AI SEO recommendation proposal.
    """
    __tablename__ = "ai_recommendations"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    website_project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    audit_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("seo_audit_runs.id", ondelete="SET NULL"), index=True, nullable=True
    )
    source_crawl_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("crawl_jobs.id", ondelete="SET NULL"), index=True, nullable=True
    )
    source_finding_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("seo_audit_findings.id", ondelete="SET NULL"), index=True, nullable=True
    )
    job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ai_generation_jobs.id", ondelete="SET NULL"), index=True, nullable=True
    )

    page_url: Mapped[str] = mapped_column(String(2048), index=True, nullable=False)
    recommendation_type: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False
    )  # title_optimization, meta_description, heading_structure, content_structure, internal_linking, image_alt_guidance

    status: Mapped[str] = mapped_column(
        String(32), default="needs_review", index=True, nullable=False
    )  # draft, needs_review, approved, rejected, outdated

    priority: Mapped[str] = mapped_column(
        String(16), default="medium", index=True, nullable=False
    )  # high, medium, low

    current_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_value: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alternative_suggestions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    prompt_template: Mapped[str] = mapped_column(String(64), default="seo_title_v1", nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="1.0", nullable=False)
    model_identifier: Mapped[str] = mapped_column(String(64), default="gemini-2.5-flash", nullable=False)
    current_version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    job: Mapped[Optional["AIGenerationJob"]] = relationship("AIGenerationJob", back_populates="recommendations")
    source_finding: Mapped[Optional["SEOAuditFinding"]] = relationship("SEOAuditFinding")
    versions: Mapped[List["AIRecommendationVersion"]] = relationship(
        "AIRecommendationVersion",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        order_by="desc(AIRecommendationVersion.version_number)",
    )
