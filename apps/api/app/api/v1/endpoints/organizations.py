from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rbac import RequireOrgRole, get_current_user
from app.db.session import get_db
from app.models.organization_member import OrganizationMember
from app.models.profile import Profile
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new organization workspace. The creator is granted the 'owner' role."""
    existing = OrganizationService.get_organization_by_slug(db, payload.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization slug '{payload.slug}' is already registered.",
        )
    try:
        return OrganizationService.create_organization(db, payload, creator_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[OrganizationRead])
def list_my_organizations(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all organizations the authenticated user is a member of."""
    return OrganizationService.get_user_organizations(db, current_user.id)


@router.get("/{org_id}", response_model=OrganizationRead)
def get_organization(
    org_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Retrieve organization details. Requires membership in the workspace."""
    org = OrganizationService.get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return org


@router.patch("/{org_id}", response_model=OrganizationRead)
def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    membership: OrganizationMember = Depends(RequireOrgRole("owner")),
    db: Session = Depends(get_db),
):
    """Update workspace settings. Requires 'owner' role."""
    org = OrganizationService.get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return OrganizationService.update_organization(db, org, payload)
