from typing import Any, Dict, List

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditResult(Base):
    """
    Detailed technical audit findings for a target URL.
    """

    __tablename__ = "audit_results"

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("audit_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("website_projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    headers_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    ssl_info_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    robots_txt_found: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sitemap_found: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    issues_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    job: Mapped["AuditJob"] = relationship("AuditJob", back_populates="results")
    project: Mapped["WebsiteProject"] = relationship(
        "WebsiteProject", back_populates="audit_results"
    )
    recommendations: Mapped[List["SEORecommendation"]] = relationship(
        "SEORecommendation", back_populates="audit_result", cascade="all, delete-orphan"
    )
