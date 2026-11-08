import secrets
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.website_project import WebsiteProject
from app.models.website_verification import WebsiteVerification
from app.schemas.project import VerificationStatusResponse, WebsiteProjectCreate


class ProjectService:
    """Manages website projects and domain verification tokens."""

    @classmethod
    def create_project(cls, db: Session, payload: WebsiteProjectCreate) -> WebsiteProject:
        token = f"rankforge_verify_{secrets.token_hex(16)}"
        project = WebsiteProject(
            organization_id=payload.organization_id,
            name=payload.name,
            domain=payload.domain.lower(),
            primary_url=payload.primary_url,
            is_verified=False,
            verification_token=token,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # Create default pending verification entry
        verification = WebsiteVerification(
            project_id=project.id,
            method="dns_txt",
            token=token,
            status="pending",
        )
        db.add(verification)
        db.commit()

        return project

    @classmethod
    def get_projects_by_org(cls, db: Session, org_id: str) -> List[WebsiteProject]:
        return db.query(WebsiteProject).filter(WebsiteProject.organization_id == org_id).all()

    @classmethod
    def get_project_by_id(cls, db: Session, project_id: str) -> Optional[WebsiteProject]:
        return db.query(WebsiteProject).filter(WebsiteProject.id == project_id).first()

    @classmethod
    def get_verification_instructions(
        cls, project: WebsiteProject, method: str = "dns_txt"
    ) -> VerificationStatusResponse:
        token = project.verification_token
        return VerificationStatusResponse(
            project_id=project.id,
            domain=project.domain,
            is_verified=project.is_verified,
            method=method,
            token=token,
            dns_txt_record=f"rankforge-verification={token}",
            meta_tag_snippet=f'<meta name="rankforge-site-verification" content="{token}" />',
            file_upload_path="/.well-known/rankforge-verification.txt",
            file_upload_content=token,
        )
