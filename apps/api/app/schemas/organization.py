import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

RESERVED_SLUGS = {
    "api",
    "admin",
    "dashboard",
    "auth",
    "login",
    "register",
    "settings",
    "billing",
    "team",
    "app",
    "help",
    "docs",
    "health",
    "webhook",
    "root",
}


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = Field(None, min_length=2, max_length=100)
    plan_tier: str = Field(default="starter")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.lower().strip()
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase alphanumeric characters and hyphens.")
        if v in RESERVED_SLUGS:
            raise ValueError(f"The slug '{v}' is reserved and cannot be used.")
        return v


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class OrganizationRead(BaseModel):
    id: str
    name: str
    slug: str
    plan_tier: str
    created_by: Optional[str] = None
    role: Optional[str] = None  # Role of the requesting user in this organization
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
