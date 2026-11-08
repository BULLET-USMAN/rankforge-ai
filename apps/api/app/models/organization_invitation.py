from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrganizationInvitation(Base):
    """
    Invitation to join an organization with a specific role.
    Stores cryptographically secure SHA-256 token hashes.
    """
    __tablename__ = "organization_invitations"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    invited_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    invited_role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    invited_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="invitations")
    inviter: Mapped["Profile"] = relationship("Profile", back_populates="sent_invitations")
