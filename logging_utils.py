import json
import logging
import os
import re
from contextvars import ContextVar
from typing import Any

# Per-request correlation id (set in FastAPI middleware)
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover
        record.request_id = request_id_ctx.get() or "-"
        return True


def setup_logging() -> None:
    """Configure app logging.

    - LOG_LEVEL controls verbosity (default: INFO)
    - Adds request_id field to all log records
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper().strip()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers in reload environments.
    if not root.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] [req=%(request_id)s] %(message)s"
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)

    # Ensure every handler includes request_id.
    filt = RequestIdFilter()
    for h in root.handlers:
        h.addFilter(filt)

    # Reduce noisy libraries a bit (still overrideable with LOG_LEVEL=DEBUG)
    if level > logging.DEBUG:
        logging.getLogger("uvicorn.error").setLevel(level)
        logging.getLogger("uvicorn.access").setLevel(level)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)


_SECRET_KEY_RE = re.compile(r"(api[_-]?key|authorization|token|secret|password)", re.IGNORECASE)


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"…(truncated {len(s) - limit} chars)"


def sanitize_for_log(value: Any, *, max_chars: int = 2000) -> str:
    """Serialize and sanitize potentially-large/untrusted objects for logs."""
    try:
        if isinstance(value, (dict, list, tuple)):
            safe = _sanitize_obj(value)
            s = json.dumps(safe, ensure_ascii=False, default=str)
        else:
            s = str(value)
    except Exception:
        s = repr(value)

    return _truncate(s, max_chars)


def _sanitize_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if _SECRET_KEY_RE.search(str(k)):
                out[str(k)] = "***"
            else:
                out[str(k)] = _sanitize_obj(v)
        return out
    if isinstance(obj, list):
        return [_sanitize_obj(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_sanitize_obj(v) for v in obj)
    return obj

