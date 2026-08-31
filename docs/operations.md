# Health checks and operational logs

## Health endpoints

The deployment entry point is `server.py`. It serves the dashboard and these
unauthenticated endpoints without returning credentials or match data:

- `GET /api/health` — process liveness. Returns HTTP 200 when the server can
  answer requests.
- `GET /api/ready` — PostgreSQL readiness. Returns HTTP 200 only when the
  database connects, every required table exists, and Alembic is at the
  repository's current head. Otherwise it returns HTTP 503.
- `GET /_stcore/health` — Streamlit's built-in process health endpoint.

The equivalent command-line check is:

```bash
.venv/bin/python scripts/healthcheck.py --json
```

It exits with status `0` when ready and `1` otherwise. The Docker image uses
the quiet form for its container health check.

## Maintenance mode

The Streamlit app checks readiness before showing login or loading analytics.
An unavailable or outdated database produces a maintenance screen with a
support reference. It never displays the database URL, SQL, credentials, or a
raw exception. The check is cached for ten seconds and the user can request an
immediate retry.

## Structured logs

Set `JSON_LOGS=true` for one compact JSON object per line. Events include:

- `login_succeeded`, `login_failed`, and `logout_succeeded`;
- `match_imported` and `match_dataset_replaced`;
- `match_status_changed`, including publication;
- `users_saved`;
- readiness, startup, and Admin-action failures.

Failed-login identifiers are one-way fingerprints. Passwords, tokens,
authorization values, cookies, database URLs, connection strings, and URL
credentials are automatically redacted. Do not add CSV rows, player notes, or
request payloads to operational log fields. Detailed before/after match changes
belong in the database audit table.

Each user-facing operational error includes a support reference that can be
matched to the structured log event.
