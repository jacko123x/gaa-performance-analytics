"""Restore a PostgreSQL custom-format backup into the local Docker DB."""

import argparse
from pathlib import Path
import subprocess

from backup_database import (
    DEFAULT_CONTAINER,
    DEFAULT_DATABASE,
    DEFAULT_USER,
)


def restore_backup(
    backup_path: Path,
    *,
    container: str = DEFAULT_CONTAINER,
    database: str = DEFAULT_DATABASE,
    user: str = DEFAULT_USER,
) -> None:
    if not backup_path.is_file():
        raise FileNotFoundError(f"Backup does not exist: {backup_path}")
    command = [
        "docker",
        "exec",
        "--interactive",
        container,
        "pg_restore",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
        "--username",
        user,
        "--dbname",
        database,
    ]
    try:
        with backup_path.open("rb") as source:
            subprocess.run(
                command,
                stdin=source,
                stderr=subprocess.PIPE,
                check=True,
            )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = (
            error.stderr.decode("utf-8", errors="replace")
            if isinstance(error, subprocess.CalledProcessError)
            and error.stderr
            else str(error)
        )
        raise RuntimeError(f"Database restore failed: {detail}") from error


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Restore the GAA Analytics PostgreSQL database."
    )
    parser.add_argument("backup", type=Path)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--database", default=DEFAULT_DATABASE)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument(
        "--confirm-database",
        help="Required safety check: enter the target database name.",
    )
    args = parser.parse_args()

    if args.confirm_database != args.database:
        parser.error(
            "Restore replaces database objects. Pass "
            f"--confirm-database {args.database} to continue."
        )
    restore_backup(
        args.backup,
        container=args.container,
        database=args.database,
        user=args.user,
    )
    print(f"Restored {args.backup} into {args.database}.")


if __name__ == "__main__":
    main()
