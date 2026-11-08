import secrets
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.website_project import WebsiteProject
from app.models.website_verification import WebsiteVerification
from app.schemas.website import WebsiteCreate, WebsiteUpdate
from app.services.domain_normalizer import DomainNormalizer


class WebsiteService:
    """Manages workspace website projects, domain normalization, and project lifecycle."""

    @classmethod
    def create_website(
        cls,
        db: Session,
        organization_id: str,
        payload: WebsiteCreate,
        creator_id: Optional[str] = None,
    ) -> WebsiteProject:
        normalized_domain, canonical_url = DomainNormalizer.normalize_and_validate(
            payload.domain_or_url
        )

        # Enforce unique active domain per organization workspace
        existing = (
            db.query(WebsiteProject)
            .filter(
                WebsiteProject.organization_id == organization_id,
                WebsiteProject.domain == normalized_domain,
                WebsiteProject.archived_at.is_(None),
            )
            .first()
        )
        if existing:
            raise ValueError(f"Domain '{normalized_domain}' is already registered in this workspace.")

        token = f"rankforge-site-verification={secrets.token_hex(16)}"

        project = WebsiteProject(
            organization_id=organization_id,
            name=payload.name.strip(),
            domain=normalized_domain,
            primary_url=canonical_url,
            description=payload.description.strip() if payload.description else None,
            is_verified=False,
            verification_status="pending",
            verification_token=token,
            created_by=creator_id,
        )
        db.add(project)
        db.flush()

        # Seed initial pending verification record
        verification = WebsiteVerification(
            project_id=project.id,
            method="dns_txt",
            token=token,
            status="pending",
        )
        db.add(verification)

        db.commit()
        db.refresh(project)
        return project

    @classmethod
    def list_websites(
        cls,
        db: Session,
        organization_id: str,
        search: Optional[str] = None,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[WebsiteProject]:
        query = db.query(WebsiteProject).filter(WebsiteProject.organization_id == organization_id)

        if not include_archived:
            query = query.filter(WebsiteProject.archived_at.is_(None))

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                (WebsiteProject.name.ilike(term)) | (WebsiteProject.domain.ilike(term))
            )

        return query.order_by(WebsiteProject.created_at.desc()).offset(skip).limit(limit).all()

    @classmethod
    def get_website(
        cls, db: Session, organization_id: str, website_id: str
    ) -> Optional[WebsiteProject]:
        return (
            db.query(WebsiteProject)
            .filter(
                WebsiteProject.id == website_id,
                WebsiteProject.organization_id == organization_id,
            )
            .first()
        )

    @classmethod
    def update_website(
        cls, db: Session, website: WebsiteProject, payload: WebsiteUpdate
    ) -> WebsiteProject:
        if payload.name is not None:
            website.name = payload.name.strip()
        if payload.description is not None:
            website.description = payload.description.strip() or None

        db.commit()
        db.refresh(website)
        return website

    @classmethod
    def archive_website(cls, db: Session, website: WebsiteProject) -> WebsiteProject:
        website.archived_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(website)
        return website

    @classmethod
    def restore_website(cls, db: Session, website: WebsiteProject) -> WebsiteProject:
        website.archived_at = None
        db.commit()
        db.refresh(website)
        return website

    @classmethod
    def delete_website(cls, db: Session, website: WebsiteProject) -> None:
        db.delete(website)
        db.commit()
