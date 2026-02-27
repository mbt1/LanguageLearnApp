#!/bin/sh
# Install server dependencies. Called from postCreate.sh on container rebuild.
set -e

cd "$(dirname "$0")/../server"

echo "=== Server: installing Python dependencies ==="
uv sync
echo "=== Server: done ==="
