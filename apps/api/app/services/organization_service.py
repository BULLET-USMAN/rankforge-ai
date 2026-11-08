import re
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.schemas.organization import OrganizationCreate, OrganizationUpdate

RESERVED_SLUGS = {
    "api",
    "admin",
    "app",
    "auth",
    "login",
    "register",
    "dashboard",
    "settings",
    "billing",
    "docs",
    "help",
    "support",
    "system",
    "null",
    "undefined",
    "root",
}


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug.strip("-")


class OrganizationService:
    """Manages tenant organizations, memberships, and role assignments."""

    @classmethod
    def create_organization(
        cls,
        db: Session,
        payload: OrganizationCreate,
        creator_id: Optional[str] = None,
    ) -> Organization:
        slug = payload.slug.lower().strip()
        if slug in RESERVED_SLUGS:
            raise ValueError(f"Slug '{slug}' is reserved by the platform.")

        org = Organization(
            name=payload.name.strip(),
            slug=slug,
            plan_tier=payload.plan_tier,
            created_by=creator_id,
        )
        db.add(org)
        db.flush()

        if creator_id:
            membership = OrganizationMember(
                organization_id=org.id,
                user_id=creator_id,
                role="owner",
            )
            db.add(membership)

        db.commit()
        db.refresh(org)
        return org

    @classmethod
    def get_organization_by_id(cls, db: Session, org_id: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.id == org_id).first()

    @classmethod
    def get_organization_by_slug(cls, db: Session, slug: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.slug == slug.lower().strip()).first()

    @classmethod
    def list_organizations(cls, db: Session, limit: int = 50) -> List[Organization]:
        return db.query(Organization).limit(limit).all()

    @classmethod
    def get_user_organizations(cls, db: Session, user_id: str) -> List[Organization]:
        return (
            db.query(Organization)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .filter(OrganizationMember.user_id == user_id)
            .order_by(Organization.name.asc())
            .all()
        )

    @classmethod
    def update_organization(
        cls, db: Session, org: Organization, payload: OrganizationUpdate
    ) -> Organization:
        if payload.name is not None:
            org.name = payload.name.strip()
        db.commit()
        db.refresh(org)
        return org
