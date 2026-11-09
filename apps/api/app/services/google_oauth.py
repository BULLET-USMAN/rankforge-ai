"""Google Search Console OAuth 2.0 authorization, token exchange, and lifecycle service."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.google_integration import GoogleIntegration

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def generate_oauth_state(
    organization_id: str,
    user_id: str,
    website_project_id: Optional[str] = None,
    return_url: Optional[str] = None,
) -> str:
    """Generates a tamper-proof, HMAC-signed OAuth state string with expiration."""
    payload = {
        "org_id": organization_id,
        "user_id": user_id,
        "project_id": website_project_id,
        "return_url": return_url or "/dashboard/settings",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()),
        "nonce": secrets.token_hex(8),
    }
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8")

    sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{sig}"


def validate_oauth_state(state: str) -> Dict[str, Any]:
    """Validates an HMAC-signed OAuth state string and returns the payload dict."""
    if not state or "." not in state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed or missing OAuth state parameter.",
        )

    payload_b64, sig = state.split(".", 1)

    expected_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tampered or invalid OAuth state signature.",
        )

    try:
        raw_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
        payload = json.loads(raw_json)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode OAuth state payload.",
        ) from exc

    exp = payload.get("exp", 0)
    now = int(datetime.now(timezone.utc).timestamp())
    if now > exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth authorization state has expired. Please retry.",
        )

    return payload


def build_authorization_url(state: str) -> str:
    """Builds the complete Google OAuth 2.0 authorization URL for Search Console access."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured: GOOGLE_CLIENT_ID is missing.",
        )

    redirect_uri = settings.get_google_redirect_uri()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": settings.GOOGLE_SEARCH_CONSOLE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchanges an authorization code with Google for access and refresh tokens."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth credentials are not fully configured on server.",
        )

    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(GOOGLE_TOKEN_URL, data=data)
        except Exception as exc:
            logger.error(f"Failed to communicate with Google token endpoint: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to reach Google token exchange service.",
            ) from exc

    if response.status_code != 200:
        logger.warning(f"Google token exchange failed ({response.status_code}): {response.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token exchange failed. The code may be invalid or expired.",
        )

    return response.json()


async def refresh_access_token(refresh_token_plain: str) -> Dict[str, Any]:
    """Refreshes an expired Google access token using the stored refresh token."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth credentials are not configured.",
        )

    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token_plain,
        "grant_type": "refresh_token",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(GOOGLE_TOKEN_URL, data=data)
        except Exception as exc:
            logger.error(f"Failed to refresh Google access token: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to reach Google token refresh service.",
            ) from exc

    if response.status_code != 200:
        logger.warning(f"Google token refresh failed ({response.status_code}): {response.text}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google refresh token has been revoked or expired.",
        )

    return response.json()


def parse_id_token_email(id_token: Optional[str]) -> Optional[str]:
    """Safely inspects unverified payload of id_token to retrieve user email."""
    if not id_token or "." not in id_token:
        return None
    try:
        parts = id_token.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1]
            # Add base64 padding
            rem = len(payload_b64) % 4
            if rem > 0:
                payload_b64 += "=" * (4 - rem)
            decoded = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
            data = json.loads(decoded)
            return data.get("email")
    except Exception:
        pass
    return None


def save_or_update_google_integration(
    db: Session,
    organization_id: str,
    website_project_id: Optional[str],
    token_response: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    token_data: Optional[Dict[str, Any]] = None,
) -> GoogleIntegration:
    token_response = token_response or token_data or {}
    """Upserts GoogleIntegration record with encrypted credentials."""
    stmt = select(GoogleIntegration).where(
        GoogleIntegration.organization_id == organization_id,
        GoogleIntegration.website_project_id == website_project_id,
    )
    existing = db.execute(stmt).scalar_one_or_none()

    access_token = token_response.get("access_token", "")
    refresh_token = token_response.get("refresh_token")
    expires_in = token_response.get("expires_in")
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None

    scope_str = token_response.get("scope", "")
    scopes = [s.strip() for s in scope_str.split(" ") if s.strip()]
    account_email = parse_id_token_email(token_response.get("id_token"))

    if existing:
        existing.access_token = access_token
        if refresh_token:
            existing.refresh_token = refresh_token
        existing.expires_at = expires_at
        existing.scopes_json = scopes
        existing.is_active = True
        if account_email:
            existing.google_account_email = account_email
        db.commit()
        db.refresh(existing)
        return existing

    record = GoogleIntegration(
        organization_id=organization_id,
        website_project_id=website_project_id,
        google_account_email=account_email,
        token_type=token_response.get("token_type", "Bearer"),
        scopes_json=scopes,
        expires_at=expires_at,
        is_active=True,
        created_by=user_id,
    )
    record.access_token = access_token
    if refresh_token:
        record.refresh_token = refresh_token

    db.add(record)
    db.commit()
    db.refresh(record)
    return record
