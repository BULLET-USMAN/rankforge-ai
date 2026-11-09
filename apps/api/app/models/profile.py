from __future__ import annotations

from typing import List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Profile(Base):
    """
    User profile entity, mapped 1:1 with Supabase Auth auth.users.
    """

    __tablename__ = "profiles"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)

    memberships: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember",
        foreign_keys="[OrganizationMember.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )
    sent_invitations: Mapped[List["OrganizationInvitation"]] = relationship(
        "OrganizationInvitation", back_populates="inviter", cascade="all, delete-orphan"
    )
