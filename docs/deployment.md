# Deployment configuration

The application accepts configuration from three sources:

1. Hosting-platform environment variables.
2. Streamlit secrets.
3. A local `.env` file.

An existing environment variable always wins. Real `.env` and
`.streamlit/secrets.toml` files are ignored by Git.

## Local development

Copy `.env.example` to `.env`, choose local passwords, and make the PostgreSQL
password match `POSTGRES_PASSWORD` and the password inside `DATABASE_URL`.

```bash
docker compose up -d postgres
.venv/bin/alembic upgrade head
.venv/bin/streamlit run dashboard/app.py
```

Validate configuration without displaying credentials:

```bash
.venv/bin/python scripts/check_config.py
```

## Hosted deployment

Set `APP_ENV=production` and configure these secrets in the hosting platform:

- `DATABASE_URL` — hosted PostgreSQL URL, normally with `sslmode=require`.
- `INITIAL_SHARED_PASSWORD` — a unique value of at least 12 characters.

Optional application and pool settings are documented in `.env.example`.
Streamlit Community Cloud values can be copied from
`.streamlit/secrets.toml.example` into its secrets panel.
Because Community Cloud does not use this repository's Docker startup command,
run `alembic upgrade head` from a trusted environment against the hosted
database before starting the Streamlit deployment.

Production startup rejects SQLite, the demonstration password, short shared
passwords, malformed pool values, and missing database configuration.
`postgres://` and `postgresql://` URLs supplied by hosting providers are
normalized to the installed Psycopg 3 driver automatically.

## Container image

The included `Dockerfile`:

- installs the pinned requirements;
- runs as a non-root user;
- applies Alembic migrations before startup;
- exposes `/api/health` and database-aware `/api/ready` checks;
- includes a database-aware Docker health check;
- listens on the hosting platform's `PORT`, defaulting to `8501`.

Build and run it with environment variables supplied at runtime:

```bash
docker build -t gaa-analytics .
docker run --env-file .env -p 8501:8501 gaa-analytics
```

Never bake `.env`, database dumps, CSV backups, PDFs, or Streamlit secrets into
the image. `.dockerignore` excludes them.

For a non-container deployment that supports the Streamlit ASGI server, use:

```bash
alembic upgrade head
streamlit run server.py --server.address=0.0.0.0
```

See `docs/operations.md` for endpoint and logging details.

Production images install `requirements.txt`. Development and CI use
`requirements-dev.txt`, which adds the test runner without increasing the
deployed image dependency set.
