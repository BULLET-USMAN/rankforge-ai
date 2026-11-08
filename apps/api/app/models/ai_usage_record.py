"""AIUsageRecord database model."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIUsageRecord(Base):
    """
    Organization-level AI usage and cost accounting entry.
    """
    __tablename__ = "ai_usage_records"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), index=True, nullable=True
    )
    job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ai_generation_jobs.id", ondelete="SET NULL"), index=True, nullable=True
    )

    provider: Mapped[str] = mapped_column(String(50), default="gemini", nullable=False)
    model: Mapped[str] = mapped_column(String(50), default="gemini-2.5-flash", nullable=False)
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)  # title_optimization, bulk, regenerate, etc.

    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)  # success, failed, cancelled
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
