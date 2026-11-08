"""AIQuotaReservation database model."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIQuotaReservation(Base):
    """
    Atomic quota reservation for concurrent background AI jobs.
    """
    __tablename__ = "ai_quota_reservations"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ai_generation_jobs.id", ondelete="CASCADE"), index=True, nullable=True
    )

    tokens_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="active", nullable=False
    )  # active, committed, released
