import jwt


def test_unauthenticated_request_rejected(unauthenticated_client):
    """Endpoints requiring authentication must return 401 Unauthorized."""
    res = unauthenticated_client.get("/api/v1/me")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_invalid_token_signature_rejected(unauthenticated_client):
    """Tokens signed with a fraudulent secret must be rejected."""
    bad_token = jwt.encode(
        {"sub": "fraud_user", "email": "fraud@rankforge.ai"}, "wrong-secret", algorithm="HS256"
    )
    res = unauthenticated_client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert res.status_code == 401


def test_dev_token_and_profile_retrieval(client):
    """Dev token creates profile and returns authenticated identity via /api/v1/me."""
    res = client.get("/api/v1/me")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@rankforge.ai"
    assert data["id"] == "usr_default"


def test_update_profile(client):
    """User should be able to update their display name and full name."""
    update_payload = {
        "display_name": "Senior SEO Lead",
        "full_name": "Test Engineer",
    }
    res = client.patch("/api/v1/me", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["display_name"] == "Senior SEO Lead"
    assert data["full_name"] == "Test Engineer"
