"""SEOAuditFinding database model."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SEOAuditFinding(Base):
    """
    Individual technical SEO finding detected during an audit run.
    """
    __tablename__ = "seo_audit_findings"

    audit_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("seo_audit_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    website_project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )

    rule_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)

    page_url: Mapped[Optional[str]] = mapped_column(String(1024), index=True, nullable=True)  # None for site-wide
    severity: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )  # critical, high, medium, low, informational
    category: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )  # indexability, links_http, canonical, metadata, site_structure, headings, images, structured_data_sitemaps

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    finding_fingerprint: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    audit_run: Mapped["SEOAuditRun"] = relationship("SEOAuditRun", back_populates="findings")
