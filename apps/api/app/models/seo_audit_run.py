"""SEOAuditRun database model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SEOAuditRun(Base):
    """
    Technical SEO audit execution record analyzing a completed crawl snapshot.
    """
    __tablename__ = "seo_audit_runs"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    website_project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    crawl_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50), default="queued", index=True, nullable=False
    )  # queued, running, completed, partially_completed, failed, cancelled, insufficient_coverage
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    ruleset_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)

    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100 or None if insufficient coverage
    score_coverage: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # 0.0 - 1.0

    pages_evaluated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_not_evaluated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    info_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    summary_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="audit_runs")
    project: Mapped["WebsiteProject"] = relationship("WebsiteProject", back_populates="audit_runs")
    crawl_job: Mapped["CrawlJob"] = relationship("CrawlJob", back_populates="audit_runs")

    findings: Mapped[List["SEOAuditFinding"]] = relationship(
        "SEOAuditFinding", back_populates="audit_run", cascade="all, delete-orphan"
    )
    category_scores: Mapped[List["SEOAuditCategoryScore"]] = relationship(
        "SEOAuditCategoryScore", back_populates="audit_run", cascade="all, delete-orphan"
    )
