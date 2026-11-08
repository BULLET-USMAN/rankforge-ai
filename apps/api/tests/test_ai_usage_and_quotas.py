"""Tests for AI Usage Metering, Cost Calculation, and Quota Enforcement."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.services.ai.exceptions import AIQuotaExhaustedError
from app.services.ai.usage_meter import AIUsageMeter


def test_estimate_cost_calculation():
    # 10,000 input tokens, 2,000 output tokens
    cost = AIUsageMeter.estimate_cost(10000, 2000)
    expected = (10000 / 1e6) * settings.AI_ESTIMATED_INPUT_COST_PER_MILLION + (2000 / 1e6) * settings.AI_ESTIMATED_OUTPUT_COST_PER_MILLION
    assert cost == round(expected, 6)
    assert cost > 0


def test_record_usage_and_summary(db_session: Session):
    org = Organization(name="Usage Org", slug="usage-org", plan_tier="pro")
    db_session.add(org)
    db_session.commit()

    record = AIUsageMeter.record_usage(
        db=db_session,
        organization_id=org.id,
        user_id=None,
        job_id=None,
        request_type="title_optimization",
        input_tokens=500,
        output_tokens=100,
        model="gemini-2.5-flash",
        provider="gemini",
    )
    assert record.id is not None
    assert record.total_tokens == 600
    assert record.estimated_cost > 0

    summary = AIUsageMeter.get_organization_usage_summary(db_session, org.id)
    assert summary["daily_requests_used"] >= 1
    assert summary["monthly_tokens_used"] >= 600
    assert summary["quota_status"] == "normal"


def test_quota_reservation_lifecycle(db_session: Session):
    org = Organization(name="Quota Org", slug="quota-org", plan_tier="enterprise")
    db_session.add(org)
    db_session.commit()

    # Reserve
    reservation = AIUsageMeter.reserve_quota(db_session, org.id, job_id=None, estimated_tokens=1000)
    assert reservation.status == "active"
    assert reservation.tokens_reserved == 1000

    # Commit
    AIUsageMeter.commit_reservation(db_session, reservation.id)
    db_session.refresh(reservation)
    assert reservation.status == "committed"

    # New reservation and release
    res2 = AIUsageMeter.reserve_quota(db_session, org.id, job_id=None, estimated_tokens=500)
    assert res2.status == "active"
    AIUsageMeter.release_reservation(db_session, res2.id)
    db_session.refresh(res2)
    assert res2.status == "released"


def test_daily_request_limit_enforcement(db_session: Session, monkeypatch):
    org = Organization(name="Limited Org", slug="limited-org", plan_tier="free")
    db_session.add(org)
    db_session.commit()

    # Set daily limit to 2
    monkeypatch.setattr(settings, "AI_DAILY_ORG_REQUEST_LIMIT", 2)

    # 1st request
    AIUsageMeter.record_usage(
        db=db_session, organization_id=org.id, user_id=None, job_id=None,
        request_type="test", input_tokens=10, output_tokens=10, model="mock"
    )
    # 2nd request
    AIUsageMeter.record_usage(
        db=db_session, organization_id=org.id, user_id=None, job_id=None,
        request_type="test", input_tokens=10, output_tokens=10, model="mock"
    )

    # 3rd request should fail quota check
    with pytest.raises(AIQuotaExhaustedError) as exc_info:
        AIUsageMeter.check_quotas(db_session, organization_id=org.id, estimated_tokens=100)
    assert "daily AI request limit" in str(exc_info.value)
