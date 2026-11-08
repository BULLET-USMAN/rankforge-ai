from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CrawlJob(Base):
    """
    Asynchronous website crawler execution record.
    Manages crawl progress, lifecycle states, and metrics.
    """
    __tablename__ = "crawl_jobs"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="queued", index=True, nullable=False
    )  # queued, running, completed, partially_completed, failed, cancelled
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    max_pages: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    max_depth: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    pages_crawled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_blocked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    config_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    project: Mapped["WebsiteProject"] = relationship("WebsiteProject", back_populates="crawl_jobs")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="crawl_jobs")
    pages: Mapped[List["CrawledPage"]] = relationship(
        "CrawledPage", back_populates="job", cascade="all, delete-orphan"
    )
    sitemaps: Mapped[List["SitemapDocument"]] = relationship(
        "SitemapDocument", back_populates="job", cascade="all, delete-orphan"
    )
