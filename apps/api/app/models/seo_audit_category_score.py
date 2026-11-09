"""SEOAuditCategoryScore database model."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SEOAuditCategoryScore(Base):
    """
    Weighted category score breakdown for an audit run.
    """

    __tablename__ = "seo_audit_category_scores"

    audit_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("seo_audit_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)  # 0-100
    weight: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)  # e.g. 0.25

    findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_checks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    audit_run: Mapped["SEOAuditRun"] = relationship("SEOAuditRun", back_populates="category_scores")
