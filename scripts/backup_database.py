"""Create a portable PostgreSQL backup from the local Docker database."""

import argparse
from datetime import datetime
from pathlib import Path
import subprocess


DEFAULT_CONTAINER = "gaa-postgres"
DEFAULT_DATABASE = "gaa_analytics"
DEFAULT_USER = "gaa_admin"


def create_backup(
    output_dir: Path,
    *,
    container: str = DEFAULT_CONTAINER,
    database: str = DEFAULT_DATABASE,
    user: str = DEFAULT_USER,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = output_dir / f"{database}_{timestamp}.dump"
    command = [
        "docker",
        "exec",
        container,
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--username",
        user,
        "--dbname",
        database,
    ]
    try:
        with backup_path.open("wb") as output:
            subprocess.run(
                command,
                stdout=output,
                stderr=subprocess.PIPE,
                check=True,
            )
        with backup_path.open("rb") as source:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "--interactive",
                    container,
                    "pg_restore",
                    "--list",
                ],
                stdin=source,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=True,
            )
    except (OSError, subprocess.CalledProcessError) as error:
        backup_path.unlink(missing_ok=True)
        detail = (
            error.stderr.decode("utf-8", errors="replace")
            if isinstance(error, subprocess.CalledProcessError)
            and error.stderr
            else str(error)
        )
        raise RuntimeError(f"Database backup failed: {detail}") from error
    return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Back up the GAA Analytics PostgreSQL database."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("backups/database"),
    )
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--database", default=DEFAULT_DATABASE)
    parser.add_argument("--user", default=DEFAULT_USER)
    args = parser.parse_args()

    backup_path = create_backup(
        args.output_dir,
        container=args.container,
        database=args.database,
        user=args.user,
    )
    print(f"Backup created: {backup_path.resolve()}")


if __name__ == "__main__":
    main()
