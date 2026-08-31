"""Validated runtime configuration for local and hosted deployments."""

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


DEFAULT_SHARED_PASSWORD = "stacks2026"
DEPLOYMENT_KEYS = (
    "APP_ENV",
    "APP_TITLE",
    "TEAM_NAME",
    "SEASON_LABEL",
    "DATABASE_URL",
    "INITIAL_SHARED_PASSWORD",
    "DB_POOL_SIZE",
    "DB_MAX_OVERFLOW",
    "DB_POOL_RECYCLE_SECONDS",
    "DB_CONNECT_TIMEOUT_SECONDS",
    "SQL_ECHO",
    "LOG_LEVEL",
    "JSON_LOGS",
)


class ConfigurationError(RuntimeError):
    """Raised when required deployment configuration is missing or unsafe."""


def _integer(values, name, default, minimum=0):
    raw_value = values.get(name, default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as error:
        raise ConfigurationError(f"{name} must be an integer") from error
    if value < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}")
    return value


def _boolean(values, name, default=False):
    raw_value = str(values.get(name, default)).strip().lower()
    if raw_value in {"1", "true", "yes", "on"}:
        return True
    if raw_value in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be true or false")


def _normalise_database_url(database_url):
    if database_url.startswith("postgres://"):
        return database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )
    if database_url.startswith("postgresql://"):
        return database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )
    return database_url


@dataclass(frozen=True)
class Settings:
    environment: str
    app_title: str
    team_name: str
    season_label: str
    database_url: str
    initial_shared_password: str
    db_pool_size: int
    db_max_overflow: int
    db_pool_recycle_seconds: int
    db_connect_timeout_seconds: int
    sql_echo: bool
    log_level: str
    json_logs: bool

    @property
    def is_production(self):
        return self.environment == "production"

    @property
    def database_backend(self):
        return self.database_url.split(":", maxsplit=1)[0]


def build_settings(values: Mapping[str, object]) -> Settings:
    environment = str(values.get("APP_ENV", "development")).strip().lower()
    if environment not in {"development", "test", "production"}:
        raise ConfigurationError(
            "APP_ENV must be development, test, or production"
        )

    raw_database_url = str(values.get("DATABASE_URL", "")).strip()
    if not raw_database_url:
        raise ConfigurationError(
            "DATABASE_URL is required. Configure it in .env, the hosting "
            "environment, or Streamlit secrets."
        )
    database_url = _normalise_database_url(raw_database_url)
    if not database_url.startswith(("postgresql+psycopg://", "sqlite")):
        raise ConfigurationError(
            "DATABASE_URL must use PostgreSQL (or SQLite for automated tests)"
        )

    initial_password = str(
        values.get("INITIAL_SHARED_PASSWORD", DEFAULT_SHARED_PASSWORD)
    )
    if environment == "production":
        if not database_url.startswith("postgresql+psycopg://"):
            raise ConfigurationError(
                "Production deployments must use PostgreSQL"
            )
        if (
            initial_password == DEFAULT_SHARED_PASSWORD
            or len(initial_password) < 12
        ):
            raise ConfigurationError(
                "Production INITIAL_SHARED_PASSWORD must be changed and "
                "contain at least 12 characters"
            )

    log_level = str(values.get("LOG_LEVEL", "INFO")).strip().upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError(
            "LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
        )

    return Settings(
        environment=environment,
        app_title=str(
            values.get(
                "APP_TITLE",
                "Austin Stacks Performance Platform",
            )
        ).strip(),
        team_name=str(values.get("TEAM_NAME", "Austin Stacks")).strip(),
        season_label=str(
            values.get("SEASON_LABEL", "Club Championship 2026")
        ).strip(),
        database_url=database_url,
        initial_shared_password=initial_password,
        db_pool_size=_integer(values, "DB_POOL_SIZE", 5, minimum=1),
        db_max_overflow=_integer(
            values,
            "DB_MAX_OVERFLOW",
            10,
            minimum=0,
        ),
        db_pool_recycle_seconds=_integer(
            values,
            "DB_POOL_RECYCLE_SECONDS",
            1800,
            minimum=30,
        ),
        db_connect_timeout_seconds=_integer(
            values,
            "DB_CONNECT_TIMEOUT_SECONDS",
            10,
            minimum=1,
        ),
        sql_echo=_boolean(values, "SQL_ECHO", False),
        log_level=log_level,
        json_logs=_boolean(
            values,
            "JSON_LOGS",
            True,
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    return build_settings(os.environ)


def apply_secret_values(values: Mapping[str, object]) -> None:
    """Copy supported Streamlit secrets into missing environment variables."""

    for key in DEPLOYMENT_KEYS:
        value = values.get(key)
        if value is not None and key not in os.environ:
            os.environ[key] = str(value)
    get_settings.cache_clear()
