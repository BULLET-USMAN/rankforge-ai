"""Organization database model."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    """
    Tenant isolation boundary. All website projects, crawl jobs, audit runs,
    recommendations, invitations, and billing belong to an organization.
    """
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    plan_tier: Mapped[str] = mapped_column(String(50), default="starter", nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )

    creator: Mapped[Optional["Profile"]] = relationship("Profile", foreign_keys=[created_by])
    members: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember", back_populates="organization", cascade="all, delete-orphan"
    )
    invitations: Mapped[List["OrganizationInvitation"]] = relationship(
        "OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan"
    )
    projects: Mapped[List["WebsiteProject"]] = relationship(
        "WebsiteProject", back_populates="organization", cascade="all, delete-orphan"
    )
    crawl_jobs: Mapped[List["CrawlJob"]] = relationship(
        "CrawlJob", back_populates="organization", cascade="all, delete-orphan"
    )
    audit_runs: Mapped[List["SEOAuditRun"]] = relationship(
        "SEOAuditRun", back_populates="organization", cascade="all, delete-orphan"
    )
    audit_jobs: Mapped[List["AuditJob"]] = relationship(
        "AuditJob", back_populates="organization", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="organization", cascade="all, delete-orphan"
    )
    usage_events: Mapped[List["UsageEvent"]] = relationship(
        "UsageEvent", back_populates="organization", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="organization", cascade="all, delete-orphan"
    )
