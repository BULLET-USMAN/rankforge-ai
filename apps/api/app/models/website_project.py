from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WebsiteProject(Base):
    """
    Website project tracked within an organization.
    """
    __tablename__ = "website_projects"
    __table_args__ = (
        UniqueConstraint("organization_id", "domain", name="uq_org_domain"),
    )

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    primary_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    verification_token: Mapped[str] = mapped_column(String(128), nullable=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    creator: Mapped[Optional["Profile"]] = relationship("Profile", foreign_keys=[created_by])
    verifications: Mapped[List["WebsiteVerification"]] = relationship(
        "WebsiteVerification", back_populates="project", cascade="all, delete-orphan"
    )
    crawl_jobs: Mapped[List["CrawlJob"]] = relationship(
        "CrawlJob", back_populates="project", cascade="all, delete-orphan"
    )
    crawled_pages: Mapped[List["CrawledPage"]] = relationship(
        "CrawledPage", back_populates="project", cascade="all, delete-orphan"
    )
    sitemaps: Mapped[List["SitemapDocument"]] = relationship(
        "SitemapDocument", back_populates="project", cascade="all, delete-orphan"
    )
    audit_jobs: Mapped[List["AuditJob"]] = relationship(
        "AuditJob", back_populates="project", cascade="all, delete-orphan"
    )
    audit_results: Mapped[List["AuditResult"]] = relationship(
        "AuditResult", back_populates="project", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["SEORecommendation"]] = relationship(
        "SEORecommendation", back_populates="project", cascade="all, delete-orphan"
    )
