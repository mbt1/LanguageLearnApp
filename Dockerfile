# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
#
# Multi-stage build with three deployable targets:
#   server  — FastAPI API server
#   caddy   — Caddy reverse proxy serving the React SPA + proxying /v1/* to server
#   backup  — hourly pg_dump + optional S3 sync

# ────────────────────────────────────────────────────────────────────────────
# Stage 1: Build the React client
# ────────────────────────────────────────────────────────────────────────────
FROM node:22-alpine AS client-builder
WORKDIR /app/client

# Install dependencies (client has its own pnpm-lock.yaml)
COPY client/package.json client/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

# Build
COPY client/ .
RUN pnpm build

# ────────────────────────────────────────────────────────────────────────────
# Stage 2: Install Python dependencies with uv
# ────────────────────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS server-deps
WORKDIR /app/server

COPY server/pyproject.toml server/uv.lock ./
RUN uv sync --frozen --no-dev

# ────────────────────────────────────────────────────────────────────────────
# Stage 3: FastAPI server runtime  (target: server)
# ────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS server

ARG PGROLL_VERSION=0.16.1

# Install curl for pgroll download, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && ARCH=$(dpkg --print-architecture) \
    && curl -fsSL \
       "https://github.com/xataio/pgroll/releases/download/v${PGROLL_VERSION}/pgroll.linux.${ARCH}" \
       -o /usr/local/bin/pgroll \
    && chmod +x /usr/local/bin/pgroll \
    && apt-get remove -y curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=server-deps /app/server/.venv /app/server/.venv
COPY server/ /app/server/
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/server
ENV PATH="/app/server/.venv/bin:$PATH"
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]

# ────────────────────────────────────────────────────────────────────────────
# Stage 4: Caddy with built React SPA  (target: caddy)
# ────────────────────────────────────────────────────────────────────────────
FROM caddy:2 AS caddy
COPY --from=client-builder /app/client/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile

# ────────────────────────────────────────────────────────────────────────────
# Stage 5: Backup service  (target: backup)
# ────────────────────────────────────────────────────────────────────────────
FROM alpine:3.20 AS backup
RUN apk add --no-cache postgresql17-client aws-cli bash
COPY scripts/backup.sh /backup.sh
COPY scripts/backup-entrypoint.sh /backup-entrypoint.sh
RUN chmod +x /backup.sh /backup-entrypoint.sh
ENTRYPOINT ["/backup-entrypoint.sh"]
