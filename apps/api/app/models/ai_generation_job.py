"""AIGenerationJob database model."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIGenerationJob(Base):
    """
    Asynchronous AI generation job record tracking recommendations batch.
    """

    __tablename__ = "ai_generation_jobs"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    website_project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("website_projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    audit_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("seo_audit_runs.id", ondelete="SET NULL"), index=True, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50), default="queued", index=True, nullable=False
    )  # queued, running, completed, failed, cancelled

    celery_task_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    recommendation_types: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    website_project: Mapped["WebsiteProject"] = relationship("WebsiteProject")
    audit_run: Mapped[Optional["SEOAuditRun"]] = relationship("SEOAuditRun")
    recommendations: Mapped[List["AIRecommendation"]] = relationship(
        "AIRecommendation", back_populates="job", cascade="all, delete-orphan"
    )
