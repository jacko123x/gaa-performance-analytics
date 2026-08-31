"""Validate deployment settings without printing any secrets."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from src.settings import ConfigurationError, get_settings


def main():
    try:
        settings = get_settings()
    except ConfigurationError as error:
        raise SystemExit(f"Configuration invalid: {error}") from error

    print("Configuration valid")
    print(f"Environment: {settings.environment}")
    print(f"Application: {settings.app_title}")
    print(f"Team: {settings.team_name}")
    print(f"Season: {settings.season_label}")
    print(f"Database backend: {settings.database_backend}")
    print(f"Database pool: {settings.db_pool_size}")
    print(f"Maximum overflow: {settings.db_max_overflow}")


if __name__ == "__main__":
    main()
