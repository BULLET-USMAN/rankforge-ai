from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrganizationMemberRead(BaseModel):
    id: str
    organization_id: str
    user_id: str
    role: str
    email: str
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationMemberUpdate(BaseModel):
    role: str = Field(..., pattern="^(owner|admin|editor|viewer)$")


# Aliases for backward compatibility
MemberRead = OrganizationMemberRead
MemberRoleUpdate = OrganizationMemberUpdate
