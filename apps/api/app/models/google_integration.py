"""Google Integration database model for Google Search Console OAuth2."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.services.crypto import decrypt_secret, encrypt_secret


class GoogleIntegration(Base):
    """
    Stores authorized Google Search Console OAuth2 credentials per tenant/project.
    Tokens are encrypted at rest using AES-128-CBC + HMAC via Fernet.
    """

    __tablename__ = "google_integrations"
    __table_args__ = (
        UniqueConstraint("organization_id", "website_project_id", name="uq_org_project_google"),
    )

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    website_project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("website_projects.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    google_account_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Encrypted token storage
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    token_type: Mapped[str] = mapped_column(String(32), default="Bearer", nullable=False)
    scopes_json: Mapped[List[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")  # noqa: F821
    project: Mapped[Optional["WebsiteProject"]] = relationship("WebsiteProject")  # noqa: F821
    creator: Mapped[Optional["Profile"]] = relationship("Profile")  # noqa: F821

    @property
    def access_token(self) -> str:
        """Decrypts and returns the plaintext access token."""
        return decrypt_secret(self.access_token_encrypted) or ""

    @access_token.setter
    def access_token(self, value: str) -> None:
        """Encrypts and stores the plaintext access token."""
        self.access_token_encrypted = encrypt_secret(value) or ""

    @property
    def refresh_token(self) -> Optional[str]:
        """Decrypts and returns the plaintext refresh token."""
        return decrypt_secret(self.refresh_token_encrypted)

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        """Encrypts and stores the plaintext refresh token."""
        self.refresh_token_encrypted = encrypt_secret(value) if value else None

    def to_dict(self) -> dict[str, Any]:
        """Safe dictionary representation without leaking tokens."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "website_project_id": self.website_project_id,
            "google_account_email": self.google_account_email,
            "scopes": self.scopes_json,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
