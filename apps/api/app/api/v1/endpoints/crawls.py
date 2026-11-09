"""API endpoints for website crawling and crawled pages inventory."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.rbac import RequireOrgRole
from app.db.session import get_db
from app.models.crawl_job import CrawlJob
from app.models.crawled_page import CrawledPage
from app.models.organization_member import OrganizationMember
from app.models.website_project import WebsiteProject
from app.models.website_verification import WebsiteVerification
from app.schemas.crawl import (
    CrawledPageDetail,
    CrawledPageListResponse,
    CrawlJobCreate,
    CrawlJobListResponse,
    CrawlJobRead,
)
from app.services.crawler.crawler_orchestrator import CrawlerOrchestrator
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


def _get_job_or_404(db: Session, org_id: str, job_id: str) -> CrawlJob:
    job = (
        db.query(CrawlJob).filter(CrawlJob.id == job_id, CrawlJob.organization_id == org_id).first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl job not found in this workspace.",
        )
    return job


@router.post(
    "/organizations/{org_id}/websites/{website_id}/crawls",
    response_model=CrawlJobRead,
    status_code=status.HTTP_201_CREATED,
)
def create_crawl_job(
    org_id: str,
    website_id: str,
    payload: CrawlJobCreate,
    execute_sync: bool = Query(False, description="Run inline synchronously (useful for testing)"),
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """
    Initiates an asynchronous crawl job for an authorized, verified website.
    Enforces the ownership verification prerequisite gate.
    """
    project = _get_project_or_404(db, org_id, website_id)

    # 1. VERIFICATION GATE:
    # Website ownership must be verified before starting crawls
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
            detail="Website domain ownership is not verified. Please verify domain ownership before initiating crawls.",
        )

    # 2. Prevent concurrent duplicate active crawls
    active_job = (
        db.query(CrawlJob)
        .filter(
            CrawlJob.project_id == project.id,
            CrawlJob.status.in_(["queued", "running"]),
        )
        .first()
    )
    if active_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An active crawl job ({active_job.id}) is already in progress for this website.",
        )

    # 3. Create job record
    job = CrawlJob(
        project_id=project.id,
        organization_id=org_id,
        status="queued",
        max_pages=payload.max_pages,
        max_depth=payload.max_depth,
        pages_crawled=0,
        pages_discovered=0,
        pages_failed=0,
        pages_blocked=0,
        config_json={"max_pages": payload.max_pages, "max_depth": payload.max_depth},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 4. Dispatch Celery task or execute inline
    if execute_sync:
        orchestrator = CrawlerOrchestrator(db=db, job_id=job.id)
        orchestrator.run()
        db.refresh(job)
    else:
        try:
            task = celery_app.send_task("tasks.crawler.execute_crawl", args=[job.id])
            job.celery_task_id = task.id
            db.commit()
            db.refresh(job)
        except Exception as exc:
            logger.warning(
                "Could not dispatch Celery task for crawl %s: %s. Executing inline fallback.",
                job.id,
                exc,
            )
            orchestrator = CrawlerOrchestrator(db=db, job_id=job.id)
            orchestrator.run()
            db.refresh(job)

    return job


@router.get(
    "/organizations/{org_id}/websites/{website_id}/crawls",
    response_model=CrawlJobListResponse,
)
def list_crawl_jobs(
    org_id: str,
    website_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Lists crawl history for a website project."""
    project = _get_project_or_404(db, org_id, website_id)

    query = db.query(CrawlJob).filter(CrawlJob.project_id == project.id)
    total = query.count()
    items = query.order_by(CrawlJob.created_at.desc()).offset(skip).limit(limit).all()

    return CrawlJobListResponse(items=items, total=total)


@router.get(
    "/organizations/{org_id}/crawls/{job_id}",
    response_model=CrawlJobRead,
)
def get_crawl_job(
    org_id: str,
    job_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Retrieves real-time status and metrics of a crawl job."""
    return _get_job_or_404(db, org_id, job_id)


@router.post(
    "/organizations/{org_id}/crawls/{job_id}/cancel",
    response_model=CrawlJobRead,
)
def cancel_crawl_job(
    org_id: str,
    job_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """Cancels an in-progress crawl job gracefully."""
    job = _get_job_or_404(db, org_id, job_id)

    if job.status in ("completed", "partially_completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a crawl job with status '{job.status}'.",
        )

    job.status = "cancelled"
    db.commit()
    db.refresh(job)
    return job


@router.get(
    "/organizations/{org_id}/crawls/{job_id}/pages",
    response_model=CrawledPageListResponse,
)
def list_crawled_pages(
    org_id: str,
    job_id: str,
    search: Optional[str] = Query(None, description="Search in URL or title"),
    status_filter: Optional[str] = Query(
        None, description="Filter: '200', '4xx', '5xx', 'blocked', 'failed'"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Lists discovered and parsed pages for a crawl job with filtering and pagination."""
    _get_job_or_404(db, org_id, job_id)

    query = db.query(CrawledPage).filter(CrawledPage.job_id == job_id)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (CrawledPage.url.ilike(search_term)) | (CrawledPage.title.ilike(search_term))
        )

    if status_filter:
        flt = status_filter.lower().strip()
        if flt == "200":
            query = query.filter(CrawledPage.status_code == 200)
        elif flt == "4xx":
            query = query.filter(CrawledPage.status_code >= 400, CrawledPage.status_code < 500)
        elif flt == "5xx":
            query = query.filter(CrawledPage.status_code >= 500)
        elif flt == "blocked":
            query = query.filter(CrawledPage.error_details.ilike("%robots.txt%"))
        elif flt == "failed":
            query = query.filter(
                (CrawledPage.status_code == 0) | (CrawledPage.error_details.isnot(None))
            )

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query.order_by(CrawledPage.depth.asc(), CrawledPage.created_at.asc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return CrawledPageListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/organizations/{org_id}/crawls/{job_id}/pages/{page_id}",
    response_model=CrawledPageDetail,
)
def get_crawled_page_detail(
    org_id: str,
    job_id: str,
    page_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Retrieves detailed technical SEO attributes and outbound links for a crawled page."""
    _get_job_or_404(db, org_id, job_id)

    page = (
        db.query(CrawledPage)
        .filter(CrawledPage.id == page_id, CrawledPage.job_id == job_id)
        .first()
    )
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawled page record not found.",
        )
    return page
