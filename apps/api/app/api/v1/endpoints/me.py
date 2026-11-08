from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rbac import get_current_user
from app.db.session import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileRead, ProfileUpdate

router = APIRouter()


@router.get("", response_model=ProfileRead)
def get_my_profile(current_user: Profile = Depends(get_current_user)):
    """Retrieve profile of the currently authenticated user."""
    return current_user


@router.patch("", response_model=ProfileRead)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile details (display_name, full_name, avatar_url)."""
    if payload.display_name is not None:
        current_user.display_name = payload.display_name.strip()
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url.strip() or None

    db.commit()
    db.refresh(current_user)
    return current_user
