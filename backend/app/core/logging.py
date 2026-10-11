import logging
import re
from typing import Any

SENSITIVE_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
]


def redact(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    redacted = value
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
