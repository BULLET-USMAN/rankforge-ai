from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rbac import RequireOrgRole
from app.db.session import get_db
from app.models.organization_member import OrganizationMember
from app.models.profile import Profile
from app.schemas.organization_member import (
    OrganizationMemberRead,
    OrganizationMemberUpdate,
)

router = APIRouter()


@router.get(
    "/organizations/{org_id}/members",
    response_model=List[OrganizationMemberRead],
)
def list_workspace_members(
    org_id: str,
    caller_member: OrganizationMember = Depends(RequireOrgRole("viewer")),
    db: Session = Depends(get_db),
):
    """List all members of the organization with their profile info and roles."""
    members = (
        db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).all()
    )

    result = []
    for m in members:
        user_profile = db.query(Profile).filter(Profile.id == m.user_id).first()
        result.append(
            OrganizationMemberRead(
                id=m.id,
                organization_id=m.organization_id,
                user_id=m.user_id,
                role=m.role,
                email=user_profile.email if user_profile else "unknown@rankforge.ai",
                full_name=user_profile.full_name if user_profile else None,
                display_name=user_profile.display_name if user_profile else None,
                avatar_url=user_profile.avatar_url if user_profile else None,
                created_at=m.created_at,
            )
        )
    return result


@router.patch(
    "/organizations/{org_id}/members/{member_id}",
    response_model=OrganizationMemberRead,
)
def update_member_role(
    org_id: str,
    member_id: str,
    payload: OrganizationMemberUpdate,
    caller_member: OrganizationMember = Depends(RequireOrgRole("admin")),
    db: Session = Depends(get_db),
):
    """Change a team member's role. Enforces RBAC constraints and prevents demoting the last owner."""
    target_member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org_id,
        )
        .first()
    )
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization.",
        )

    # Disallow modifying own role
    if target_member.id == caller_member.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot modify your own role.",
        )

    # Admin cannot touch owner or promote to owner
    if caller_member.role != "owner":
        if target_member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owners can alter an owner's role.",
            )
        if payload.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owners can promote members to owner.",
            )

    # Prevent demoting the final owner
    if target_member.role == "owner" and payload.role != "owner":
        owner_count = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.role == "owner",
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the final workspace owner.",
            )

    target_member.role = payload.role
    db.commit()
    db.refresh(target_member)

    user_profile = db.query(Profile).filter(Profile.id == target_member.user_id).first()
    return OrganizationMemberRead(
        id=target_member.id,
        organization_id=target_member.organization_id,
        user_id=target_member.user_id,
        role=target_member.role,
        email=user_profile.email if user_profile else "unknown@rankforge.ai",
        full_name=user_profile.full_name if user_profile else None,
        display_name=user_profile.display_name if user_profile else None,
        avatar_url=user_profile.avatar_url if user_profile else None,
        created_at=target_member.created_at,
    )


@router.delete(
    "/organizations/{org_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    org_id: str,
    member_id: str,
    caller_member: OrganizationMember = Depends(RequireOrgRole("admin")),
    db: Session = Depends(get_db),
):
    """Remove a member from the workspace."""
    target_member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org_id,
        )
        .first()
    )
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization.",
        )

    # Admin cannot remove an owner
    if caller_member.role != "owner" and target_member.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners can remove an owner.",
        )

    # Cannot remove final owner
    if target_member.role == "owner":
        owner_count = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.role == "owner",
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the final workspace owner.",
            )

    db.delete(target_member)
    db.commit()
    return None
