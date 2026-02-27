#!/bin/sh
# Post-create setup for LanguageLearnApp.
# Works standalone (app repo only) or when called from a parent workspace.
set -e

APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

git config --global --add safe.directory "$APP_ROOT"

cd "$APP_ROOT"

if [ -f scripts/install-server.sh ]; then
    sh scripts/install-server.sh
fi

if [ -f scripts/install-client.sh ]; then
    sh scripts/install-client.sh
fi
