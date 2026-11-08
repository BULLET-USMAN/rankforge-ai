def test_create_organization(client):
    """Should successfully create a new organization."""
    payload = {
        "name": "Acme Digital",
        "slug": "acme-digital",
        "plan_tier": "starter",
    }
    response = client.post("/api/v1/organizations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Digital"
    assert data["slug"] == "acme-digital"
    assert "id" in data


def test_reject_duplicate_organization_slug(client):
    """Should return 409 Conflict when creating an organization with duplicate slug."""
    payload = {
        "name": "Beta Labs",
        "slug": "beta-labs",
        "plan_tier": "starter",
    }
    res1 = client.post("/api/v1/organizations", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/organizations", json=payload)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"]


def test_list_and_get_organization(client):
    """Should list organizations and get by ID."""
    payload = {"name": "Gamma SEO", "slug": "gamma-seo"}
    created = client.post("/api/v1/organizations", json=payload).json()

    org_id = created["id"]
    get_res = client.get(f"/api/v1/organizations/{org_id}")
    assert get_res.status_code == 200
    assert get_res.json()["slug"] == "gamma-seo"

    list_res = client.get("/api/v1/organizations")
    assert list_res.status_code == 200
    assert any(o["id"] == org_id for o in list_res.json())
