from typing import Any, Dict, Optional

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ActivityLog(Base):
    """
    Audit trail for multi-tenant actions and state changes.
    """

    __tablename__ = "activity_logs"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="activity_logs"
    )
    user: Mapped[Optional["Profile"]] = relationship("Profile", back_populates="activity_logs")
