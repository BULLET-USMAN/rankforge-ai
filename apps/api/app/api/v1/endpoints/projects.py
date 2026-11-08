from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.website_project import WebsiteProject
from app.schemas.project import (
    VerificationStatusResponse,
    WebsiteProjectCreate,
    WebsiteProjectRead,
)
from app.services.organization_service import OrganizationService
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("", response_model=WebsiteProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: WebsiteProjectCreate, db: Session = Depends(get_db)):
    """Add a website project to an organization."""
    org = OrganizationService.get_organization_by_id(db, payload.organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return ProjectService.create_project(db, payload)


@router.get("", response_model=List[WebsiteProjectRead])
def list_projects(
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    db: Session = Depends(get_db),
):
    """List website projects."""
    if organization_id:
        return ProjectService.get_projects_by_org(db, organization_id)
    return db.query(WebsiteProject).limit(50).all()


@router.get("/{project_id}", response_model=WebsiteProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retrieve website project details."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found.",
        )
    return project


@router.get("/{project_id}/verification", response_model=VerificationStatusResponse)
def get_verification_instructions(
    project_id: str,
    method: str = Query("dns_txt", pattern="^(dns_txt|meta_tag|file_upload)$"),
    db: Session = Depends(get_db),
):
    """Retrieve DNS/Meta/File verification instructions for site ownership."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found.",
        )
    return ProjectService.get_verification_instructions(project, method=method)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a website project and its associated audit records."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found.",
        )
    db.delete(project)
    db.commit()
    return None
