# temporal-lens — Agent Instructions

You are the sole implementer of temporal-lens. Work autonomously through
the phases below. Commit after each phase. The spec is the source of truth.
Make conservative choices and document inline.

## Repository layout

```
temporal-lens/
├── backend/          Python 3.11 + FastAPI backend
├── frontend/         React 18 + TypeScript + Vite frontend
├── docs/             Setup guide, tagging guide, screenshots
├── docker-compose.yml
├── .env.example
└── README.md
```

## Key decisions (do not relitigate)

- Backend: Python 3.11+, FastAPI, temporalio SDK, langfuse SDK
- Realtime: Server-Sent Events (SSE)
- Frontend: React 18 + TypeScript + Vite + React Flow + Tailwind + Zustand
- Persistence: none — stateless, all data from Temporal + Langfuse on demand
- Auth: none in v1 — credentials are env vars

## Development phases

1. Phase 0 — Monorepo skeleton + health endpoint + blank Vite canvas
2. Phase 1 — Temporal integration (list/get workflows)
3. Phase 2 — Langfuse integration (trace fetching)
4. Phase 3 — Graph builder (federation layer)
5. Phase 4 — SSE stream endpoint
6. Phase 5 — Frontend: WorkflowList + basic DAG
7. Phase 6 — Frontend: Custom nodes + DetailPanel
8. Phase 7 — Frontend: Live SSE stream
9. Phase 8 — Polish + docs

## Commit conventions

- `chore:` — infrastructure, deps, config
- `feat:` — new functionality
- `fix:` — bug fixes
- `docs:` — documentation only
