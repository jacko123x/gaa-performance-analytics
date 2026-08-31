# Database backups

The application data now lives in PostgreSQL, so GitHub is not a database
backup. Create a backup before migrations, bulk imports, or major corrections:

```bash
.venv/bin/python scripts/backup_database.py
```

Backups are written to `backups/database/` and deliberately ignored by Git.
Copy important backups to a separate encrypted drive or cloud location.

To restore, stop Streamlit first and explicitly confirm the target database:

```bash
.venv/bin/python scripts/restore_database.py \
  backups/database/gaa_analytics_YYYYMMDD_HHMMSS.dump \
  --confirm-database gaa_analytics
```

The restore command replaces database objects. Make a fresh backup immediately
before using it.

## Scheduling on macOS

Run the backup command from a macOS `launchd` job at least daily and while the
Docker container is running. The job's working directory must be this project
folder and its command should use the absolute path to `.venv/bin/python`.
Keep several recent daily backups and at least one monthly backup somewhere
outside this Mac. Test a restore periodically; an untested backup is only an
assumption.
