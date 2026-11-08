from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WebsiteVerification(Base):
    """
    Website domain ownership verification record.
    Supports DNS TXT record and HTML verification file methods.
    """
    __tablename__ = "website_verifications"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # dns_txt, file_upload, meta_tag
    token: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True, nullable=False
    )  # pending, verified, failed, expired, revoked
    txt_record_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    txt_record_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_content: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["WebsiteProject"] = relationship("WebsiteProject", back_populates="verifications")
