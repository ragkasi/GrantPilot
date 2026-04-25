#!/bin/sh
set -e

# Run Alembic migrations before starting the server.
# This is triggered when RUN_MIGRATIONS=true (set in docker-compose or deployment env).
# In local dev (SQLite), this is skipped and create_all_tables() handles schema creation.
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "[entrypoint] Running database migrations..."
    alembic upgrade head
    echo "[entrypoint] Migrations complete."
fi

echo "[entrypoint] Starting GrantPilot API on port ${PORT:-8000}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WORKERS:-1}" \
    --log-level "${LOG_LEVEL:-info}"
