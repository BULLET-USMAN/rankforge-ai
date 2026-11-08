from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WebsiteVerification(Base):
    """
    Website domain ownership verification log (DNS TXT, meta tag, or file upload).
    """
    __tablename__ = "website_verifications"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("website_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # dns_txt, meta_tag, file_upload
    token: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, verified, failed
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["WebsiteProject"] = relationship("WebsiteProject", back_populates="verifications")
