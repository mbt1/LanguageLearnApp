#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
#
# Hourly backup script. Retains 24 hourly + 7 daily backups.
# Optionally syncs to S3 when S3_BUCKET is set.
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
HOURLY_DIR=/backups/hourly
DAILY_DIR=/backups/daily

mkdir -p "$HOURLY_DIR" "$DAILY_DIR"

echo "=== Backup started at $TIMESTAMP ==="

# Dump database
pg_dump "$DATABASE_URL" | gzip > "$HOURLY_DIR/backup_${TIMESTAMP}.sql.gz"
echo "=== Dump written: $HOURLY_DIR/backup_${TIMESTAMP}.sql.gz ==="

# Retain last 24 hourly backups
# shellcheck disable=SC2012
ls -t "$HOURLY_DIR"/backup_*.sql.gz 2>/dev/null | tail -n +25 | xargs -r rm -f

# Daily snapshot at midnight; retain 7
if [ "$(date +%H)" = "00" ]; then
    cp "$HOURLY_DIR/backup_${TIMESTAMP}.sql.gz" "$DAILY_DIR/"
    echo "=== Daily snapshot promoted ==="
    # shellcheck disable=SC2012
    ls -t "$DAILY_DIR"/backup_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -f
fi

# Optional S3 upload
if [ -n "${S3_BUCKET:-}" ]; then
    echo "=== Syncing to s3://$S3_BUCKET/backups/ ==="
    aws s3 sync /backups "s3://$S3_BUCKET/backups/" --only-show-errors
fi

echo "=== Backup complete ==="
