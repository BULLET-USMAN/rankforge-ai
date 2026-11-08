"""Organization-level AI usage metering and quota enforcement."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_quota_reservation import AIQuotaReservation
from app.models.ai_usage_record import AIUsageRecord
from app.services.ai.exceptions import AIQuotaExhaustedError


class AIUsageMeter:
    """
    Manages usage logging, token cost estimation, and quota verification
    with concurrency safeguards.
    """

    @classmethod
    def estimate_cost(cls, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate estimated USD cost based on configurable per-million token rates.
        """
        input_cost = (input_tokens / 1_000_000.0) * settings.AI_ESTIMATED_INPUT_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000.0) * settings.AI_ESTIMATED_OUTPUT_COST_PER_MILLION
        return round(input_cost + output_cost, 6)

    @classmethod
    def check_quotas(cls, db: Session, organization_id: str, estimated_tokens: int = 1000) -> None:
        """
        Verifies organization has sufficient daily requests and monthly token allowance.
        Raises AIQuotaExhaustedError if limits are breached.
        """
        now = datetime.now(timezone.utc)
        start_of_day = now - timedelta(days=1)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        # 1. Daily request count check
        daily_reqs_stmt = select(func.count(AIUsageRecord.id)).where(
            AIUsageRecord.organization_id == organization_id,
            AIUsageRecord.created_at >= start_of_day,
        )
        daily_reqs = db.execute(daily_reqs_stmt).scalar() or 0
        if daily_reqs >= settings.AI_DAILY_ORG_REQUEST_LIMIT:
            raise AIQuotaExhaustedError(
                f"Organization daily AI request limit ({settings.AI_DAILY_ORG_REQUEST_LIMIT}) reached. "
                "Limit will reset in 24 hours."
            )

        # 2. Monthly token quota check (including active reservations)
        monthly_tokens_stmt = select(func.coalesce(func.sum(AIUsageRecord.total_tokens), 0)).where(
            AIUsageRecord.organization_id == organization_id,
            AIUsageRecord.created_at >= start_of_month,
        )
        monthly_tokens = db.execute(monthly_tokens_stmt).scalar() or 0

        # Include active reserved tokens
        reserved_stmt = select(func.coalesce(func.sum(AIQuotaReservation.tokens_reserved), 0)).where(
            AIQuotaReservation.organization_id == organization_id,
            AIQuotaReservation.status == "active",
        )
        reserved_tokens = db.execute(reserved_stmt).scalar() or 0

        if (monthly_tokens + reserved_tokens + estimated_tokens) > settings.AI_MONTHLY_ORG_TOKEN_LIMIT:
            raise AIQuotaExhaustedError(
                f"Organization monthly AI token quota ({settings.AI_MONTHLY_ORG_TOKEN_LIMIT:,}) exhausted. "
                f"Used: {monthly_tokens + reserved_tokens:,} tokens."
            )

    @classmethod
    def reserve_quota(
        cls, db: Session, organization_id: str, job_id: Optional[str], estimated_tokens: int = 2000
    ) -> AIQuotaReservation:
        """
        Atomically reserves quota for an asynchronous job before execution.
        """
        cls.check_quotas(db, organization_id, estimated_tokens)
        reservation = AIQuotaReservation(
            organization_id=organization_id,
            job_id=job_id,
            tokens_reserved=estimated_tokens,
            status="active",
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation

    @classmethod
    def release_reservation(cls, db: Session, reservation_id: str) -> None:
        """
        Releases an active reservation.
        """
        res = db.get(AIQuotaReservation, reservation_id)
        if res and res.status == "active":
            res.status = "released"
            db.commit()

    @classmethod
    def commit_reservation(cls, db: Session, reservation_id: str) -> None:
        """
        Marks an active reservation as committed.
        """
        res = db.get(AIQuotaReservation, reservation_id)
        if res and res.status == "active":
            res.status = "committed"
            db.commit()

    @classmethod
    def record_usage(
        cls,
        db: Session,
        organization_id: str,
        user_id: Optional[str],
        job_id: Optional[str],
        request_type: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        provider: str = "gemini",
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AIUsageRecord:
        """
        Persists a durable usage audit record.
        """
        total_tokens = input_tokens + output_tokens
        cost = cls.estimate_cost(input_tokens, output_tokens)

        record = AIUsageRecord(
            organization_id=organization_id,
            user_id=user_id,
            job_id=job_id,
            provider=provider,
            model=model,
            request_type=request_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            status=status,
            error_message=error_message,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def get_organization_usage_summary(cls, db: Session, organization_id: str) -> dict:
        """
        Returns real-time usage statistics and quota status for the organization.
        """
        now = datetime.now(timezone.utc)
        start_of_day = now - timedelta(days=1)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        # 24h requests
        daily_reqs = db.execute(
            select(func.count(AIUsageRecord.id)).where(
                AIUsageRecord.organization_id == organization_id,
                AIUsageRecord.created_at >= start_of_day,
            )
        ).scalar() or 0

        # Monthly tokens & cost
        monthly_row = db.execute(
            select(
                func.coalesce(func.sum(AIUsageRecord.total_tokens), 0),
                func.coalesce(func.sum(AIUsageRecord.estimated_cost), 0.0),
            ).where(
                AIUsageRecord.organization_id == organization_id,
                AIUsageRecord.created_at >= start_of_month,
            )
        ).first()

        monthly_tokens = monthly_row[0] if monthly_row else 0
        monthly_cost = float(monthly_row[1]) if monthly_row else 0.0

        return {
            "daily_requests_used": daily_reqs,
            "daily_requests_limit": settings.AI_DAILY_ORG_REQUEST_LIMIT,
            "monthly_tokens_used": monthly_tokens,
            "monthly_tokens_limit": settings.AI_MONTHLY_ORG_TOKEN_LIMIT,
            "monthly_estimated_cost_usd": round(monthly_cost, 4),
            "quota_status": "normal" if daily_reqs < settings.AI_DAILY_ORG_REQUEST_LIMIT and monthly_tokens < settings.AI_MONTHLY_ORG_TOKEN_LIMIT else "exceeded",
        }
