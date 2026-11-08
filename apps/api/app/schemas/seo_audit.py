"""Pydantic schemas for Phase 4 SEO Technical Audit Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditTriggerRequest(BaseModel):
    crawl_job_id: Optional[str] = Field(
        default=None,
        description="Optional crawl job ID to audit. If omitted, the latest completed crawl job for this project is audited.",
    )
    execute_sync: bool = Field(
        default=False,
        description="If True, executes synchronously in the request thread (recommended for tests or quick jobs).",
    )


class SEOAuditFindingRead(BaseModel):
    id: str
    audit_run_id: str
    organization_id: str
    website_project_id: str
    rule_id: str
    rule_version: str
    page_url: Optional[str] = None
    severity: str
    category: str
    title: str
    description: str
    evidence_json: Dict[str, Any] = Field(default_factory=dict)
    recommendation: str
    finding_fingerprint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SEOAuditFindingListResponse(BaseModel):
    items: List[SEOAuditFindingRead]
    total: int
    page: int
    page_size: int


class SEOAuditCategoryScoreRead(BaseModel):
    id: str
    audit_run_id: str
    category: str
    score: int
    weight: float
    findings_count: int
    passed_checks_count: int
    details_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SEOAuditRunRead(BaseModel):
    id: str
    organization_id: str
    website_project_id: str
    crawl_job_id: str
    status: str
    ruleset_version: str
    scoring_version: str
    score: Optional[int] = None
    score_coverage: float
    pages_evaluated: int
    pages_not_evaluated: int
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    summary_json: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime
    category_scores: Optional[List[SEOAuditCategoryScoreRead]] = None

    model_config = ConfigDict(from_attributes=True)


class SEOAuditRunListResponse(BaseModel):
    items: List[SEOAuditRunRead]
    total: int
    page: int
    page_size: int


class SEOAuditComparisonRead(BaseModel):
    id: str
    organization_id: str
    website_project_id: str
    current_audit_id: str
    previous_audit_id: str
    score_change: int
    new_findings_count: int
    resolved_findings_count: int
    persisting_findings_count: int
    comparison_data_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditedPageRead(BaseModel):
    url: str
    normalized_url: str
    status_code: int
    response_time_ms: float
    depth: int
    title: Optional[str] = None
    canonical_url: Optional[str] = None
    meta_robots: Optional[str] = None
    h1_count: int
    images_count: int
    images_missing_alt_count: int
    findings_count: int = 0
