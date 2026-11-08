from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WebsiteCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    domain_or_url: str = Field(
        ...,
        min_length=3,
        max_length=1024,
        description="Target domain or URL (will be normalized and validated)",
    )
    description: Optional[str] = Field(None, max_length=500)


class WebsiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WebsiteRead(BaseModel):
    id: str
    organization_id: str
    name: str
    domain: str
    primary_url: str
    description: Optional[str] = None
    is_verified: bool
    verification_status: str
    verification_token: str
    created_by: Optional[str] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
