def test_cross_tenant_isolation(client):
    """Enforce strict multi-tenant boundary isolation between organizations."""
    user_a_token = "Bearer dev_token_usr_tenant_a_alice@tenant-a.com"
    user_b_token = "Bearer dev_token_usr_tenant_b_bob@tenant-b.com"

    # 1. User A creates Workspace A and adds a website
    res_org_a = client.post(
        "/api/v1/organizations",
        json={"name": "Tenant Alpha", "slug": "tenant-alpha"},
        headers={"Authorization": user_a_token},
    )
    assert res_org_a.status_code == 201
    org_a_id = res_org_a.json()["id"]

    res_site_a = client.post(
        f"/api/v1/organizations/{org_a_id}/websites",
        json={"name": "Alpha Portal", "domain_or_url": "alpha-seo.com"},
        headers={"Authorization": user_a_token},
    )
    assert res_site_a.status_code == 201
    site_a_id = res_site_a.json()["id"]

    # 2. User B creates Workspace B and adds a website
    res_org_b = client.post(
        "/api/v1/organizations",
        json={"name": "Tenant Beta", "slug": "tenant-beta"},
        headers={"Authorization": user_b_token},
    )
    assert res_org_b.status_code == 201
    org_b_id = res_org_b.json()["id"]

    res_site_b = client.post(
        f"/api/v1/organizations/{org_b_id}/websites",
        json={"name": "Beta Portal", "domain_or_url": "beta-seo.com"},
        headers={"Authorization": user_b_token},
    )
    assert res_site_b.status_code == 201
    site_b_id = res_site_b.json()["id"]
    assert site_b_id is not None

    # 3. User B cannot list websites from Workspace A
    res_b_access_a = client.get(
        f"/api/v1/organizations/{org_a_id}/websites",
        headers={"Authorization": user_b_token},
    )
    assert res_b_access_a.status_code == 403
    assert "Access denied. You are not a member" in res_b_access_a.json()["detail"]

    # 4. User B cannot retrieve website details of site A
    res_b_get_site_a = client.get(
        f"/api/v1/organizations/{org_a_id}/websites/{site_a_id}",
        headers={"Authorization": user_b_token},
    )
    assert res_b_get_site_a.status_code == 403

    # 5. User A cannot view members or invitations of Workspace B
    res_a_members_b = client.get(
        f"/api/v1/organizations/{org_b_id}/members",
        headers={"Authorization": user_a_token},
    )
    assert res_a_members_b.status_code == 403

    res_a_invites_b = client.get(
        f"/api/v1/organizations/{org_b_id}/invitations",
        headers={"Authorization": user_a_token},
    )
    assert res_a_invites_b.status_code == 403

    # 6. User B cannot delete website A even if they guess the ID
    res_b_delete_site_a = client.delete(
        f"/api/v1/organizations/{org_a_id}/websites/{site_a_id}",
        headers={"Authorization": user_b_token},
    )
    assert res_b_delete_site_a.status_code == 403

    # 7. Workspace list only shows orgs each user belongs to
    my_orgs_a = client.get("/api/v1/organizations", headers={"Authorization": user_a_token}).json()
    assert len(my_orgs_a) == 1
    assert my_orgs_a[0]["id"] == org_a_id

    my_orgs_b = client.get("/api/v1/organizations", headers={"Authorization": user_b_token}).json()
    assert len(my_orgs_b) == 1
    assert my_orgs_b[0]["id"] == org_b_id
