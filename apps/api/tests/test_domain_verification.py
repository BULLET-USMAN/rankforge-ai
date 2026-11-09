"""Unit and API integration tests for website domain verification."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.website_project import WebsiteProject
from app.services.crawler.safe_fetcher import SafeFetchResult
from app.services.verification_service import VerificationService


def test_initiate_challenge_token_generation(db_session):
    # Setup org and website
    org = Organization(name="Verif Org", slug="verif-org")
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id="user-123", role="owner")
    db_session.add(member)

    project = WebsiteProject(
        organization_id=org.id,
        name="Verif Site",
        domain="verif-example.com",
        primary_url="https://verif-example.com",
        is_verified=False,
        verification_status="pending",
        verification_token="initial",
    )
    db_session.add(project)
    db_session.commit()

    # 1. DNS TXT challenge
    dns_verif = VerificationService.initiate_challenge(db_session, project, method="dns_txt")
    assert dns_verif.status == "pending"
    assert dns_verif.token is not None
    assert len(dns_verif.token) == 32
    assert dns_verif.txt_record_name == "_rankforge-challenge.verif-example.com"
    assert dns_verif.txt_record_value == f"rankforge-verification={dns_verif.token}"
    exp = (
        dns_verif.expires_at
        if dns_verif.expires_at.tzinfo
        else dns_verif.expires_at.replace(tzinfo=timezone.utc)
    )
    assert exp > datetime.now(timezone.utc)

    # 2. HTML File challenge
    file_verif = VerificationService.initiate_challenge(db_session, project, method="html_file")
    assert file_verif.status == "pending"
    assert file_verif.file_path == "/.well-known/rankforge-verification.txt"
    assert file_verif.file_content == f"rankforge-verification={file_verif.token}"


def test_verify_dns_txt_flow(db_session):
    org = Organization(name="DNS Org", slug="dns-org")
    db_session.add(org)
    db_session.flush()

    project = WebsiteProject(
        organization_id=org.id,
        name="DNS Site",
        domain="dns-test.com",
        primary_url="https://dns-test.com",
        is_verified=False,
        verification_status="pending",
        verification_token="token123",
    )
    db_session.add(project)
    db_session.commit()

    verif = VerificationService.initiate_challenge(db_session, project, method="dns_txt")

    # Mock DNS resolution success
    mock_rdata = MagicMock()
    mock_rdata.strings = [f"rankforge-verification={verif.token}".encode("utf-8")]

    with patch("dns.resolver.Resolver.resolve", return_value=[mock_rdata]):
        is_verified, msg, updated = VerificationService.verify_dns_txt(db_session, project)
        assert is_verified is True
        assert updated.status == "verified"
        assert project.is_verified is True
        assert project.verification_status == "verified"

    # Test revocation
    VerificationService.revoke_verification(db_session, project)
    assert project.is_verified is False
    assert project.verification_status == "revoked"


def test_verify_html_file_flow(db_session):
    org = Organization(name="File Org", slug="file-org")
    db_session.add(org)
    db_session.flush()

    project = WebsiteProject(
        organization_id=org.id,
        name="File Site",
        domain="file-test.com",
        primary_url="https://file-test.com",
        is_verified=False,
        verification_status="pending",
        verification_token="token456",
    )
    db_session.add(project)
    db_session.commit()

    verif = VerificationService.initiate_challenge(db_session, project, method="html_file")

    # Mock successful fetch
    mock_success = SafeFetchResult(
        is_success=True,
        status_code=200,
        text_content=f"rankforge-verification={verif.token}",
    )
    with patch(
        "app.services.crawler.safe_fetcher.SafeHttpFetcher.fetch_sync", return_value=mock_success
    ):
        is_verified, msg, updated = VerificationService.verify_html_file(db_session, project)
        assert is_verified is True
        assert updated.status == "verified"
        assert project.is_verified is True


def test_verification_api_endpoints(client):
    owner_token = "Bearer dev_token_usr_verif_owner@domain.com"
    headers = {"Authorization": owner_token}

    # Setup Org
    org = client.post(
        "/api/v1/organizations",
        json={"name": "API Verif Org", "slug": "api-verif-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    # Setup Website
    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "API Site", "domain_or_url": "https://api-site.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    # GET verification status
    resp = client.get(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/verification?method=dns_txt",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["domain"] == "api-site.com"
    assert data["method"] == "dns_txt"
    assert data["status"] == "pending"

    # POST check verification (mock DNS success)
    mock_rdata = MagicMock()
    mock_rdata.strings = [f"rankforge-verification={data['token']}".encode("utf-8")]

    with patch("dns.resolver.Resolver.resolve", return_value=[mock_rdata]):
        check_resp = client.post(
            f"/api/v1/organizations/{org_id}/websites/{site_id}/verification/check?method=dns_txt",
            headers=headers,
        )
        assert check_resp.status_code == 200
        assert check_resp.json()["is_verified"] is True
        assert check_resp.json()["status"] == "verified"

    # POST revoke verification
    revoke_resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/verification/revoke",
        headers=headers,
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "revoked"
