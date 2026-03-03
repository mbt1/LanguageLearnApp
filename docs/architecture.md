# Architecture

## Overview

```
Internet → Caddy (80/443, auto-HTTPS)
              ├── /v1/*  →  server:8000 (FastAPI)
              └── /*     →  /srv (React SPA, try_files → index.html)

server → postgres:17 (named volume)
backup → postgres:17 (hourly pg_dump, optional S3 sync)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| API client | Fetch with JWT bearer + silent refresh |
| Backend | Python 3.12, FastAPI, uvicorn |
| Database | PostgreSQL 17, raw SQL via psycopg v3 |
| Migrations | pgroll (expand/contract schema migrations) |
| Auth | Email+password login, WebAuthn passkeys, JWT (access) + httpOnly cookie (refresh) |
| SRS | FSRS algorithm (`fsrs` PyPI package) |
| Reverse proxy | Caddy 2 (auto-HTTPS via Let's Encrypt) |
| Deployment | Docker Compose, AWS EC2 arm64 (t4g.small) |
| Infrastructure | OpenTofu (Terraform-compatible) |

## Repository Layout

```
client/          React SPA
  src/
    api/         HTTP client + typed API wrappers
    auth/        AuthContext, passkey helpers
    components/  Shared UI components
    pages/       Route-level page components
  e2e/           Playwright end-to-end tests

server/          FastAPI application
  auth/          JWT issuance, WebAuthn, passkey endpoints
  content/       Course, concept, exercise models + CRUD
  srs/           FSRS scheduler, session logic
  db/            Connection pool, migration helpers
  migrations/    pgroll JSON migration files

api/             Shared OpenAPI types (generated)
scripts/         Docker entrypoint, backup, rotate-secrets
infra/           OpenTofu for ephemeral CI test environments (x86)
```

## Auth Flow

1. User registers with email + password → server returns `access_token` (15 min JWT)
2. Refresh token stored in httpOnly cookie (7 days)
3. Client stores access token in JS memory (not localStorage)
4. On 401: client silently calls `POST /v1/auth/refresh` → new access token
5. Passkeys registered via WebAuthn — replace password on supported browsers

## Learning Model

- **Concept-based**: content is organised into concepts (vocabulary, grammar, etc.)
- **CEFR levels**: A1 → C2 progression within each course
- **FSRS algorithm**: spaced repetition scheduling based on memory stability
- **Exercise progression**: multiple choice → cloze → reverse typing → typing
- **Mastery**: typing stage + long FSRS interval; can regress on errors
- **Prerequisite cap**: concept cannot advance beyond its weakest prerequisite

## Exercise Types

| Type | Description |
|------|-------------|
| `multiple_choice` | Pick the correct option from 2–4 choices |
| `cloze` | Fill in the blank within a sentence |
| `reverse_typing` | Type the source-language equivalent |
| `typing` | Type the target-language answer |

## API Conventions

- Base path: `/v1/`
- Auth: `Authorization: Bearer <access_token>` header
- Errors: `{ "detail": "..." }` JSON body with appropriate HTTP status
- Content negotiation: `application/json` throughout
- Health check: `GET /v1/health` → `{ "status": "ok" }`

## Deployment

See [docker-compose.yml](../docker-compose.yml) and [.env.example](../.env.example) for
self-hosting instructions. Copy `.env.example` to `.env`, fill in secrets, and run:

```bash
docker compose pull
docker compose up -d
```

Caddy handles TLS automatically via Let's Encrypt. Set `DOMAIN` to your domain name.
