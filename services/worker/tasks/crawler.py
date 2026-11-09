"""Celery background tasks for website crawling."""

from __future__ import annotations

import logging

from celery import shared_task

from app.db.session import SessionLocal
from app.services.crawler.crawler_orchestrator import CrawlerOrchestrator

logger = logging.getLogger("rankforge.worker.crawler")


@shared_task(
    bind=True,
    name="tasks.crawler.execute_crawl",
    max_retries=0,
)
def execute_crawl(self, job_id: str):
    """Executes a website crawl job asynchronously in the background."""
    logger.info(
        "Starting background crawl execution: job_id=%s, task_id=%s", job_id, self.request.id
    )
    db = SessionLocal()
    try:
        orchestrator = CrawlerOrchestrator(db=db, job_id=job_id)
        orchestrator.run()
        return {"status": "finished", "job_id": job_id}
    except Exception as exc:
        logger.exception("Crawl execution failed for job_id=%s: %s", job_id, exc)
        raise
    finally:
        db.close()
