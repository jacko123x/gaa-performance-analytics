import json
import logging

from src.logging_config import JsonFormatter, identifier_fingerprint


def test_json_logging_redacts_secrets_and_url_credentials():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="configuration_checked",
        args=(),
        exc_info=None,
    )
    record.event_name = "configuration_checked"
    record.event_data = {
        "password": "do-not-log-me",
        "database_url": "postgresql://user:do-not-log-me@db/app",
        "message": "postgresql://user:do-not-log-me@db/app",
    }

    payload = json.loads(JsonFormatter().format(record))
    serialized = json.dumps(payload)

    assert "do-not-log-me" not in serialized
    assert payload["data"]["password"] == "[REDACTED]"
    assert "user:***@db" in payload["data"]["message"]


def test_failed_login_identifier_uses_stable_fingerprint():
    assert identifier_fingerprint(" ExampleUser ") == identifier_fingerprint(
        "exampleuser"
    )
    assert "exampleuser" not in identifier_fingerprint("exampleuser")
