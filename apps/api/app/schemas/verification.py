"""Pydantic schemas for domain ownership verification."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VerificationInitiateRequest(BaseModel):
    """Request payload to initiate domain verification."""
    method: str = Field(
        default="dns_txt",
        pattern=r"^(dns_txt|html_file)$",
        description="Verification method: 'dns_txt' or 'html_file'"
    )


class VerificationStatusResponse(BaseModel):
    """Full details of a website's verification challenge."""
    project_id: str
    domain: str
    method: str
    status: str  # pending, verified, failed, revoked, expired
    token: Optional[str] = None
    txt_record_name: Optional[str] = None
    txt_record_value: Optional[str] = None
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    last_checked_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VerificationCheckResponse(BaseModel):
    """Response returned upon checking verification status."""
    is_verified: bool
    status: str
    message: str
    failure_reason: Optional[str] = None
    verified_at: Optional[datetime] = None
