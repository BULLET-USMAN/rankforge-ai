from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvitationCreate(BaseModel):
    invited_email: EmailStr
    invited_role: str = Field(default="viewer", pattern="^(admin|editor|viewer)$")


class InvitationRead(BaseModel):
    id: str
    organization_id: str
    invited_email: str
    invited_role: str
    invited_by: str
    inviter_name: Optional[str] = None
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    manual_link: Optional[str] = None  # Returned on creation for local development flow

    model_config = ConfigDict(from_attributes=True)


class InvitationAcceptRequest(BaseModel):
    token: str = Field(..., min_length=16)


class InvitationAcceptResponse(BaseModel):
    message: str
    organization_id: str
    organization_name: str
    role: str


OrganizationInvitationCreate = InvitationCreate
OrganizationInvitationRead = InvitationRead
