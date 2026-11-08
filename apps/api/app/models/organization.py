from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    """
    Tenant isolation boundary. All website projects, audit jobs,
    recommendations, and billing belong to an organization.
    """
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    plan_tier: Mapped[str] = mapped_column(String(50), default="starter", nullable=False)

    members: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember", back_populates="organization", cascade="all, delete-orphan"
    )
    projects: Mapped[List["WebsiteProject"]] = relationship(
        "WebsiteProject", back_populates="organization", cascade="all, delete-orphan"
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
