#!/bin/sh
# Install client dependencies and tools. Called from postCreate.sh on container rebuild.
set -e

APP_ROOT="$(dirname "$0")/.."

echo "=== Client: installing Node dependencies ==="
cd "$APP_ROOT/client"
pnpm install

echo "=== Root: installing workspace dependencies ==="
cd "$APP_ROOT"
pnpm install

echo "=== Playwright: installing Chromium ==="
pnpm exec playwright install chromium --with-deps

echo "=== Client: done ==="
