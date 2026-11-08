from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SitemapDocument(Base):
    """
    Sitemap documents discovered and parsed during a crawl job.
    """
    __tablename__ = "sitemap_documents"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    discovery_source: Mapped[str] = mapped_column(
        String(50), default="robots", nullable=False
    )  # robots, well_known, index
    status_code: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="discovered", nullable=False
    )  # discovered, parsed, failed
    urls_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_details: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    job: Mapped["CrawlJob"] = relationship("CrawlJob", back_populates="sitemaps")
    project: Mapped["WebsiteProject"] = relationship("WebsiteProject", back_populates="sitemaps")
