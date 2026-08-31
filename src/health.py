"""Application liveness and database/schema readiness checks."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from src.logging_config import get_logger, log_exception


LOGGER = get_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_TABLES = {
    "alembic_version",
    "audit_events",
    "kickout_stats",
    "matches",
    "player_match_stats",
    "players",
    "scoring_sources",
    "shooting_detail",
    "team_match_stats",
    "turnover_stats",
    "users",
}


@dataclass(frozen=True)
class HealthReport:
    status: str
    ready: bool
    checks: dict[str, bool]
    reason: str | None
    checked_at: str

    def as_dict(self):
        return asdict(self)


def expected_schema_revision():
    configuration = Config(str(PROJECT_ROOT / "alembic.ini"))
    configuration.set_main_option(
        "script_location",
        str(PROJECT_ROOT / "migrations"),
    )
    return ScriptDirectory.from_config(configuration).get_current_head()


def check_database_readiness(
    db_engine=None,
    *,
    expected_revision=None,
    log_failures=True,
):
    if db_engine is None:
        from src.database.db import engine as db_engine

    checks = {
        "database_connection": False,
        "required_tables": False,
        "schema_revision": False,
    }
    checked_at = datetime.now(UTC).isoformat()
    try:
        with db_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            checks["database_connection"] = True

            table_names = set(inspect(connection).get_table_names())
            checks["required_tables"] = REQUIRED_TABLES.issubset(table_names)

            current_revision = None
            if "alembic_version" in table_names:
                current_revision = connection.scalar(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )
            target_revision = expected_revision or expected_schema_revision()
            checks["schema_revision"] = current_revision == target_revision
    except Exception as error:
        if log_failures:
            log_exception(
                LOGGER,
                "database_readiness_failed",
                error=error,
                error_type=type(error).__name__,
            )
        return HealthReport(
            status="unavailable",
            ready=False,
            checks=checks,
            reason="database_unavailable",
            checked_at=checked_at,
        )

    ready = all(checks.values())
    reason = None
    if not checks["required_tables"]:
        reason = "schema_incomplete"
    elif not checks["schema_revision"]:
        reason = "schema_outdated"
    return HealthReport(
        status="ready" if ready else "not_ready",
        ready=ready,
        checks=checks,
        reason=reason,
        checked_at=checked_at,
    )
