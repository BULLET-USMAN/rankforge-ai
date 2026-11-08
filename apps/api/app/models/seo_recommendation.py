from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SEORecommendation(Base):
    """
    Actionable SEO recommendation identified during auditing.
    """
    __tablename__ = "seo_recommendations"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    audit_result_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("audit_results.id", ondelete="SET NULL"), index=True, nullable=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # technical, performance, content, indexing
    severity: Mapped[str] = mapped_column(String(50), default="warning", nullable=False)  # critical, warning, info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_fix: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)  # open, approved, applied, dismissed

    project: Mapped["WebsiteProject"] = relationship("WebsiteProject", back_populates="recommendations")
    audit_result: Mapped[Optional["AuditResult"]] = relationship("AuditResult", back_populates="recommendations")
