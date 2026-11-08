from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WebsiteProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(..., min_length=3, max_length=255, pattern=r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    primary_url: str = Field(..., max_length=1024)


class WebsiteProjectCreate(WebsiteProjectBase):
    organization_id: str


class WebsiteProjectRead(WebsiteProjectBase):
    id: str
    organization_id: str
    is_verified: bool
    verification_token: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationInitiateRequest(BaseModel):
    method: str = Field(..., pattern="^(dns_txt|meta_tag|file_upload)$")


class VerificationStatusResponse(BaseModel):
    project_id: str
    domain: str
    is_verified: bool
    method: str
    token: str
    dns_txt_record: str
    meta_tag_snippet: str
    file_upload_path: str
    file_upload_content: str
