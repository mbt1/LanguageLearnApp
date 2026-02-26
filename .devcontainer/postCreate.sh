#!/bin/sh
set -e

git config --global --add safe.directory /workspace
for dir in /workspace/*/; do
    git config --global --add safe.directory "$dir"
done

cd /workspace

if [ -d server ]; then
    cd server && uv sync
    cd ..
fi

if [ -d client ]; then
    cd client && pnpm install
    cd ..
fi
