from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditTriggerRequest(BaseModel):
    project_id: str
    target_url: Optional[str] = None
    job_type: str = Field(default="preflight", pattern="^(preflight|technical_crawl)$")


class IssueItem(BaseModel):
    code: str
    severity: str  # critical, warning, info
    title: str
    description: str


class AuditResultRead(BaseModel):
    id: str
    job_id: str
    project_id: str
    url: str
    status_code: int
    response_time_ms: float
    headers_json: Dict[str, Any]
    ssl_info_json: Dict[str, Any]
    robots_txt_found: bool
    sitemap_found: bool
    issues_json: List[IssueItem]
    score: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditJobRead(BaseModel):
    id: str
    project_id: str
    organization_id: str
    job_type: str
    status: str
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    results: List[AuditResultRead] = []

    model_config = ConfigDict(from_attributes=True)
