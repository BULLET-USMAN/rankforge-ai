"""Pydantic schemas for Google Search Console OAuth2 integration."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GoogleAuthUrlResponse(BaseModel):
    """Response containing Google OAuth2 consent URL and signed state."""

    authorization_url: str = Field(..., description="Google OAuth 2.0 authorization URL")
    state: str = Field(..., description="Signed CSRF state parameter")
    redirect_uri: str = Field(..., description="Callback redirect URI configured")


class GoogleIntegrationStatusResponse(BaseModel):
    """Safe status overview of Google Search Console connection."""

    is_connected: bool = Field(..., description="Whether a valid Google integration exists")
    connected_email: Optional[str] = Field(None, description="Connected Google account email")
    scopes: List[str] = Field(default_factory=list, description="Authorized Google OAuth scopes")
    expires_at: Optional[str] = Field(None, description="Access token expiration timestamp")
    is_active: bool = Field(False, description="Active status")
    organization_id: Optional[str] = Field(None, description="Workspace organization ID")
    website_project_id: Optional[str] = Field(None, description="Linked website project ID")


class GoogleDisconnectResponse(BaseModel):
    """Response confirming disconnection of Google Search Console."""

    success: bool = Field(True, description="Disconnection status")
    message: str = Field("Google Search Console integration successfully disconnected.")
