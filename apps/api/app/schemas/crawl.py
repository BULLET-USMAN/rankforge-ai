"""Pydantic schemas for asynchronous website crawling and page inventory."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CrawlJobCreate(BaseModel):
    """Payload to initiate a new asynchronous crawl."""
    max_pages: int = Field(default=50, ge=1, le=100, description="Page limit budget (max 100 for Phase 3)")
    max_depth: int = Field(default=3, ge=1, le=5, description="Maximum crawl traversal depth (max 5)")


class CrawlJobRead(BaseModel):
    """Summary of a crawl job execution and metrics."""
    id: str
    project_id: str
    organization_id: str
    status: str  # queued, running, completed, partially_completed, failed, cancelled
    celery_task_id: Optional[str] = None
    pages_crawled: int
    pages_discovered: int
    pages_failed: int
    pages_blocked: int
    max_pages: int
    max_depth: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CrawledPageRead(BaseModel):
    """Summary of an individual crawled web page."""
    id: str
    job_id: str
    project_id: str
    url: str
    normalized_url: str
    status_code: int
    response_time_ms: float
    content_type: Optional[str] = None
    byte_size: int
    depth: int
    discovery_method: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    meta_robots: Optional[str] = None
    h1_count: int
    internal_links_count: int
    external_links_count: int
    content_hash: Optional[str] = None
    error_details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CrawledPageDetail(CrawledPageRead):
    """Full detail of a crawled page, including discovered outbound links."""
    links_json: List[Dict[str, Any]] = []


class CrawlJobListResponse(BaseModel):
    """List of crawl jobs for a project."""
    items: List[CrawlJobRead]
    total: int


class CrawledPageListResponse(BaseModel):
    """Paginated list of crawled pages for a crawl job."""
    items: List[CrawledPageRead]
    total: int
    page: int
    page_size: int
