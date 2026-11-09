import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.models.organization_invitation import OrganizationInvitation
from app.models.organization_member import OrganizationMember
from app.models.profile import Profile


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class InvitationService:
    """Manages workspace team invitations with cryptographic token validation."""

    @classmethod
    def create_invitation(
        cls,
        db: Session,
        organization_id: str,
        invited_by_user_id: str,
        invited_email: str,
        invited_role: str,
    ) -> Tuple[OrganizationInvitation, str]:
        email_clean = invited_email.strip().lower()

        # Verify not already an active member
        existing_profile = db.query(Profile).filter(Profile.email == email_clean).first()
        if existing_profile:
            existing_member = (
                db.query(OrganizationMember)
                .filter(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.user_id == existing_profile.id,
                )
                .first()
            )
            if existing_member:
                raise ValueError("This user is already a member of this workspace.")

        # Invalidate any previous pending invitations for this email in this org
        now = datetime.now(timezone.utc)
        pending_invitations = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.organization_id == organization_id,
                OrganizationInvitation.invited_email == email_clean,
                OrganizationInvitation.accepted_at.is_(None),
                OrganizationInvitation.revoked_at.is_(None),
            )
            .all()
        )
        for prev in pending_invitations:
            prev.revoked_at = now

        # Generate secure random token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        expires_at = now + timedelta(days=settings.INVITATION_EXPIRY_DAYS)

        invitation = OrganizationInvitation(
            organization_id=organization_id,
            invited_email=email_clean,
            invited_role=invited_role,
            invited_by=invited_by_user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        return invitation, raw_token

    @classmethod
    def list_pending_invitations(
        cls, db: Session, organization_id: str
    ) -> List[OrganizationInvitation]:
        now = datetime.now(timezone.utc)
        return (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.organization_id == organization_id,
                OrganizationInvitation.accepted_at.is_(None),
                OrganizationInvitation.revoked_at.is_(None),
                OrganizationInvitation.expires_at > now,
            )
            .order_by(OrganizationInvitation.created_at.desc())
            .all()
        )

    @classmethod
    def get_invitation_by_token(
        cls, db: Session, raw_token: str
    ) -> Optional[OrganizationInvitation]:
        token_hash = hash_token(raw_token.strip())
        return (
            db.query(OrganizationInvitation)
            .filter(OrganizationInvitation.token_hash == token_hash)
            .first()
        )

    @classmethod
    def revoke_invitation(
        cls, db: Session, invitation_id: str, organization_id: str
    ) -> OrganizationInvitation:
        invitation = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.id == invitation_id,
                OrganizationInvitation.organization_id == organization_id,
            )
            .first()
        )
        if not invitation:
            raise ValueError("Invitation not found.")
        if invitation.accepted_at is not None:
            raise ValueError("Cannot revoke an invitation that has already been accepted.")

        invitation.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invitation)
        return invitation

    @classmethod
    def accept_invitation(
        cls, db: Session, raw_token: str, current_user: Profile
    ) -> Tuple[OrganizationMember, Organization]:
        invitation = cls.get_invitation_by_token(db, raw_token)
        if not invitation:
            raise ValueError("Invalid invitation link.")

        now = datetime.now(timezone.utc)
        # Ensure timezone-aware comparison
        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if invitation.revoked_at is not None:
            raise ValueError("This invitation has been revoked.")
        if invitation.accepted_at is not None:
            raise ValueError("This invitation has already been accepted.")
        if expires_at <= now:
            raise ValueError("This invitation link has expired.")

        # Enforce email recipient match
        if current_user.email.strip().lower() != invitation.invited_email.strip().lower():
            raise ValueError(
                f"This invitation was sent to {invitation.invited_email}. "
                f"You are signed in as {current_user.email}. Please switch accounts to accept."
            )

        org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
        if not org:
            raise ValueError("Organization associated with invitation no longer exists.")

        # Create or update membership
        existing_member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == invitation.organization_id,
                OrganizationMember.user_id == current_user.id,
            )
            .first()
        )
        if existing_member:
            member = existing_member
        else:
            member = OrganizationMember(
                organization_id=invitation.organization_id,
                user_id=current_user.id,
                role=invitation.invited_role,
                invited_by=invitation.invited_by,
            )
            db.add(member)

        invitation.accepted_at = now
        db.commit()
        db.refresh(member)
        return member, org
