import logging
from datetime import datetime, timezone

from celery import shared_task

logger = logging.getLogger("rankforge.worker")


@shared_task(
    bind=True,
    name="tasks.smoke.smoke_task",
    max_retries=3,
    default_retry_delay=5,
)
def smoke_task(self, x: int = 21, y: int = 21):
    """
    Harmless mathematical smoke test task to confirm queue dispatch and execution.
    Supports up to 3 automatic retries with exponential backoff.
    """
    logger.info(f"Executing Celery smoke task: x={x}, y={y}, task_id={self.request.id}")
    try:
        result = x + y
        return {
            "status": "success",
            "task_id": self.request.id,
            "x": x,
            "y": y,
            "sum": result,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.error(f"Task failed with error: {exc}. Retrying...")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(name="tasks.smoke.ping_task")
def ping_task():
    """Worker health heartbeat task."""
    return {
        "status": "pong",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
