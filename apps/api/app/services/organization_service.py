from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate


class OrganizationService:
    """Manages tenant organizations."""

    @classmethod
    def create_organization(cls, db: Session, payload: OrganizationCreate) -> Organization:
        org = Organization(
            name=payload.name,
            slug=payload.slug.lower(),
            plan_tier=payload.plan_tier,
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org

    @classmethod
    def get_organization_by_id(cls, db: Session, org_id: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.id == org_id).first()

    @classmethod
    def get_organization_by_slug(cls, db: Session, slug: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.slug == slug.lower()).first()

    @classmethod
    def list_organizations(cls, db: Session, limit: int = 20) -> List[Organization]:
        return db.query(Organization).limit(limit).all()
