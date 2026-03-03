#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
#
# Production server entrypoint: run DB migrations then start uvicorn.
set -e

# pgroll uses lib/pq which requires explicit sslmode for non-TLS connections.
BASE_URL="${DATABASE_URL:-postgresql://languagelearn:languagelearn@db:5432/languagelearn}"
case "$BASE_URL" in
    *sslmode=*) DB_URL="$BASE_URL" ;;
    *\?*)       DB_URL="${BASE_URL}&sslmode=disable" ;;
    *)          DB_URL="${BASE_URL}?sslmode=disable" ;;
esac

MIGRATIONS_DIR="/app/server/migrations"

echo "=== Initializing pgroll ==="
pgroll init --postgres-url "$DB_URL" 2>&1 || true

MIGRATION_COUNT=$(find "$MIGRATIONS_DIR" \( -name '*.json' -o -name '*.yaml' -o -name '*.yml' \) 2>/dev/null | wc -l)
if [ "$MIGRATION_COUNT" -gt 0 ]; then
    echo "=== Applying $MIGRATION_COUNT migration(s) ==="
    pgroll migrate "$MIGRATIONS_DIR" --complete --postgres-url "$DB_URL"
    echo "=== Migrations complete ==="
else
    echo "=== No migrations found, skipping ==="
fi

echo "=== Starting uvicorn ==="
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
