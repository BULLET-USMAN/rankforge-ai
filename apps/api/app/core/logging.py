import json
import logging
import sys
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for production observability.
    Formats logs as single-line JSON objects with ISO timestamps,
    log level, logger name, and message payload.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra context if passed
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

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
