#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
#
# Entrypoint for the backup container: registers hourly cron job and runs crond.
echo "0 * * * * /backup.sh >> /proc/1/fd/1 2>&1" > /etc/crontabs/root
echo "=== Backup service started (runs hourly) ==="
exec crond -f -d 8
