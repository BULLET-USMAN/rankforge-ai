from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.rbac import RequireOrgRole
from app.db.session import get_db
from app.models.organization_member import OrganizationMember
from app.schemas.website import WebsiteCreate, WebsiteRead, WebsiteUpdate
from app.services.domain_normalizer import DomainValidationError
from app.services.website_service import WebsiteService

router = APIRouter()


@router.get(
    "/organizations/{org_id}/websites",
    response_model=List[WebsiteRead],
)
def list_workspace_websites(
    org_id: str,
    search: Optional[str] = Query(None, description="Search by name or domain"),
    include_archived: bool = Query(False, description="Include soft-deleted/archived projects"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """List all website projects in the workspace."""
    return WebsiteService.list_websites(
        db,
        organization_id=org_id,
        search=search,
        include_archived=include_archived,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/organizations/{org_id}/websites",
    response_model=WebsiteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace_website(
    org_id: str,
    payload: WebsiteCreate,
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """
    Add a new website project to the workspace.
    Domain is strictly normalized and validated against SSRF/private networks.
    Initial status is set to 'pending'.
    """
    try:
        return WebsiteService.create_website(
            db,
            organization_id=org_id,
            payload=payload,
            creator_id=membership.user_id,
        )
    except DomainValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/organizations/{org_id}/websites/{website_id}",
    response_model=WebsiteRead,
)
def get_workspace_website(
    org_id: str,
    website_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Retrieve website project details. Enforces workspace isolation."""
    website = WebsiteService.get_website(db, org_id, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found in this workspace.",
        )
    return website


@router.patch(
    "/organizations/{org_id}/websites/{website_id}",
    response_model=WebsiteRead,
)
def update_workspace_website(
    org_id: str,
    website_id: str,
    payload: WebsiteUpdate,
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """Update website project metadata (name, description)."""
    website = WebsiteService.get_website(db, org_id, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found in this workspace.",
        )
    return WebsiteService.update_website(db, website, payload)


@router.post(
    "/organizations/{org_id}/websites/{website_id}/archive",
    response_model=WebsiteRead,
)
def archive_workspace_website(
    org_id: str,
    website_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """Soft-delete / archive a website project."""
    website = WebsiteService.get_website(db, org_id, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found in this workspace.",
        )
    return WebsiteService.archive_website(db, website)


@router.post(
    "/organizations/{org_id}/websites/{website_id}/restore",
    response_model=WebsiteRead,
)
def restore_workspace_website(
    org_id: str,
    website_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """Restore an archived website project."""
    website = WebsiteService.get_website(db, org_id, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found in this workspace.",
        )
    return WebsiteService.restore_website(db, website)


@router.delete(
    "/organizations/{org_id}/websites/{website_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_workspace_website(
    org_id: str,
    website_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("admin")),
    db: Session = Depends(get_db),
):
    """Permanently delete a website project. Requires 'admin' or 'owner' role."""
    website = WebsiteService.get_website(db, org_id, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found in this workspace.",
        )
    WebsiteService.delete_website(db, website)
    return None
