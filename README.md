# temporal-lens

> See your AI agents think. In real time.

temporal-lens federates Temporal workflow history and Langfuse LLM traces
into a live-updating DAG visualization. Point it at your setup and watch
your agents execute — activity by activity, LLM call by LLM call.

```bash
docker compose up
```

---

## Features

- **Live DAG** — React Flow canvas updates every 2 seconds via Server-Sent Events
- **5 node types** — Workflow root, Activity, LLM Span, HITL Gate, OPA Gate
- **Status colors** — pending (gray), running (blue pulse), success (green), failed (red), waiting (amber pulse)
- **LLM metadata** — model name, prompt/completion tokens, cost, latency per span
- **Activity metadata** — attempt count, duration, failure messages
- **HITL detection** — activities waiting on a Temporal signal render as amber "waiting" gates
- **Langfuse correlation** — LLM spans are nested under their parent Temporal activity (see [tagging guide](docs/tagging-guide.md))
- **Detail panel** — click any node to inspect its full metadata
- **Zero persistence** — stateless; all data comes from Temporal + Langfuse APIs on demand
- **60-second deploy** — single `docker compose up` command

---

## What gets visualized

```
┌─────────────────┐
│  WORKFLOW ROOT  │  — Temporal workflow execution metadata
└────────┬────────┘
         │
┌────────▼────────┐
│   ACTIVITY      │  — Temporal activity (name, status, duration, attempts)
│   NODE          │
└────────┬────────┘
         │
┌────────▼────────┐
│   LLM SPAN      │  — Langfuse span (model, tokens, latency, cost)
│   (child)       │
└────────┬────────┘
         │
┌────────▼────────┐
│   HITL GATE     │  — Signal wait (waiting/approved/rejected)
└────────┬────────┘
         │
┌────────▼────────┐
│   OPA GATE      │  — Policy evaluation (pass/fail + policy ID)
└─────────────────┘
```

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/zacwilson87/temporal-lens.git
cd temporal-lens

# 2. Configure
cp .env.example .env
# Edit .env with your Temporal address and (optionally) Langfuse credentials

# 3. Start
docker compose up --build

# 4. Open
open http://localhost:5173
```

The frontend opens at **http://localhost:5173**.  
The backend API is at **http://localhost:8000** (see `/health` to verify connectivity).

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `TEMPORAL_ADDRESS` | `localhost:7233` | Temporal server address |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `TEMPORAL_API_KEY` | _(empty)_ | API key for Temporal Cloud |
| `LANGFUSE_HOST` | `http://localhost:3000` | Langfuse instance URL |
| `LANGFUSE_PUBLIC_KEY` | _(empty)_ | Langfuse project public key |
| `LANGFUSE_SECRET_KEY` | _(empty)_ | Langfuse project secret key |
| `POLL_INTERVAL_S` | `2` | SSE graph refresh interval (seconds) |

---

## Langfuse integration

To see LLM spans nested under their parent activities, tag your Langfuse traces
with Temporal context. See the **[Tagging Guide](docs/tagging-guide.md)** for
full instrumentation examples.

---

## Architecture

```
temporal-lens/
├── backend/              # Python 3.11 + FastAPI + temporalio + langfuse SDK
│   ├── services/
│   │   ├── temporal_client.py   # Temporal SDK wrapper
│   │   ├── langfuse_client.py   # Langfuse HTTP client
│   │   └── graph_builder.py     # Federation → DAG
│   └── routers/
│       ├── health.py            # GET /health
│       ├── workflows.py         # GET /workflows[/{id}]
│       └── graph.py             # GET /workflows/{id}/graph[/stream]
└── frontend/             # React 18 + TypeScript + Vite + React Flow + Tailwind
    └── src/
        ├── components/          # WorkflowList, DAGCanvas, DetailPanel, 5 node types
        ├── hooks/               # useWorkflows, useGraphStream (SSE)
        ├── store/               # Zustand store
        └── lib/                 # api.ts, layout.ts (dagre)
```

**Realtime transport**: Server-Sent Events (SSE) — the backend streams a new
`GraphSnapshot` every `POLL_INTERVAL_S` seconds. The stream closes automatically
when the workflow reaches a terminal state.

---

## Local development

See [docs/setup.md](docs/setup.md) for detailed local dev and Temporal Cloud setup.

---

## License

MIT
