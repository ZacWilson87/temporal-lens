# temporal-lens — Setup Guide

## Prerequisites

- Docker + Docker Compose v2
- A running Temporal server (self-hosted or Temporal Cloud)
- A running Langfuse instance (optional — LLM spans appear only if configured)

---

## Quickstart (local Temporal dev server)

```bash
# 1. Start a local Temporal dev server (if you don't have one)
temporal server start-dev

# 2. Clone temporal-lens
git clone https://github.com/zacwilson87/temporal-lens.git
cd temporal-lens

# 3. Copy and edit the env file
cp .env.example .env
# Edit .env — TEMPORAL_ADDRESS=localhost:7233 is the default

# 4. Start temporal-lens
docker compose up --build

# 5. Open the UI
open http://localhost:5173
```

---

## Temporal Cloud setup

1. Create a namespace in [Temporal Cloud](https://cloud.temporal.io).
2. Generate an API key (Settings → API Keys).
3. Update `.env`:

```bash
TEMPORAL_ADDRESS=<your-namespace>.tmprl.cloud:7233
TEMPORAL_NAMESPACE=<your-namespace>.<account-id>
TEMPORAL_API_KEY=<your-api-key>
```

4. Run `docker compose up --build`.

---

## Langfuse setup

temporal-lens supports both Langfuse Cloud and self-hosted Langfuse.

### Langfuse Cloud

1. Create a project at [langfuse.com](https://langfuse.com).
2. Copy your **Public Key** and **Secret Key** from Settings → API Keys.
3. Update `.env`:

```bash
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

### Self-hosted Langfuse

Follow the [Langfuse self-hosting guide](https://langfuse.com/docs/deployment/self-host), then set:

```bash
LANGFUSE_HOST=http://your-langfuse-host:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

---

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

---

## Configuration reference

| Variable | Default | Description |
|---|---|---|
| `TEMPORAL_ADDRESS` | `localhost:7233` | Temporal server address |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `TEMPORAL_API_KEY` | _(empty)_ | API key for Temporal Cloud |
| `LANGFUSE_HOST` | `http://localhost:3000` | Langfuse instance URL |
| `LANGFUSE_PUBLIC_KEY` | _(empty)_ | Langfuse project public key |
| `LANGFUSE_SECRET_KEY` | _(empty)_ | Langfuse project secret key |
| `POLL_INTERVAL_S` | `2` | SSE graph refresh interval (seconds) |
