"""Comprehensive tests for Google Search Console OAuth2 integration and token security."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import mask_sensitive_data
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.profile import Profile
from app.services.crypto import decrypt_secret, encrypt_secret
from app.services.google_oauth import (
    build_authorization_url,
    exchange_code_for_tokens,
    generate_oauth_state,
    parse_id_token_email,
    refresh_access_token,
    save_or_update_google_integration,
    validate_oauth_state,
)


def test_secret_safe_logging_masks_credentials():
    """Verifies that sensitive tokens, keys, and connection strings are masked from logs."""
    raw_log = "User Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token123"
    masked = mask_sensitive_data(raw_log)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked
    assert "Bearer [REDACTED]" in masked

    raw_db = (
        "Connecting to postgresql+psycopg://rankforge:super_secret_pw@db.supabase.co:5432/postgres"
    )
    masked_db = mask_sensitive_data(raw_db)
    assert "super_secret_pw" not in masked_db
    assert "[REDACTED]@" in masked_db

    raw_redis = "Connecting to rediss://default:redis_secret_password@redis.railway.internal:6379/0"
    masked_redis = mask_sensitive_data(raw_redis)
    assert "redis_secret_password" not in masked_redis
    assert "[REDACTED]@" in masked_redis


def test_database_url_normalization():
    """Verifies that raw postgres:// and postgresql:// URLs are normalized to postgresql+psycopg://."""
    raw1 = "postgres://user:pass@db.supabase.co:5432/postgres"
    normalized1 = settings.normalize_database_url(raw1)
    assert normalized1.startswith("postgresql+psycopg://")

    raw2 = (
        "postgresql://user:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )
    normalized2 = settings.normalize_database_url(raw2)
    assert normalized2.startswith("postgresql+psycopg://")
    assert "sslmode=require" in normalized2


def test_token_encryption_and_decryption_at_rest():
    """Verifies AES-128-CBC + HMAC (Fernet) cryptographic isolation of OAuth tokens."""
    token = "ya29.a0ARrdaM_test_google_access_token_super_secret"
    cipher = encrypt_secret(token)
    assert cipher is not None
    assert cipher != token
    assert "ya29" not in cipher

    decrypted = decrypt_secret(cipher)
    assert decrypted == token

    # Empty handling
    assert encrypt_secret(None) is None
    assert decrypt_secret(None) is None


def test_oauth_state_generation_and_validation():
    """Verifies signed state tamper detection and expiration enforcement."""
    org_id = "org_test_123"
    user_id = "usr_lead_123"

    state = generate_oauth_state(org_id, user_id, return_url="/dashboard/settings")
    assert "." in state

    # Valid validation
    payload = validate_oauth_state(state)
    assert payload["org_id"] == org_id
    assert payload["user_id"] == user_id
    assert payload["return_url"] == "/dashboard/settings"
    assert "nonce" in payload

    # Tampered payload detection
    parts = state.split(".")
    tampered_b64 = parts[0] + "xyz"
    tampered_state = f"{tampered_b64}.{parts[1]}"
    with pytest.raises(Exception) as excinfo:
        validate_oauth_state(tampered_state)
    assert "Invalid" in str(excinfo.value.detail) or "Tampered" in str(excinfo.value.detail)

    # Expired state detection
    expired_payload = {
        "org_id": org_id,
        "user_id": user_id,
        "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp()),
    }
    exp_b64 = base64.urlsafe_b64encode(
        json.dumps(expired_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("utf-8")
    import hashlib
    import hmac

    sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        exp_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expired_state = f"{exp_b64}.{sig}"
    with pytest.raises(Exception) as excinfo:
        validate_oauth_state(expired_state)
    assert "expired" in str(excinfo.value.detail).lower()


def test_build_authorization_url(monkeypatch):
    """Verifies generated authorization URL includes webmasters.readonly and offline access."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "mock-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "PUBLIC_API_URL", "https://api.rankforge.ai")

    state = "mock_state_token.mock_sig"
    auth_url = build_authorization_url(state)

    assert "accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert "client_id=mock-client-id.apps.googleusercontent.com" in auth_url
    assert "access_type=offline" in auth_url
    assert "prompt=consent" in auth_url
    assert "webmasters.readonly" in auth_url
    assert (
        "https%3A%2F%2Fapi.rankforge.ai%2Fapi%2Fv1%2Fintegrations%2Fgoogle%2Fcallback" in auth_url
    )


@pytest.mark.asyncio
async def test_token_exchange_and_refresh_mocked(monkeypatch):
    """Verifies token exchange and refresh logic with mocked Google token endpoint."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "mock-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "mock-client-secret")

    mock_exchange_resp = {
        "access_token": "mock_new_access_token_123",
        "refresh_token": "mock_refresh_token_456",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
    }

    mock_refresh_resp = {
        "access_token": "mock_refreshed_access_token_789",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_exchange_resp
        mock_post.return_value = mock_response

        exchange_result = await exchange_code_for_tokens(
            "mock_auth_code", "http://localhost:8000/api/v1/integrations/google/callback"
        )
        assert exchange_result["access_token"] == "mock_new_access_token_123"
        assert exchange_result["refresh_token"] == "mock_refresh_token_456"

        # Mock refresh
        mock_response.json.return_value = mock_refresh_resp
        refresh_result = await refresh_access_token("mock_refresh_token_456")
        assert refresh_result["access_token"] == "mock_refreshed_access_token_789"


def test_parse_id_token_email():
    """Verifies unverified parsing of user email from JWT id_token payload."""
    payload = {"email": "gsc-owner@example.com", "sub": "12345"}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    dummy_jwt = f"header.{payload_b64}.signature"
    assert parse_id_token_email(dummy_jwt) == "gsc-owner@example.com"
    assert parse_id_token_email("invalid-token") is None


def test_google_integration_db_persistence(db_session: Session):
    """Verifies GoogleIntegration model creation, encryption roundtrip, and updates."""
    # Create test org & user
    user = Profile(
        id="usr_gsc_pers",
        email="gsc-pers@rankforge.ai",
        full_name="GSC Admin",
        role="admin",
    )
    org = Organization(
        id="org_gsc_pers",
        name="GSC Persistence Workspace",
        slug="gsc-pers-workspace",
        plan_tier="enterprise",
    )
    db_session.add(user)
    db_session.add(org)
    db_session.commit()

    token_data = {
        "access_token": "ya29.initial_access_token_xyz",
        "refresh_token": "1//initial_refresh_token_abc",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "https://www.googleapis.com/auth/webmasters.readonly openid email",
    }

    integration = save_or_update_google_integration(
        db=db_session,
        organization_id=org.id,
        website_project_id=None,
        token_data=token_data,
        user_id=user.id,
    )

    assert integration.id is not None
    assert integration.is_active is True
    # Plaintext properties decrypt automatically
    assert integration.access_token == "ya29.initial_access_token_xyz"
    assert integration.refresh_token == "1//initial_refresh_token_abc"
    # Encrypted columns never contain raw plaintext
    assert "ya29" not in integration.access_token_encrypted
    assert "1//" not in (integration.refresh_token_encrypted or "")

    # Test update
    update_data = {
        "access_token": "ya29.updated_access_token_new",
        "expires_in": 7200,
    }
    updated = save_or_update_google_integration(
        db=db_session,
        organization_id=org.id,
        website_project_id=None,
        token_data=update_data,
        user_id=user.id,
    )
    assert updated.id == integration.id
    assert updated.access_token == "ya29.updated_access_token_new"
    # Preserves refresh token if omitted in update
    assert updated.refresh_token == "1//initial_refresh_token_abc"


def test_google_oauth_api_endpoints(client, db_session: Session, monkeypatch):
    """Verifies FastAPI endpoints for /authorize, /callback, /status, /disconnect."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-gsc-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-gsc-client-secret")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:3000")

    # Setup org, user, membership
    user = Profile(
        id="usr_gsc_api",
        email="gsc-api@rankforge.ai",
        full_name="GSC Tester",
        role="admin",
    )
    org = Organization(
        id="org_gsc_api",
        name="GSC API Org",
        slug="gsc-api-org",
        plan_tier="growth",
    )
    member = OrganizationMember(
        id="mem_gsc_api",
        organization_id=org.id,
        user_id=user.id,
        role="admin",
    )
    db_session.add(user)
    db_session.add(org)
    db_session.add(member)
    db_session.commit()

    token = f"dev_token_{user.id}::{user.email}"
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Authorize URL endpoint
    res_auth = client.get(
        f"/api/v1/integrations/google/authorize?organization_id={org.id}",
        headers=headers,
    )
    assert res_auth.status_code == 200
    auth_data = res_auth.json()
    assert "authorization_url" in auth_data
    assert "accounts.google.com" in auth_data["authorization_url"]
    assert "state" in auth_data

    state = auth_data["state"]

    # 2. Callback endpoint (mocking exchange)
    mock_tokens = {
        "access_token": "ya29.callback_access_token",
        "refresh_token": "1//callback_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
    }
    with patch(
        "app.api.v1.endpoints.google_oauth.exchange_code_for_tokens",
        new=AsyncMock(return_value=mock_tokens),
    ):
        res_cb = client.get(
            f"/api/v1/integrations/google/callback?code=mock_code_123&state={state}",
            follow_redirects=False,
        )
        assert res_cb.status_code in (302, 307)
        assert "google_connected=true" in res_cb.headers["location"]

    # 3. Status endpoint
    res_status = client.get(
        f"/api/v1/integrations/google/status?organization_id={org.id}",
        headers=headers,
    )
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["is_connected"] is True
    assert status_data["is_active"] is True

    # 4. Disconnect endpoint
    res_disc = client.post(
        f"/api/v1/integrations/google/disconnect?organization_id={org.id}",
        headers=headers,
    )
    assert res_disc.status_code == 200
    assert res_disc.json()["success"] is True

    # Status should now be disconnected
    res_status2 = client.get(
        f"/api/v1/integrations/google/status?organization_id={org.id}",
        headers=headers,
    )
    assert res_status2.json()["is_connected"] is False
