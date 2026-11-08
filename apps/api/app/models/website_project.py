from typing import List

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
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
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[str] = mapped_column(String(128), nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    verifications: Mapped[List["WebsiteVerification"]] = relationship(
        "WebsiteVerification", back_populates="project", cascade="all, delete-orphan"
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
