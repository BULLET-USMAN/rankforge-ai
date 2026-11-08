"""Celery background tasks for AI recommendation generation."""

from __future__ import annotations

import asyncio
import logging

from celery import shared_task

from app.db.session import SessionLocal
from app.models.ai_generation_job import AIGenerationJob
from app.services.ai.orchestrator import AIOptimizationOrchestrator
from app.services.ai.types import AIJobStatus

logger = logging.getLogger("rankforge.worker.ai")


@shared_task(
    bind=True,
    name="tasks.ai.execute_batch_job",
    max_retries=1,
)
def execute_batch_job(self, job_id: str):
    """
    Executes a bulk AI recommendation batch job asynchronously.
    """
    logger.info("Starting background AI batch job: job_id=%s, task_id=%s", job_id, self.request.id)
    db = SessionLocal()
    try:
        job = db.get(AIGenerationJob, job_id)
        if not job:
            logger.error("Job %s not found", job_id)
            return {"status": "not_found", "job_id": job_id}

        job.celery_task_id = self.request.id
        db.commit()

        asyncio.run(AIOptimizationOrchestrator.run_batch_job(db=db, job_id=job_id))
        return {"status": "completed", "job_id": job_id}
    except Exception as exc:
        logger.exception("AI batch generation job %s failed: %s", job_id, exc)
        job = db.get(AIGenerationJob, job_id)
        if job:
            job.status = AIJobStatus.FAILED.value
            job.error_message = str(exc)[:500]
            db.commit()
        raise
    finally:
        db.close()
