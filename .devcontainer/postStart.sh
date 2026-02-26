#!/bin/sh
set -e

echo "Verifying dev container tools..."
echo ""

ok=true

check() {
    if command -v "$1" > /dev/null 2>&1; then
        version=$(eval "$2")
        printf "  %-12s %s\n" "$1" "$version"
    else
        printf "  %-12s MISSING\n" "$1"
        ok=false
    fi
}

check python   "python --version"
check node     "node --version"
check pnpm     "pnpm --version"
check uv       "uv --version"
check pwsh     "pwsh --version"
check gh       "gh --version | head -1"
check pgroll   "pgroll --version"
check psql     "psql --version"

echo ""

if PGPASSWORD=languagelearn psql -h db -U languagelearn -c "SELECT 1" > /dev/null 2>&1; then
    echo "  PostgreSQL    connected"
else
    echo "  PostgreSQL    UNREACHABLE"
    ok=false
fi

echo ""

if [ "$ok" = true ]; then
    echo "All tools verified."
else
    echo "WARNING: Some tools are missing or unreachable."
fi
