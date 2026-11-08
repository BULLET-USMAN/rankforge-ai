def test_invitation_lifecycle_and_security(client):
    """Test full invitation lifecycle: creation, token hashing, revocation, acceptance, and rejection."""
    owner_token = "Bearer dev_token_usr_inv_owner_owner@company.com"

    # 1. Create org
    org = client.post(
        "/api/v1/organizations",
        json={"name": "Invite Org", "slug": "invite-org"},
        headers={"Authorization": owner_token},
    ).json()
    org_id = org["id"]

    # 2. Owner invites engineer@company.com as editor
    inv_res = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"invited_email": "engineer@company.com", "invited_role": "editor"},
        headers={"Authorization": owner_token},
    )
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    assert inv_data["invited_email"] == "engineer@company.com"
    assert inv_data["invited_role"] == "editor"
    raw_token = inv_data["manual_link"].split("token=")[1]

    # 3. Mismatched user attempts to accept -> rejected
    imposter_token = "Bearer dev_token_usr_imposter_other@company.com"
    res_mismatch = client.post(
        "/api/v1/invitations/accept",
        json={"token": raw_token},
        headers={"Authorization": imposter_token},
    )
    assert res_mismatch.status_code == 400
    assert "Please switch accounts" in res_mismatch.json()["detail"]

    # 4. Valid recipient accepts -> success
    recipient_token = "Bearer dev_token_usr_eng_engineer@company.com"
    res_accept = client.post(
        "/api/v1/invitations/accept",
        json={"token": raw_token},
        headers={"Authorization": recipient_token},
    )
    assert res_accept.status_code == 200
    assert res_accept.json()["role"] == "editor"

    # 5. Cannot re-accept already accepted invitation
    res_reaccept = client.post(
        "/api/v1/invitations/accept",
        json={"token": raw_token},
        headers={"Authorization": recipient_token},
    )
    assert res_reaccept.status_code == 400
    assert "already been accepted" in res_reaccept.json()["detail"]

    # 6. Test Revocation
    inv_rev_res = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"invited_email": "revoked@company.com", "invited_role": "viewer"},
        headers={"Authorization": owner_token},
    )
    assert inv_rev_res.status_code == 201
    rev_id = inv_rev_res.json()["id"]
    rev_token = inv_rev_res.json()["manual_link"].split("token=")[1]

    # Revoke it
    del_res = client.delete(
        f"/api/v1/organizations/{org_id}/invitations/{rev_id}",
        headers={"Authorization": owner_token},
    )
    assert del_res.status_code == 204

    # Acceptance after revocation is rejected
    user_rev_token = "Bearer dev_token_usr_rev_revoked@company.com"
    res_accept_rev = client.post(
        "/api/v1/invitations/accept",
        json={"token": rev_token},
        headers={"Authorization": user_rev_token},
    )
    assert res_accept_rev.status_code == 400
    assert "revoked" in res_accept_rev.json()["detail"]
