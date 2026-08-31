"""Structured application logging with automatic sensitive-data redaction."""

from datetime import UTC, datetime
import hashlib
import json
import logging
import re
import sys


SENSITIVE_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "database_url",
    "connection_string",
)
URL_CREDENTIALS = re.compile(
    r"(?P<prefix>[a-z][a-z0-9+.-]*://[^:\s/@]+:)[^@\s]+@",
    flags=re.IGNORECASE,
)


def _redact_text(value):
    return URL_CREDENTIALS.sub(r"\g<prefix>***@", str(value))


def redact(value, key=""):
    normalized_key = key.lower()
    if any(marker in normalized_key for marker in SENSITIVE_KEY_MARKERS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(child_key): redact(child_value, str(child_key))
            for child_key, child_value in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [redact(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return _redact_text(value) if isinstance(value, str) else value
    return _redact_text(value)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event_name", record.getMessage()),
        }
        event_data = getattr(record, "event_data", None)
        if event_data:
            payload["data"] = redact(event_data)
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
            if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
                payload["traceback"] = _redact_text(
                    self.formatException(record.exc_info)
                )
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(level="INFO", json_logs=True):
    root_logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
        )
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
    logging.getLogger("alembic.runtime.plugins").setLevel(logging.WARNING)


def get_logger(name):
    return logging.getLogger(name)


def log_event(logger, event, *, level=logging.INFO, **data):
    logger.log(
        level,
        event,
        extra={"event_name": event, "event_data": redact(data)},
    )


def log_exception(logger, event, *, error, **data):
    logger.error(
        event,
        exc_info=(type(error), error, error.__traceback__),
        extra={"event_name": event, "event_data": redact(data)},
    )


def identifier_fingerprint(identifier):
    normalized = str(identifier or "").strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
