import os

import pytest

from src.settings import (
    ConfigurationError,
    apply_secret_values,
    build_settings,
)


def test_hosted_postgres_url_is_normalised():
    settings = build_settings(
        {
            "APP_ENV": "production",
            "DATABASE_URL": "postgres://user:password@db.example/app",
            "INITIAL_SHARED_PASSWORD": "a-long-production-password",
        }
    )

    assert settings.is_production
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.database_backend == "postgresql+psycopg"


@pytest.mark.parametrize(
    "password",
    ["stacks2026", "too-short"],
)
def test_production_rejects_unsafe_shared_password(password):
    with pytest.raises(ConfigurationError, match="INITIAL_SHARED_PASSWORD"):
        build_settings(
            {
                "APP_ENV": "production",
                "DATABASE_URL": "postgresql://user:password@db/app",
                "INITIAL_SHARED_PASSWORD": password,
            }
        )


def test_streamlit_secrets_do_not_override_environment(monkeypatch):
    monkeypatch.setenv("TEAM_NAME", "Environment Team")
    monkeypatch.delenv("SEASON_LABEL", raising=False)

    apply_secret_values(
        {
            "TEAM_NAME": "Secret Team",
            "SEASON_LABEL": "Secret Season",
        }
    )

    assert os.environ["TEAM_NAME"] == "Environment Team"
    assert os.environ["SEASON_LABEL"] == "Secret Season"
