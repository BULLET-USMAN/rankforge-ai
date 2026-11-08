def test_liveness_endpoint(client):
    """Liveness probe must return 200 OK with status='alive'."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_endpoint_structure(client):
    """Readiness probe must report status of dependencies."""
    response = client.get("/health/ready")
    # In test environment, Redis might be mocked or unavailable, which gracefully reports not_ready/503
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "dependencies" in data
    assert "database" in data["dependencies"]
    assert data["dependencies"]["database"]["status"] == "ok"


def test_root_identity_endpoint(client):
    """Root endpoint must report RankForge AI branding."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "RankForge AI API"
    assert "version" in data
    assert "docs" in data
