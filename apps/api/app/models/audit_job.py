from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditJob(Base):
    """
    Asynchronous audit task execution tracker.
    """
    __tablename__ = "audit_jobs"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(50), default="preflight", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    project: Mapped["WebsiteProject"] = relationship("WebsiteProject", back_populates="audit_jobs")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="audit_jobs")
    results: Mapped[List["AuditResult"]] = relationship(
        "AuditResult", back_populates="job", cascade="all, delete-orphan"
    )
