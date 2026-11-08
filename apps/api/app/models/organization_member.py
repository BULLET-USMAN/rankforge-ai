from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrganizationMember(Base):
    """
    Membership linking a user profile to an organization with a role
    ('owner', 'admin', 'member').
    """
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="members")
    user: Mapped["Profile"] = relationship("Profile", back_populates="memberships")
