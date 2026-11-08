def test_rbac_member_roles_and_escalation_rules(client):
    """Verify RBAC role permissions: owner, admin, editor, viewer, and escalation protections."""
    # 1. Owner creates organization
    owner_token = "Bearer dev_token_usr_owner_owner@example.com"
    org_res = client.post(
        "/api/v1/organizations",
        json={"name": "RBAC Enterprise", "slug": "rbac-ent"},
        headers={"Authorization": owner_token},
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]

    # 2. Add an admin, editor, and viewer to the org via invitations
    admin_token = "Bearer dev_token_usr_admin_admin@example.com"
    editor_token = "Bearer dev_token_usr_editor_editor@example.com"
    viewer_token = "Bearer dev_token_usr_viewer_viewer@example.com"

    for email, role in [
        ("admin@example.com", "admin"),
        ("editor@example.com", "editor"),
        ("viewer@example.com", "viewer"),
    ]:
        inv_res = client.post(
            f"/api/v1/organizations/{org_id}/invitations",
            json={"invited_email": email, "invited_role": role},
            headers={"Authorization": owner_token},
        )
        assert inv_res.status_code == 201
        token = inv_res.json()["manual_link"].split("token=")[1]

        # Accept as that user
        u_token = f"Bearer dev_token_usr_{role}_{email}"
        accept_res = client.post(
            "/api/v1/invitations/accept",
            json={"token": token},
            headers={"Authorization": u_token},
        )
        assert accept_res.status_code == 200

    # 3. Viewer attempts to create a website project -> should be 403 Forbidden
    res_viewer_write = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Forbidden Site", "domain_or_url": "forbidden.com"},
        headers={"Authorization": viewer_token},
    )
    assert res_viewer_write.status_code == 403
    assert "Insufficient permissions" in res_viewer_write.json()["detail"]

    # 4. Viewer can read websites -> should be 200 OK
    res_viewer_read = client.get(
        f"/api/v1/organizations/{org_id}/websites",
        headers={"Authorization": viewer_token},
    )
    assert res_viewer_read.status_code == 200

    # 5. Editor can create website project -> 201 Created
    res_editor_write = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Editor Site", "domain_or_url": "editorsite.com"},
        headers={"Authorization": editor_token},
    )
    assert res_editor_write.status_code == 201
    website_id = res_editor_write.json()["id"]

    # 6. Editor cannot delete website project permanently -> 403 Forbidden
    res_editor_delete = client.delete(
        f"/api/v1/organizations/{org_id}/websites/{website_id}",
        headers={"Authorization": editor_token},
    )
    assert res_editor_delete.status_code == 403

    # 7. Admin attempts to promote editor to owner -> 403 Forbidden (privilege escalation check)
    members = client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers={"Authorization": owner_token},
    ).json()
    editor_member = next(m for m in members if m["role"] == "editor")
    owner_member = next(m for m in members if m["role"] == "owner")

    res_admin_escalate = client.patch(
        f"/api/v1/organizations/{org_id}/members/{editor_member['id']}",
        json={"role": "owner"},
        headers={"Authorization": admin_token},
    )
    assert res_admin_escalate.status_code == 403

    # 8. User attempts to alter own role -> 400 Bad Request
    admin_member = next(m for m in members if m["role"] == "admin")
    res_self_edit = client.patch(
        f"/api/v1/organizations/{org_id}/members/{admin_member['id']}",
        json={"role": "editor"},
        headers={"Authorization": admin_token},
    )
    assert res_self_edit.status_code == 400

    # 9. Owner cannot demote or remove the sole owner
    res_demote_sole_owner = client.patch(
        f"/api/v1/organizations/{org_id}/members/{owner_member['id']}",
        json={"role": "admin"},
        headers={"Authorization": owner_token},
    )
    # Self edit prevents this first:
    assert res_demote_sole_owner.status_code == 400
