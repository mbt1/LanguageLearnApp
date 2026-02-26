#!/bin/sh
set -e

cd /workspaces/LanguageLearnApp

if [ -d server ]; then
    cd server && uv sync
    cd ..
fi

if [ -d client ]; then
    cd client && pnpm install
    cd ..
fi
