from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    """Create a new organization workspace."""
    existing = OrganizationService.get_organization_by_slug(db, payload.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization slug '{payload.slug}' is already registered.",
        )
    return OrganizationService.create_organization(db, payload)


@router.get("", response_model=List[OrganizationRead])
def list_organizations(limit: int = 20, db: Session = Depends(get_db)):
    """List organizations."""
    return OrganizationService.list_organizations(db, limit=limit)


@router.get("/{org_id}", response_model=OrganizationRead)
def get_organization(org_id: str, db: Session = Depends(get_db)):
    """Retrieve organization by ID."""
    org = OrganizationService.get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return org
