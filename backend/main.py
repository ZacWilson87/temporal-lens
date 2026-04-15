"""FastAPI application entrypoint for temporal-lens backend."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import health, workflows, graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="temporal-lens",
    description="Real-time DAG visualizer for Temporal + Langfuse AI agent executions",
    version="0.1.0",
)

# Allow the Vite dev server and any configured frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(graph.router)
