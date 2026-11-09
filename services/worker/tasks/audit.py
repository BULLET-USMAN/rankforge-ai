"""Celery background tasks for SEO audit execution."""

from __future__ import annotations

import logging

from celery import shared_task

from app.db.session import SessionLocal
from app.services.audit.audit_orchestrator import SEOAuditOrchestrator

logger = logging.getLogger("rankforge.worker.audit")


@shared_task(
    bind=True,
    name="tasks.audit.execute_audit",
    max_retries=0,
)
def execute_audit(self, audit_run_id: str):
    """Executes a technical SEO audit run asynchronously."""
    logger.info(
        "Starting background SEO audit execution: audit_run_id=%s, task_id=%s",
        audit_run_id,
        self.request.id,
    )
    db = SessionLocal()
    try:
        orchestrator = SEOAuditOrchestrator(db=db, audit_run_id=audit_run_id)
        orchestrator.run()
        return {"status": "finished", "audit_run_id": audit_run_id}
    except Exception as exc:
        logger.exception("SEO audit execution failed for audit_run_id=%s: %s", audit_run_id, exc)
        raise
    finally:
        db.close()
