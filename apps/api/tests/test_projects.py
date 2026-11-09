def test_create_website_project(client):
    """Should create website project under an organization with verification token."""
    # Create org first
    org_res = client.post(
        "/api/v1/organizations", json={"name": "Alpha Agency", "slug": "alpha-agency"}
    )
    org_id = org_res.json()["id"]

    project_payload = {
        "organization_id": org_id,
        "name": "E-Commerce Store",
        "domain": "store.example.com",
        "primary_url": "https://store.example.com",
    }
    res = client.post("/api/v1/projects", json=project_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["domain"] == "store.example.com"
    assert data["is_verified"] is False
    assert data["verification_token"].startswith("rankforge_verify_")


def test_verification_instructions(client):
    """Should return DNS TXT, Meta Tag, and File Upload instructions."""
    org_res = client.post("/api/v1/organizations", json={"name": "Delta Org", "slug": "delta-org"})
    org_id = org_res.json()["id"]

    proj_res = client.post(
        "/api/v1/projects",
        json={
            "organization_id": org_id,
            "name": "Blog Site",
            "domain": "blog.example.com",
            "primary_url": "https://blog.example.com",
        },
    )
    proj_id = proj_res.json()["id"]

    verif_res = client.get(f"/api/v1/projects/{proj_id}/verification?method=dns_txt")
    assert verif_res.status_code == 200
    vdata = verif_res.json()
    assert "dns_txt_record" in vdata
    assert "meta_tag_snippet" in vdata
    assert "file_upload_path" in vdata
    assert vdata["domain"] == "blog.example.com"
