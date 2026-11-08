def test_website_project_lifecycle_and_security(client):
    """Test website project creation, domain normalization, SSRF protection, archiving, and deletion."""
    owner_token = "Bearer dev_token_usr_web_owner_owner@agency.com"

    # 1. Setup Org
    org = client.post(
        "/api/v1/organizations",
        json={"name": "SEO Agency", "slug": "seo-agency"},
        headers={"Authorization": owner_token},
    ).json()
    org_id = org["id"]

    # 2. Add website with URL containing path and query parameters
    raw_input = "https://www.rankforge-test.com/deep/page?tracking=1#section"
    res_create = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={
            "name": "RankForge Test",
            "domain_or_url": raw_input,
            "description": "Primary staging site",
        },
        headers={"Authorization": owner_token},
    )
    assert res_create.status_code == 201
    site = res_create.json()
    assert site["domain"] == "www.rankforge-test.com"
    assert site["primary_url"] == "https://www.rankforge-test.com/"
    assert site["verification_status"] == "pending"
    assert site["is_verified"] is False
    assert site["archived_at"] is None
    site_id = site["id"]

    # 3. Reject duplicate domain in same org
    res_dup = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Duplicate", "domain_or_url": "www.rankforge-test.com"},
        headers={"Authorization": owner_token},
    )
    assert res_dup.status_code == 409
    assert "already registered" in res_dup.json()["detail"]

    # 4. Reject SSRF / Internal IP targets
    for bad_target in [
        "127.0.0.1",
        "169.254.169.254",
        "10.0.0.1",
        "192.168.1.1",
        "http://metadata.google.internal",
        "http://test.local",
        "https://admin:pass@secret.com",
    ]:
        res_bad = client.post(
            f"/api/v1/organizations/{org_id}/websites",
            json={"name": "Unsafe Target", "domain_or_url": bad_target},
            headers={"Authorization": owner_token},
        )
        assert res_bad.status_code == 422, f"Target {bad_target} should have been rejected with 422"

    # 5. Search websites
    search_res = client.get(
        f"/api/v1/organizations/{org_id}/websites?search=RankForge",
        headers={"Authorization": owner_token},
    )
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1

    search_empty = client.get(
        f"/api/v1/organizations/{org_id}/websites?search=NonExistent",
        headers={"Authorization": owner_token},
    )
    assert len(search_empty.json()) == 0

    # 6. Update website metadata
    update_res = client.patch(
        f"/api/v1/organizations/{org_id}/websites/{site_id}",
        json={"name": "RankForge Production", "description": "Updated description"},
        headers={"Authorization": owner_token},
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "RankForge Production"

    # 7. Archive (soft delete)
    archive_res = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/archive",
        headers={"Authorization": owner_token},
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["archived_at"] is not None

    # Normal list hides archived
    active_list = client.get(
        f"/api/v1/organizations/{org_id}/websites",
        headers={"Authorization": owner_token},
    ).json()
    assert len(active_list) == 0

    # Include archived reveals it
    all_list = client.get(
        f"/api/v1/organizations/{org_id}/websites?include_archived=true",
        headers={"Authorization": owner_token},
    ).json()
    assert len(all_list) == 1

    # 8. Restore
    restore_res = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/restore",
        headers={"Authorization": owner_token},
    )
    assert restore_res.status_code == 200
    assert restore_res.json()["archived_at"] is None

    # 9. Permanent Delete
    del_res = client.delete(
        f"/api/v1/organizations/{org_id}/websites/{site_id}",
        headers={"Authorization": owner_token},
    )
    assert del_res.status_code == 204

    # Confirm 404
    get_res = client.get(
        f"/api/v1/organizations/{org_id}/websites/{site_id}",
        headers={"Authorization": owner_token},
    )
    assert get_res.status_code == 404
