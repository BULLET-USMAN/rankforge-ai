"""AIRecommendationVersion database model."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIRecommendationVersion(Base):
    """
    Immutable version history snapshot for an AI recommendation proposal.
    """

    __tablename__ = "ai_recommendation_versions"
    __table_args__ = (
        UniqueConstraint("recommendation_id", "version_number", name="uq_rec_version"),
    )

    recommendation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_recommendations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    suggested_value: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )

    recommendation: Mapped["AIRecommendation"] = relationship(
        "AIRecommendation", back_populates="versions"
    )
