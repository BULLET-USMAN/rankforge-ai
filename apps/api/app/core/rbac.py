from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import verify_supabase_jwt
from app.db.session import get_db
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.profile import Profile

# Role hierarchy: higher integer represents higher authority
ROLE_HIERARCHY = {
    "viewer": 1,
    "editor": 2,
    "admin": 3,
    "owner": 4,
}


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Profile:
    """
    Extracts and verifies the Supabase JWT from the Authorization header or session cookie.
    Ensures a matching Profile record exists idempotently.
    Raises HTTPException(401) if token is missing or invalid.
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    elif "sb-access-token" in request.cookies:
        token = request.cookies["sb-access-token"]
    elif "supabase_token" in request.cookies:
        token = request.cookies["supabase_token"]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_supabase_jwt(token)
    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing required identity claims.",
        )

    # Fetch profile or create idempotently
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        # Check by email in case profile was pre-seeded
        profile = db.query(Profile).filter(Profile.email == email).first()
        if profile:
            profile.id = user_id
            db.commit()
            db.refresh(profile)
        else:
            full_name = payload.get("user_metadata", {}).get("full_name") or email.split("@")[0]
            profile = Profile(
                id=user_id,
                email=email,
                full_name=full_name,
                display_name=full_name,
                role="member",
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

    return profile


class RequireOrgRole:
    """
    Dependency that enforces organization membership and minimum role authority.
    Usage in endpoint:
      membership = Depends(RequireOrgRole("admin"))
    """

    def __init__(self, min_role: str = "viewer"):
        if min_role not in ROLE_HIERARCHY:
            raise ValueError(f"Unknown role '{min_role}'")
        self.min_role = min_role

    def __call__(
        self,
        org_id: str,
        current_user: Profile = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> OrganizationMember:
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found.",
            )

        # Verify user is a member of this specific organization
        member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == current_user.id,
            )
            .first()
        )

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not a member of this workspace.",
            )

        user_level = ROLE_HIERARCHY.get(member.role, 0)
        required_level = ROLE_HIERARCHY[self.min_role]

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Minimum role required: '{self.min_role}'. Your role: '{member.role}'.",
            )

        return member


def require_role(
    db: Session,
    organization_id: str,
    user_id: str,
    minimum_role: str = "viewer",
) -> OrganizationMember:
    """Verifies that user belongs to organization and possesses at least minimum_role."""
    if minimum_role not in ROLE_HIERARCHY:
        raise ValueError(f"Unknown role '{minimum_role}'")

    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You are not a member of this workspace.",
        )

    user_level = ROLE_HIERARCHY.get(member.role, 0)
    required_level = ROLE_HIERARCHY[minimum_role]

    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Minimum role required: '{minimum_role}'. Your role: '{member.role}'.",
        )

    return member
