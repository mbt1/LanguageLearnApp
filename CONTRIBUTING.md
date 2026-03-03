# Contributing

Thank you for your interest in contributing to LanguageLearn!

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | 22 | [nodejs.org](https://nodejs.org) or `nvm install 22` |
| pnpm | 10+ | `corepack enable` |
| Python | 3.12 | [python.org](https://python.org) or `pyenv install 3.12` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | 24+ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| PostgreSQL | 17 | Via Docker (recommended) |

The easiest way to get started is with the **Dev Container** (VS Code + Docker):

1. Open the repo in VS Code
2. Install the "Dev Containers" extension
3. Click "Reopen in Container"

The container includes all tools pre-installed and starts a local PostgreSQL instance automatically.

## Running Locally

```bash
# Install all dependencies
pnpm install

# Start the backend (runs migrations automatically)
cd server && uv run uvicorn main:app --reload

# Start the frontend (separate terminal)
pnpm --filter client dev
```

The app is available at `http://localhost:5173`. The API is at `http://localhost:8000`.

## Running Tests

```bash
# Server tests (pytest)
cd server && uv run pytest

# Client unit tests (vitest)
pnpm --filter client test

# Client E2E tests (Playwright, requires running server + client)
pnpm --filter client test:e2e

# Type checking
pnpm --filter client typecheck
cd server && uv run pyright
```

All tests must pass before submitting a PR. Coverage should not regress.

## Code Style

**Python** — formatted and linted with [ruff](https://docs.astral.sh/ruff/):

```bash
cd server && uv run ruff check . && uv run ruff format .
```

**TypeScript** — linted with ESLint:

```bash
pnpm --filter client lint
```

No configuration changes to linters without discussion in an issue first.

## PR Checklist

- [ ] All existing tests pass (`pytest`, `vitest`, `playwright`)
- [ ] New behaviour covered by tests (TDD preferred)
- [ ] `pnpm --filter client typecheck` reports 0 errors
- [ ] `uv run pyright` reports 0 errors
- [ ] `uv run ruff check .` reports 0 issues
- [ ] No secrets committed (check `.env` is in `.gitignore`)
- [ ] PR description explains *why*, not just *what*

## Architecture

See [docs/architecture.md](docs/architecture.md) for a full overview of the tech stack, auth
flow, learning model, and deployment.

## Licence

By contributing you agree that your contributions will be licensed under the
[Apache 2.0 licence](LICENSE).
