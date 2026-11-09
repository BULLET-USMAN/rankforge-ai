"""API endpoints for Phase 4 SEO Technical Audits."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.rbac import RequireOrgRole
from app.db.session import get_db
from app.models.crawl_job import CrawlJob
from app.models.crawled_page import CrawledPage
from app.models.organization_member import OrganizationMember
from app.models.seo_audit_category_score import SEOAuditCategoryScore
from app.models.seo_audit_finding import SEOAuditFinding
from app.models.seo_audit_run import SEOAuditRun
from app.models.website_project import WebsiteProject
from app.models.website_verification import WebsiteVerification
from app.schemas.seo_audit import (
    AuditedPageRead,
    AuditTriggerRequest,
    SEOAuditCategoryScoreRead,
    SEOAuditComparisonRead,
    SEOAuditFindingListResponse,
    SEOAuditRunListResponse,
    SEOAuditRunRead,
)
from app.services.audit.audit_orchestrator import SEOAuditOrchestrator
from app.services.audit.comparison_service import AuditComparisonService
from app.services.website_service import WebsiteService
from services.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_project_or_404(db: Session, org_id: str, website_id: str) -> WebsiteProject:
    website = WebsiteService.get_website(db, org_id, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found in this workspace.",
        )
    return website


def _get_audit_or_404(db: Session, org_id: str, audit_id: str) -> SEOAuditRun:
    audit = (
        db.query(SEOAuditRun)
        .filter(SEOAuditRun.id == audit_id, SEOAuditRun.organization_id == org_id)
        .first()
    )
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SEO audit run not found in this workspace.",
        )
    return audit


@router.post(
    "/organizations/{org_id}/websites/{website_id}/audits",
    response_model=SEOAuditRunRead,
    status_code=status.HTTP_201_CREATED,
)
def trigger_seo_audit(
    org_id: str,
    website_id: str,
    payload: Optional[AuditTriggerRequest] = None,
    execute_sync: bool = Query(False, description="Run inline synchronously"),
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """
    Triggers an asynchronous technical SEO audit against a crawl snapshot.
    Enforces ownership verification and workspace tenant isolation.
    """
    project = _get_project_or_404(db, org_id, website_id)

    # 1. VERIFICATION GATE
    verification = (
        db.query(WebsiteVerification)
        .filter(
            WebsiteVerification.project_id == project.id,
            WebsiteVerification.status == "verified",
        )
        .first()
    )
    if not project.is_verified or not verification:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Website ownership must be verified before running technical SEO audits.",
        )

    # 2. RESOLVE CRAWL SNAPSHOT
    req = payload or AuditTriggerRequest()
    crawl_job_id = req.crawl_job_id

    if crawl_job_id:
        crawl_job = (
            db.query(CrawlJob)
            .filter(
                CrawlJob.id == crawl_job_id,
                CrawlJob.project_id == project.id,
                CrawlJob.organization_id == org_id,
            )
            .first()
        )
        if not crawl_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified crawl job snapshot not found for this website.",
            )
    else:
        # Pick the latest completed crawl job, or latest job with pages
        crawl_job = (
            db.query(CrawlJob)
            .filter(
                CrawlJob.project_id == project.id,
                CrawlJob.organization_id == org_id,
                CrawlJob.status == "completed",
            )
            .order_by(CrawlJob.created_at.desc())
            .first()
        )
        if not crawl_job:
            # Fallback to any job with crawled pages
            crawl_job = (
                db.query(CrawlJob)
                .filter(
                    CrawlJob.project_id == project.id,
                    CrawlJob.organization_id == org_id,
                    CrawlJob.pages_crawled > 0,
                )
                .order_by(CrawlJob.created_at.desc())
                .first()
            )

    if not crawl_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No crawl snapshots found for this website. Please perform a crawl first before running an audit.",
        )

    # 3. CREATE AUDIT RUN RECORD
    audit_run = SEOAuditRun(
        organization_id=org_id,
        website_project_id=project.id,
        crawl_job_id=crawl_job.id,
        status="queued",
        ruleset_version="v1.0.0",
        scoring_version="v1.0.0",
        created_by=membership.user_id,
    )
    db.add(audit_run)
    db.commit()
    db.refresh(audit_run)

    run_sync = execute_sync or req.execute_sync

    # 4. EXECUTE OR DISPATCH
    if run_sync:
        orchestrator = SEOAuditOrchestrator(db=db, audit_run_id=audit_run.id)
        orchestrator.run()
        db.refresh(audit_run)
    else:
        try:
            task = celery_app.send_task(
                "tasks.audit.execute_audit",
                args=[audit_run.id],
            )
            audit_run.celery_task_id = task.id
            db.commit()
            db.refresh(audit_run)
        except Exception as exc:
            logger.warning("Could not dispatch Celery task, falling back to sync run: %s", exc)
            orchestrator = SEOAuditOrchestrator(db=db, audit_run_id=audit_run.id)
            orchestrator.run()
            db.refresh(audit_run)

    return audit_run


@router.get(
    "/organizations/{org_id}/websites/{website_id}/audits",
    response_model=SEOAuditRunListResponse,
)
def list_website_audits(
    org_id: str,
    website_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Lists historical technical SEO audit runs for a website project."""
    _get_project_or_404(db, org_id, website_id)

    query = (
        db.query(SEOAuditRun)
        .filter(
            SEOAuditRun.organization_id == org_id,
            SEOAuditRun.website_project_id == website_id,
        )
        .order_by(SEOAuditRun.created_at.desc())
    )

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return SEOAuditRunListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/organizations/{org_id}/audits/{audit_id}",
    response_model=SEOAuditRunRead,
)
def get_audit_run(
    org_id: str,
    audit_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Retrieves full details and category scores for a specific SEO audit run."""
    audit = _get_audit_or_404(db, org_id, audit_id)
    return audit


@router.get(
    "/organizations/{org_id}/audits/{audit_id}/findings",
    response_model=SEOAuditFindingListResponse,
)
def list_audit_findings(
    org_id: str,
    audit_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    rule_id: Optional[str] = Query(None, description="Filter by rule ID"),
    page_url: Optional[str] = Query(None, description="Filter by exact page URL"),
    search: Optional[str] = Query(
        None, description="Text search across title, description, recommendation"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Lists audit findings with rich category, severity, and text search filtering."""
    _get_audit_or_404(db, org_id, audit_id)

    query = db.query(SEOAuditFinding).filter(
        SEOAuditFinding.audit_run_id == audit_id,
        SEOAuditFinding.organization_id == org_id,
    )

    if category:
        query = query.filter(SEOAuditFinding.category == category)
    if severity:
        query = query.filter(SEOAuditFinding.severity == severity)
    if rule_id:
        query = query.filter(SEOAuditFinding.rule_id == rule_id)
    if page_url:
        query = query.filter(SEOAuditFinding.page_url == page_url)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                SEOAuditFinding.title.ilike(search_filter),
                SEOAuditFinding.description.ilike(search_filter),
                SEOAuditFinding.recommendation.ilike(search_filter),
                SEOAuditFinding.page_url.ilike(search_filter),
            )
        )

    total = query.count()
    items = (
        query.order_by(
            SEOAuditFinding.severity.asc(),
            SEOAuditFinding.created_at.asc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return SEOAuditFindingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/organizations/{org_id}/audits/{audit_id}/scores",
    response_model=List[SEOAuditCategoryScoreRead],
)
def get_audit_category_scores(
    org_id: str,
    audit_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Retrieves the 8 category score breakdowns for an audit run."""
    _get_audit_or_404(db, org_id, audit_id)

    scores = (
        db.query(SEOAuditCategoryScore).filter(SEOAuditCategoryScore.audit_run_id == audit_id).all()
    )
    return scores


@router.get(
    "/organizations/{org_id}/audits/{audit_id}/compare/{previous_audit_id}",
    response_model=SEOAuditComparisonRead,
)
def compare_audit_runs(
    org_id: str,
    audit_id: str,
    previous_audit_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Compares current audit findings against a previous audit snapshot."""
    curr = _get_audit_or_404(db, org_id, audit_id)
    prev = _get_audit_or_404(db, org_id, previous_audit_id)

    comparison = AuditComparisonService.compare_audits(
        db=db,
        current_audit_id=curr.id,
        previous_audit_id=prev.id,
        organization_id=org_id,
    )

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to compare the requested audit runs.",
        )

    return comparison


@router.post(
    "/organizations/{org_id}/audits/{audit_id}/cancel",
    response_model=SEOAuditRunRead,
)
def cancel_audit_run(
    org_id: str,
    audit_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """Cancels an active or queued SEO audit run."""
    audit = _get_audit_or_404(db, org_id, audit_id)

    if audit.status in ("completed", "failed", "cancelled", "insufficient_coverage"):
        return audit

    audit.status = "cancelled"
    audit.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(audit)
    return audit


@router.get(
    "/organizations/{org_id}/audits/{audit_id}/pages",
    response_model=List[AuditedPageRead],
)
def list_audited_pages(
    org_id: str,
    audit_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Lists the pages evaluated in this audit run along with per-page finding counts."""
    audit = _get_audit_or_404(db, org_id, audit_id)

    pages = db.query(CrawledPage).filter(CrawledPage.job_id == audit.crawl_job_id).all()

    # Count findings per page_url
    counts_by_url: dict[str, int] = {}
    findings = (
        db.query(SEOAuditFinding.page_url, func.count(SEOAuditFinding.id))
        .filter(SEOAuditFinding.audit_run_id == audit.id)
        .group_by(SEOAuditFinding.page_url)
        .all()
    )
    for url, count in findings:
        if url:
            counts_by_url[url] = count

    result = []
    for p in pages:
        result.append(
            AuditedPageRead(
                url=p.url,
                normalized_url=p.normalized_url,
                status_code=p.status_code,
                response_time_ms=p.response_time_ms,
                depth=p.depth,
                title=p.title,
                canonical_url=p.canonical_url,
                meta_robots=p.meta_robots,
                h1_count=p.h1_count,
                images_count=p.images_count,
                images_missing_alt_count=p.images_missing_alt_count,
                findings_count=counts_by_url.get(p.url, 0),
            )
        )

    return result
