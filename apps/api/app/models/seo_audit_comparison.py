"""SEOAuditComparison database model."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SEOAuditComparison(Base):
    """
    Historical differential comparison between two completed audit snapshots.
    """

    __tablename__ = "seo_audit_comparisons"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    website_project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("website_projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    current_audit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("seo_audit_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    previous_audit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("seo_audit_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    score_change: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resolved_findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    persisting_findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    comparison_data_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    current_audit: Mapped["SEOAuditRun"] = relationship(
        "SEOAuditRun", foreign_keys=[current_audit_id]
    )
    previous_audit: Mapped["SEOAuditRun"] = relationship(
        "SEOAuditRun", foreign_keys=[previous_audit_id]
    )
