from typing import Any, Dict

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UsageEvent(Base):
    """
    Metered usage tracking (audit crawls, keyword checks, API calls).
    """
    __tablename__ = "usage_events"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="usage_events")
