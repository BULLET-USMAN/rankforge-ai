"""Structured, secret-safe JSON logging configuration for production observability."""

from __future__ import annotations

import json
import logging
import re
import sys
from typing import Any, Dict

SENSITIVE_PATTERNS = [
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), r"\1[REDACTED]"),
    (
        re.compile(
            r"((?:password|secret|token|api_key|access_token|refresh_token)[\"']?\s*[:=]\s*[\"']?)[^\"'\s&,]+",
            re.IGNORECASE,
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(postgresql(?:\+psycopg)?://[^:]+:)[^@]+(@)", re.IGNORECASE),
        r"\1[REDACTED]\2",
    ),
    (re.compile(r"(redis(?:s)?://[^:]+:)[^@]+(@)", re.IGNORECASE), r"\1[REDACTED]\2"),
]


def mask_sensitive_data(text: str) -> str:
    """Masks authorization tokens, passwords, and sensitive keys from log strings."""
    if not text:
        return text
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for production observability.
    Formats logs as single-line JSON objects with ISO timestamps,
    log level, logger name, and message payload with secret masking.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_sensitive_data(record.getMessage()),
        }

        # Include extra context if passed
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms
        if record.exc_info:
            log_record["exception"] = mask_sensitive_data(self.formatException(record.exc_info))

        return json.dumps(log_record)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configures structured JSON logging on the root logger."""
    logger = logging.getLogger("rankforge")
    logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logging()
