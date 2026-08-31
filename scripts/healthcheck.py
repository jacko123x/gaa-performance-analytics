"""Exit successfully only when the application database is ready."""

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="Check GAA Analytics database and schema readiness."
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true")
    output_group.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    try:
        from src.health import check_database_readiness
        report = check_database_readiness(log_failures=not args.quiet)
    except Exception as error:
        if not args.quiet:
            payload = {
                "status": "unavailable",
                "ready": False,
                "reason": "configuration_error",
                "error_type": type(error).__name__,
            }
            print(json.dumps(payload) if args.json else "Not ready")
        raise SystemExit(1) from error

    if not args.quiet:
        if args.json:
            print(json.dumps(report.as_dict(), separators=(",", ":")))
        else:
            print("Ready" if report.ready else f"Not ready: {report.reason}")
    raise SystemExit(0 if report.ready else 1)


if __name__ == "__main__":
    main()
