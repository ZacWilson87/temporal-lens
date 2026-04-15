"""Pydantic models for the DAG graph snapshot."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: Literal["workflow", "activity", "llm_span", "hitl_gate", "opa_gate"]
    label: str
    status: Literal["pending", "running", "success", "failed", "waiting", "cancelled"]
    metadata: dict  # type-specific data (tokens, cost, attempts, etc.)
    position: dict | None = None  # {x, y} — optional, frontend auto-layouts


class GraphEdge(BaseModel):
    id: str
    source: str  # node id
    target: str  # node id
    type: Literal["dependency", "spawn", "signal"]


class GraphSnapshot(BaseModel):
    workflow_id: str
    workflow_name: str
    status: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    snapshot_at: float  # unix timestamp
