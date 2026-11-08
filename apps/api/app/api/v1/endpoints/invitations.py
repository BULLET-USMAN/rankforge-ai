from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rbac import RequireOrgRole, get_current_user
from app.db.session import get_db
from app.models.organization_member import OrganizationMember
from app.models.profile import Profile
from app.schemas.organization_invitation import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    OrganizationInvitationCreate,
    OrganizationInvitationRead,
)
from app.services.invitation_service import InvitationService

router = APIRouter()


@router.get(
    "/organizations/{org_id}/invitations",
    response_model=List[OrganizationInvitationRead],
)
def list_pending_invitations(
    org_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("admin")),
    db: Session = Depends(get_db),
):
    """List pending invitations for the workspace. Requires 'admin' or 'owner' role."""
    invitations = InvitationService.list_pending_invitations(db, org_id)
    result = []
    for inv in invitations:
        inviter = db.query(Profile).filter(Profile.id == inv.invited_by).first()
        inviter_name = inviter.display_name or inviter.full_name if inviter else "Team Member"
        result.append(
            OrganizationInvitationRead(
                id=inv.id,
                organization_id=inv.organization_id,
                invited_email=inv.invited_email,
                invited_role=inv.invited_role,
                invited_by=inv.invited_by,
                inviter_name=inviter_name,
                expires_at=inv.expires_at,
                accepted_at=inv.accepted_at,
                revoked_at=inv.revoked_at,
                created_at=inv.created_at,
            )
        )
    return result


@router.post(
    "/organizations/{org_id}/invitations",
    response_model=OrganizationInvitationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    org_id: str,
    payload: OrganizationInvitationCreate,
    membership: OrganizationMember = Depends(RequireOrgRole("admin")),
    db: Session = Depends(get_db),
):
    """Invite a new member to the workspace. Requires 'admin' or 'owner' role."""
    # Prevent role escalation: admins cannot invite members with higher roles
    if membership.role != "owner" and payload.invited_role in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners can invite new admins or owners.",
        )

    try:
        invitation, raw_token = InvitationService.create_invitation(
            db,
            organization_id=org_id,
            invited_by_user_id=membership.user_id,
            invited_email=payload.invited_email,
            invited_role=payload.invited_role,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    inviter = db.query(Profile).filter(Profile.id == invitation.invited_by).first()
    inviter_name = inviter.display_name or inviter.full_name if inviter else "Team Member"

    manual_link = f"/invitations/accept?token={raw_token}"

    return OrganizationInvitationRead(
        id=invitation.id,
        organization_id=invitation.organization_id,
        invited_email=invitation.invited_email,
        invited_role=invitation.invited_role,
        invited_by=invitation.invited_by,
        inviter_name=inviter_name,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        revoked_at=invitation.revoked_at,
        created_at=invitation.created_at,
        manual_link=manual_link,
    )


@router.delete(
    "/organizations/{org_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_invitation(
    org_id: str,
    invitation_id: str,
    membership: OrganizationMember = Depends(RequireOrgRole("admin")),
    db: Session = Depends(get_db),
):
    """Revoke an active invitation."""
    try:
        InvitationService.revoke_invitation(db, invitation_id, org_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None


@router.post(
    "/invitations/accept",
    response_model=InvitationAcceptResponse,
)
def accept_invitation(
    payload: InvitationAcceptRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept an invitation to join an organization workspace."""
    try:
        member, org = InvitationService.accept_invitation(db, payload.token, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return InvitationAcceptResponse(
        message="Invitation accepted successfully.",
        organization_id=org.id,
        organization_name=org.name,
        role=member.role,
    )
