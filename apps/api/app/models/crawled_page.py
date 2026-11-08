"""CrawledPage database model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CrawledPage(Base):
    """
    Extracted page metadata and structural inventory captured during a crawl job.
    """
    __tablename__ = "crawled_pages"

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )

    url: Mapped[str] = mapped_column(String(1024), index=True, nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(1024), index=True, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    byte_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discovery_method: Mapped[str] = mapped_column(
        String(50), default="hyperlink", nullable=False
    )  # seed, sitemap, hyperlink

    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    meta_robots: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    x_robots_tag: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    h1_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    headings_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    images_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    images_missing_alt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    images_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    structured_data_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    redirect_chain_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    internal_links_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external_links_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    links_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_details: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    job: Mapped["CrawlJob"] = relationship("CrawlJob", back_populates="pages")
    project: Mapped["WebsiteProject"] = relationship("WebsiteProject", back_populates="crawled_pages")
