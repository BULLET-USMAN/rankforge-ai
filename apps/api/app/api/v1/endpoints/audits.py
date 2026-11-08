from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.session import get_db
from app.models.audit_job import AuditJob
from app.models.website_project import WebsiteProject
from app.schemas.audit import AuditJobRead, AuditTriggerRequest
from app.services.audit_service import AuditService
from app.services.ssrf_guard import SSRFSecurityException

router = APIRouter()


@router.post("", response_model=AuditJobRead, status_code=status.HTTP_201_CREATED)
async def trigger_audit(payload: AuditTriggerRequest, db: Session = Depends(get_db)):
    """
    Trigger a technical SEO audit run for a project.
    Conducts real SSRF safety validation, protocol checks, and performance inspection.
    """
    project = db.query(WebsiteProject).filter(WebsiteProject.id == payload.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found.",
        )

    target_url = payload.target_url or project.primary_url

    # Create job entry
    job = AuditJob(
        project_id=project.id,
        organization_id=project.organization_id,
        job_type=payload.job_type,
        status="running",
        started_at=utc_now(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        await AuditService.perform_preflight_audit(db, job, project, target_url)
        job.status = "completed"
        job.completed_at = utc_now()
        db.commit()
        db.refresh(job)
    except SSRFSecurityException as ssrf_err:
        job.status = "failed"
        job.error_message = str(ssrf_err)
        job.completed_at = utc_now()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ssrf_err),
        )
    except Exception as exc:
        job.status = "failed"
        job.error_message = f"Audit execution failure: {str(exc)}"
        job.completed_at = utc_now()
        db.commit()

    return job


@router.get("/jobs/{job_id}", response_model=AuditJobRead)
def get_audit_job(job_id: str, db: Session = Depends(get_db)):
    """Retrieve audit job and associated results."""
    job = db.query(AuditJob).filter(AuditJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit job not found.",
        )
    return job


@router.get("/projects/{project_id}", response_model=List[AuditJobRead])
def list_project_audits(project_id: str, db: Session = Depends(get_db)):
    """List all audit runs conducted for a website project."""
    return (
        db.query(AuditJob)
        .filter(AuditJob.project_id == project_id)
        .order_by(AuditJob.created_at.desc())
        .limit(20)
        .all()
    )
