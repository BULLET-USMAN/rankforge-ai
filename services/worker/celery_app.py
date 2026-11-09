"""Production Celery application configuration for background worker processing."""

from __future__ import annotations

import os

from celery import Celery

# Read broker and backend URLs from environment, supporting Railway Redis variables
redis_fallback = os.getenv("REDIS_URL", os.getenv("REDISPRIVATEURL", "redis://localhost:6379/0"))
broker_url = os.getenv("CELERY_BROKER_URL", redis_fallback)
result_backend = os.getenv("CELERY_RESULT_BACKEND", redis_fallback)

celery_app = Celery(
    "rankforge_worker",
    broker=broker_url,
    backend=result_backend,
    include=["tasks.smoke", "tasks.crawler", "tasks.audit", "tasks.ai"],
)

conf_updates = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "worker_max_tasks_per_child": 50,
    "worker_prefetch_multiplier": 1,
    "task_time_limit": int(os.getenv("CELERY_TASK_TIME_LIMIT", "300")),
    "task_soft_time_limit": int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "240")),
}

# Configure SSL/TLS when connecting over secure rediss://
if broker_url.startswith("rediss://"):
    conf_updates["broker_use_ssl"] = {"ssl_cert_reqs": None}
if result_backend.startswith("rediss://"):
    conf_updates["redis_backend_use_ssl"] = {"ssl_cert_reqs": None}

celery_app.conf.update(**conf_updates)
