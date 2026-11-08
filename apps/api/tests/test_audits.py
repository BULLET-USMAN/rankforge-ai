from unittest.mock import AsyncMock, patch


def test_trigger_audit_ssrf_rejection(client):
    """Triggering an audit on a private loopback target should be blocked by SSRFGuard."""
    # Create org & project
    org = client.post("/api/v1/organizations", json={"name": "Secure Org", "slug": "secure-org"}).json()
    proj = client.post("/api/v1/projects", json={
        "organization_id": org["id"],
        "name": "Intranet",
        "domain": "internal.local",
        "primary_url": "http://127.0.0.1:8000",
    }).json()

    # Trigger audit targeting 127.0.0.1
    audit_res = client.post("/api/v1/audits", json={
        "project_id": proj["id"],
        "target_url": "http://127.0.0.1:8000/metrics",
    })
    assert audit_res.status_code == 400
    assert "SSRF Check Rejected" in audit_res.json()["detail"]


@patch("httpx.AsyncClient.get")
def test_successful_preflight_audit(mock_get, client):
    """Triggering an audit with mock valid HTTP responses should calculate score and save results."""
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {
        "strict-transport-security": "max-age=31536000",
        "x-content-type-options": "nosniff",
        "content-type": "text/html",
    }
    mock_get.return_value = mock_resp

    org = client.post("/api/v1/organizations", json={"name": "Audit Test Org", "slug": "audit-test-org"}).json()
    proj = client.post("/api/v1/projects", json={
        "organization_id": org["id"],
        "name": "Public Site",
        "domain": "example.com",
        "primary_url": "https://example.com",
    }).json()

    audit_res = client.post("/api/v1/audits", json={"project_id": proj["id"]})
    assert audit_res.status_code == 201
    job_data = audit_res.json()
    assert job_data["status"] == "completed"
    assert len(job_data["results"]) > 0
    res = job_data["results"][0]
    assert res["status_code"] == 200
    assert res["score"] >= 80
