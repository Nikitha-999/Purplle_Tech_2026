import logging
import sys
from typing import Any

from app.config import get_settings


class StructuredFormatter(logging.Formatter):
    """Emit single-line key=value logs suitable for grep and log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        parts: list[str] = [
            f"level={record.levelname}",
            f"logger={record.name}",
            f"message={record.getMessage()}",
        ]
        for key in ("trace_id", "store_id", "endpoint", "latency_ms", "event_count", "status_code"):
            value = getattr(record, key, None)
            if value is not None:
                parts.append(f"{key}={value}")
        if record.exc_info:
            parts.append(f"exception={self.formatException(record.exc_info)}")
        return " ".join(parts)


def configure_logging() -> None:
    settings = get_settings()
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def log_request(
    logger: logging.Logger,
    *,
    trace_id: str,
    endpoint: str,
    latency_ms: float,
    status_code: int,
    store_id: str | None = None,
    event_count: int | None = None,
) -> None:
    extra: dict[str, Any] = {
        "trace_id": trace_id,
        "endpoint": endpoint,
        "latency_ms": round(latency_ms, 2),
        "status_code": status_code,
    }
    if store_id:
        extra["store_id"] = store_id
    if event_count is not None:
        extra["event_count"] = event_count
    logger.info("request_completed", extra=extra)
