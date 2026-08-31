from sqlalchemy import text

from src.database.db import engine
from src.health import check_database_readiness


def test_database_is_ready_with_current_schema():
    report = check_database_readiness(engine, log_failures=False)

    assert report.ready
    assert report.status == "ready"
    assert all(report.checks.values())


def test_outdated_schema_is_not_ready():
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('old')")
        )

    report = check_database_readiness(engine, log_failures=False)

    assert not report.ready
    assert report.reason == "schema_outdated"
    assert report.checks["database_connection"]


def test_missing_required_table_is_not_ready():
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE turnover_stats"))

    report = check_database_readiness(engine, log_failures=False)

    assert not report.ready
    assert report.reason == "schema_incomplete"
    assert not report.checks["required_tables"]
