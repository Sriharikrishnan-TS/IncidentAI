# IncidentOS

IncidentOS is a monorepo for an AI-powered engineering intelligence platform.

## Repository Layout

- `frontend/` — React + TypeScript frontend using App Router, TailwindCSS, and shadcn/ui-style components.
- `backend-go/` — Golang Gin API server.
- `ai-engine/` — Python AI engine for LangGraph-style agent orchestration.
- `infra/` — Docker Compose and infrastructure configuration.
- `docs/` — Architecture docs and workflow/contracts references.
- `scripts/` — Utility/setup scripts.
- `repos/` — Temporary cloned repositories (gitignored).

## Quick Start

1. Copy `.env.example` to `.env` and update values.
2. Start local stack:

```bash
cd infra
docker compose up --build
```

## Notes

This repository currently contains scaffold/starter modules only.
Production business logic is intentionally not implemented yet.
