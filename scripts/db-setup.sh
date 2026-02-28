#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
#
# Initialize pgroll and apply all outstanding migrations.
# Idempotent — safe to run on every container rebuild.
set -e

APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${DATABASE_URL:-postgresql://languagelearn:languagelearn@db:5432/languagelearn}"

# pgroll uses lib/pq which defaults to sslmode=require; our dev Postgres has no SSL.
case "$BASE_URL" in
    *sslmode=*) DB_URL="$BASE_URL" ;;
    *\?*)       DB_URL="${BASE_URL}&sslmode=disable" ;;
    *)          DB_URL="${BASE_URL}?sslmode=disable" ;;
esac

echo "=== DB: initializing pgroll ==="
pgroll init --postgres-url "$DB_URL" 2>&1 || true

MIGRATIONS_DIR="$APP_ROOT/server/migrations"
# Count migration files (JSON or YAML)
MIGRATION_COUNT=$(find "$MIGRATIONS_DIR" \( -name '*.json' -o -name '*.yaml' -o -name '*.yml' \) 2>/dev/null | wc -l)

if [ "$MIGRATION_COUNT" -gt 0 ]; then
    echo "=== DB: applying $MIGRATION_COUNT migration(s) ==="
    pgroll migrate "$MIGRATIONS_DIR" --complete --postgres-url "$DB_URL"
    echo "=== DB: migrations complete ==="
else
    echo "=== DB: no migration files found, skipping ==="
fi
