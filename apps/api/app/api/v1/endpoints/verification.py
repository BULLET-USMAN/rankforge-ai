"""API endpoints for domain ownership verification."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.rbac import RequireOrgRole
from app.db.session import get_db
from app.models.organization_member import OrganizationMember
from app.models.website_project import WebsiteProject
from app.schemas.verification import (
    VerificationCheckResponse,
    VerificationInitiateRequest,
    VerificationStatusResponse,
)
from app.services.verification_service import VerificationService
from app.services.website_service import WebsiteService

router = APIRouter()


def _get_project_or_404(db: Session, org_id: str, website_id: str) -> WebsiteProject:
    website = WebsiteService.get_website(db, org_id, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website project not found in this workspace.",
        )
    return website


@router.get(
    "/organizations/{org_id}/websites/{website_id}/verification",
    response_model=VerificationStatusResponse,
)
def get_verification_status(
    org_id: str,
    website_id: str,
    method: str = Query("dns_txt", pattern="^(dns_txt|html_file|file_upload)$"),
    membership: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """Retrieves the active verification instructions and status for a website."""
    project = _get_project_or_404(db, org_id, website_id)
    verif = VerificationService.get_or_create_challenge(db, project, method=method)

    return VerificationStatusResponse(
        project_id=project.id,
        domain=project.domain,
        method=verif.method,
        status=verif.status,
        token=verif.token,
        txt_record_name=verif.txt_record_name,
        txt_record_value=verif.txt_record_value,
        file_path=verif.file_path,
        file_content=verif.file_content,
        last_checked_at=verif.last_checked_at,
        failure_reason=verif.failure_reason,
        expires_at=verif.expires_at,
        verified_at=verif.verified_at,
    )


@router.post(
    "/organizations/{org_id}/websites/{website_id}/verification/initiate",
    response_model=VerificationStatusResponse,
)
def initiate_verification(
    org_id: str,
    website_id: str,
    payload: VerificationInitiateRequest,
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """Generates a fresh verification challenge token and instructions for the domain."""
    project = _get_project_or_404(db, org_id, website_id)
    verif = VerificationService.initiate_challenge(db, project, method=payload.method)

    return VerificationStatusResponse(
        project_id=project.id,
        domain=project.domain,
        method=verif.method,
        status=verif.status,
        token=verif.token,
        txt_record_name=verif.txt_record_name,
        txt_record_value=verif.txt_record_value,
        file_path=verif.file_path,
        file_content=verif.file_content,
        last_checked_at=verif.last_checked_at,
        failure_reason=verif.failure_reason,
        expires_at=verif.expires_at,
        verified_at=verif.verified_at,
    )


@router.post(
    "/organizations/{org_id}/websites/{website_id}/verification/check",
    response_model=VerificationCheckResponse,
)
def check_verification(
    org_id: str,
    website_id: str,
    method: str = Query("dns_txt", pattern="^(dns_txt|html_file|file_upload)$"),
    membership: OrganizationMember = Depends(RequireOrgRole("editor")),
    db: Session = Depends(get_db),
):
    """Triggers real-time DNS TXT or HTML verification challenge check."""
    project = _get_project_or_404(db, org_id, website_id)
    norm_method = "dns_txt" if method == "dns_txt" else "file_upload"

    if norm_method == "dns_txt":
        is_verified, message, verif = VerificationService.verify_dns_txt(db, project)
    else:
        is_verified, message, verif = VerificationService.verify_html_file(db, project)

    return VerificationCheckResponse(
        is_verified=is_verified,
        status=verif.status,
        message=message,
        failure_reason=verif.failure_reason,
        verified_at=verif.verified_at,
    )


@router.post(
    "/organizations/{org_id}/websites/{website_id}/verification/revoke",
    response_model=VerificationCheckResponse,
)
def revoke_verification(
    org_id: str,
    website_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("admin")),
    db: Session = Depends(get_db),
):
    """Revokes domain ownership verification status. Requires workspace admin or owner."""
    project = _get_project_or_404(db, org_id, website_id)
    VerificationService.revoke_verification(db, project)

    return VerificationCheckResponse(
        is_verified=False,
        status="revoked",
        message="Domain ownership verification has been revoked.",
        failure_reason=None,
        verified_at=None,
    )
