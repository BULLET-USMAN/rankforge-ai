"""Google Search Console OAuth2 endpoints for production authentication and sync."""

from __future__ import annotations

import urllib.parse
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.rbac import require_role
from app.core.security import verify_supabase_jwt
from app.db.session import get_db
from app.models.google_integration import GoogleIntegration
from app.models.website_project import WebsiteProject
from app.schemas.google_oauth import (
    GoogleAuthUrlResponse,
    GoogleDisconnectResponse,
    GoogleIntegrationStatusResponse,
)
from app.services.google_oauth import (
    build_authorization_url,
    exchange_code_for_tokens,
    generate_oauth_state,
    save_or_update_google_integration,
    validate_oauth_state,
)

router = APIRouter(prefix="/integrations/google", tags=["Google Search Console Integration"])


def get_current_user_claims(
    authorization: Optional[str] = Header(None),
) -> dict:
    """Extracts and verifies Supabase JWT token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1]
    return verify_supabase_jwt(token)


@router.get("/authorize", response_model=GoogleAuthUrlResponse)
def get_google_authorization_url(
    organization_id: str = Query(..., description="Organization ID connecting GSC"),
    website_project_id: Optional[str] = Query(None, description="Optional website project ID"),
    return_url: Optional[str] = Query(None, description="Frontend path to redirect after flow"),
    claims: dict = Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    Generates a secure Google Search Console OAuth2 consent URL.
    Enforces RBAC: requester must have at least 'admin' or 'owner' role in the organization.
    """
    user_id = claims.get("sub", "")
    require_role(db, organization_id, user_id, minimum_role="admin")

    if website_project_id:
        project = db.execute(
            select(WebsiteProject).where(
                WebsiteProject.id == website_project_id,
                WebsiteProject.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Website project not found in organization.",
            )

    state = generate_oauth_state(
        organization_id=organization_id,
        user_id=user_id,
        website_project_id=website_project_id,
        return_url=return_url,
    )
    auth_url = build_authorization_url(state)

    return GoogleAuthUrlResponse(
        authorization_url=auth_url,
        state=state,
        redirect_uri=settings.get_google_redirect_uri(),
    )


@router.get("/callback")
async def google_oauth_callback(
    code: Optional[str] = Query(None, description="Google authorization code"),
    state: Optional[str] = Query(None, description="Signed OAuth state parameter"),
    error: Optional[str] = Query(None, description="Error reported by Google OAuth"),
    db: Session = Depends(get_db),
):
    """
    Production OAuth 2.0 callback endpoint invoked by Google upon user consent.
    Validates signed state, exchanges code for encrypted access/refresh tokens,
    persists credentials, and redirects safely back to the frontend application.
    """
    frontend_base = settings.FRONTEND_URL.rstrip("/")

    # Handle denial or cancellation by user in Google consent screen
    if error:
        logger.warning(f"Google OAuth authorization rejected or cancelled: {error}")
        target_error_url = (
            f"{frontend_base}/dashboard/settings?"
            f"{urllib.parse.urlencode({'error': 'google_oauth_denied', 'message': error})}"
        )
        return RedirectResponse(
            url=target_error_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )

    if not code or not state:
        logger.warning("Google OAuth callback received without code or state parameter.")
        target_missing_url = (
            f"{frontend_base}/dashboard/settings?"
            f"{urllib.parse.urlencode({'error': 'invalid_callback', 'message': 'Missing code or state'})}"
        )
        return RedirectResponse(
            url=target_missing_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )

    try:
        # Validate tamper-proof state and expiration
        payload = validate_oauth_state(state)
        org_id = payload["org_id"]
        user_id = payload.get("user_id")
        project_id = payload.get("project_id")
        return_url = payload.get("return_url", "/dashboard/settings")

        # Exchange authorization code for tokens
        redirect_uri = settings.get_google_redirect_uri()
        token_data = await exchange_code_for_tokens(code, redirect_uri)

        # Persist encrypted tokens
        save_or_update_google_integration(
            db=db,
            organization_id=org_id,
            website_project_id=project_id,
            token_data=token_data,
            user_id=user_id,
        )

        logger.info(
            f"Successfully connected Google Search Console for org={org_id}, project={project_id}"
        )

        # Safe frontend redirect
        dest_path = return_url if return_url.startswith("/") else f"/{return_url}"
        separator = "&" if "?" in dest_path else "?"
        success_redirect = f"{frontend_base}{dest_path}{separator}google_connected=true"
        return RedirectResponse(
            url=success_redirect, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )

    except HTTPException as exc:
        logger.error(f"HTTP error during Google OAuth callback: {exc.detail}")
        err_redirect = (
            f"{frontend_base}/dashboard/settings?"
            f"{urllib.parse.urlencode({'error': 'google_auth_failed', 'message': str(exc.detail)})}"
        )
        return RedirectResponse(url=err_redirect, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    except Exception as exc:
        logger.error(f"Unexpected error in Google OAuth callback: {exc}", exc_info=True)
        err_redirect = (
            f"{frontend_base}/dashboard/settings?"
            f"{urllib.parse.urlencode({'error': 'internal_auth_error', 'message': 'An unexpected error occurred during Google connection.'})}"
        )
        return RedirectResponse(url=err_redirect, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/status", response_model=GoogleIntegrationStatusResponse)
def get_google_integration_status(
    organization_id: str = Query(..., description="Organization ID"),
    website_project_id: Optional[str] = Query(None, description="Optional website project ID"),
    claims: dict = Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """Checks whether an active Google Search Console integration exists for this workspace."""
    user_id = claims.get("sub", "")
    require_role(db, organization_id, user_id, minimum_role="viewer")

    stmt = select(GoogleIntegration).where(
        GoogleIntegration.organization_id == organization_id,
        GoogleIntegration.website_project_id == website_project_id,
        GoogleIntegration.is_active == True,  # noqa: E712
    )
    integration = db.execute(stmt).scalar_one_or_none()

    if not integration:
        return GoogleIntegrationStatusResponse(
            is_connected=False,
            organization_id=organization_id,
            website_project_id=website_project_id,
        )

    return GoogleIntegrationStatusResponse(
        is_connected=True,
        connected_email=integration.google_account_email,
        scopes=integration.scopes_json,
        expires_at=integration.expires_at.isoformat() if integration.expires_at else None,
        is_active=integration.is_active,
        organization_id=integration.organization_id,
        website_project_id=integration.website_project_id,
    )


@router.post("/disconnect", response_model=GoogleDisconnectResponse)
def disconnect_google_integration(
    organization_id: str = Query(..., description="Organization ID"),
    website_project_id: Optional[str] = Query(None, description="Optional website project ID"),
    claims: dict = Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """Disconnects Google Search Console and deactivates stored credentials."""
    user_id = claims.get("sub", "")
    require_role(db, organization_id, user_id, minimum_role="admin")

    stmt = select(GoogleIntegration).where(
        GoogleIntegration.organization_id == organization_id,
        GoogleIntegration.website_project_id == website_project_id,
    )
    integration = db.execute(stmt).scalar_one_or_none()
    if integration:
        integration.is_active = False
        db.commit()

    logger.info(f"Google Search Console disconnected by user {user_id} for org {organization_id}")
    return GoogleDisconnectResponse(
        success=True,
        message="Google Search Console integration successfully disconnected.",
    )
