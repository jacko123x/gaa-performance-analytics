# Application architecture

## Streamlit layer

- `dashboard/app.py` — login gate, cached-data request, role navigation, and
  routing only.
- `dashboard/dashboard_data.py` — loads Published database records, calculates
  metrics, and returns team-scoped dataframes.
- `dashboard/maintenance.py` — safe database-unavailable experience.
- `dashboard/match_analysis.py` — match selection, match-level aggregation,
  scoreline, and match-tab orchestration.
- `dashboard/match_tabs/` — one renderer per match-analysis tab.
- `dashboard/match_formatting.py` — shared display formats and colours.

## Admin layer

- `dashboard/admin.py` — stable public entry point.
- `dashboard/admin_pages.py` — Admin tab orchestration.
- `dashboard/admin_services.py` — CSV schemas, validation, reconciliation, and
  import-template preparation.
- `dashboard/admin_views/` — import, data-entry, review/publish, and user views.

## Data layer

- `src/settings.py` — validates environment variables and imported Streamlit
  secrets before database or authentication modules initialize.
- `src/health.py` — database connectivity, required-table, and Alembic-revision
  readiness checks.
- `src/logging_config.py` — JSON logs, event helpers, and secret redaction.
- `src/load_data.py` — application-facing database loaders.
- `src/database/repository.py` — read queries; analytics default to Published
  matches only.
- `src/database/admin_repository.py` — transactional imports, edits, lifecycle
  transitions, and audit history.
- `src/database/models.py` — SQLAlchemy schema.
- `migrations/` — Alembic database migrations.

## Verification

- `tests/test_match_workflow.py` — isolated lifecycle and auditing tests.
- `tests/test_streamlit_smoke.py` — role and dashboard rendering tests.
- `.github/workflows/tests.yml` — runs the suite for pushes and pull requests.
- `server.py` — deployment entry point with liveness and readiness routes.

Business rules should remain in services or repositories. Streamlit modules
should focus on widget state, layout, and presenting prepared results.
