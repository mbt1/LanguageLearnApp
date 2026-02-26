# LanguageLearn

An open-source language learning platform built on spaced repetition and honest progress tracking.

## Why LanguageLearn?

Most language learning apps optimize for engagement — streaks, badges, and time-in-app. LanguageLearn optimizes for **comprehension**. Every design decision serves one question: *did the learner actually acquire the language?*

## Principles

### Comprehension over engagement

We measure success by what you can produce and understand, not how many days in a row you opened the app. If you've mastered today's material in 10 minutes, the session is done — we won't pad it with filler.

### Honest progress

Your progress reflects actual mastery. If you can only recognize a word in a multiple-choice list, you haven't learned it yet. If you forget a word you once knew, your score goes back down. The CEFR-level progress bars (A1 through C2) show what you genuinely know, not what you've been exposed to.

### Production, not recognition

Mastery means you can **produce** the language — type a translation from memory, fill in a blank without hints. The exercise progression moves from recognition (multiple choice) through context (cloze) to full production (typing). You advance when you demonstrate real recall, not when you've done enough repetitions.

### Review before new material

If your existing knowledge is slipping, we hold you back from new concepts until foundations are solid. This feels slower but produces durable learning. Cramming forward while forgetting backward is the illusion of progress.

### Smart prerequisites

A grammar concept won't ask you to produce something harder than your weakest building block. If you're still practicing "aprender" with fill-in-the-blank exercises, we won't ask you to type a full sentence using the past tense of "aprender." Difficulty flows upward through the dependency graph.

### No gimmicks

No streaks. No leaderboards. No hearts or lives. No artificial urgency. Learning a language is a long-term endeavor — the app should support sustained, honest practice, not exploit psychology for retention metrics.

## How It Works

### Concepts, not flashcards

The unit of learning is a **concept** — a vocabulary word or grammar rule. Each concept is tagged with a CEFR proficiency level (A1 through C2) and placed in a learning timeline. The system schedules concepts for review using the [FSRS](https://github.com/open-spaced-repetition/py-fsrs) spaced repetition algorithm.

### Exercise progression

Each concept is tested through increasingly difficult exercise types:

1. **Multiple choice** — pick the correct answer from four options
2. **Cloze** — fill in the missing word in a sentence
3. **Reverse typing** — see the target language, type your native language
4. **Typing** — see your native language, type the target language

You advance to the next difficulty when you consistently answer correctly — not after a fixed number of attempts.

### CEFR progress tracking

Progress is displayed as mastery percentages across the Common European Framework levels:

```
A1  ██████████████████████ 100%
A2  █████████████████░░░░   89%
B1  ████░░░░░░░░░░░░░░░░░   20%
B2  █░░░░░░░░░░░░░░░░░░░░    3%
C1  ░░░░░░░░░░░░░░░░░░░░░    0%
C2  ░░░░░░░░░░░░░░░░░░░░░    0%
```

These map to real-world proficiency certifications (DELE, DELF, JLPT, etc.), giving your progress immediate, tangible meaning.

## Architecture

LanguageLearn is a server-first web application:

- **Client** — React + TypeScript, communicating with the server via a versioned REST API
- **Server** — Python (FastAPI), handling scheduling, grading, and user progress
- **Database** — PostgreSQL

The API is defined using OpenAPI 3.1, with the spec as the single source of truth between client and server. See the `api/` directory for the current spec.

### Open-core model

The core platform is open source under the Apache 2.0 license. Premium features (advanced grading, speech analysis, language-specific plugins) are developed separately and interact through the same public API contracts.

## Self-Hosting

LanguageLearn is designed to be self-hosted with a single command:

```bash
docker compose up
```

This starts PostgreSQL, the API server, and a Caddy reverse proxy with automatic HTTPS. Configure your domain and credentials in `.env`.

## Development

### Prerequisites

- [Node.js 22+](https://nodejs.org/) and [pnpm](https://pnpm.io/) (client)
- [Python 3.12+](https://www.python.org/) and [uv](https://github.com/astral-sh/uv) (server)
- [Docker](https://www.docker.com/) (for PostgreSQL in development)

### Getting started

```powershell
# Clone the repo
git clone https://github.com/your-org/LanguageLearnApp.git
cd LanguageLearnApp

# Start the development environment
./scripts/dev.ps1
```

See `scripts/` for available development commands.

### Project structure

```
LanguageLearnApp/
├── api/              # OpenAPI specs (source of truth)
│   └── v1/
├── client/           # React + TypeScript + Vite
├── server/           # Python + FastAPI
├── scripts/          # PowerShell dev scripts
├── docker-compose.yml
└── README.md
```

### Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
