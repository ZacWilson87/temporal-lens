"""
Federation layer — merges Temporal history + Langfuse traces into a DAG.

Convention for Langfuse correlation:
  Langfuse traces must be tagged with:
    temporal_workflow_id:<workflow_id>
    temporal_activity_id:<activity_id>
    temporal_activity_type:<activity_type>
"""
from __future__ import annotations

import time
import logging
from typing import Any

from models.graph import GraphEdge, GraphNode, GraphSnapshot
from services import temporal_client, langfuse_client

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = temporal_client.TERMINAL_STATUSES


async def build_graph(workflow_id: str) -> GraphSnapshot:
    """
    1. Fetch Temporal workflow execution + history
    2. Fetch Langfuse traces filtered by workflow_id tag
    3. Correlate Langfuse spans to Temporal activities by activity_id tag
    4. Detect HITL nodes (activities waiting on a signal)
    5. Build and return GraphSnapshot
    """
    # --- 1. Temporal data -----------------------------------------------
    summary = await temporal_client.get_workflow(workflow_id)
    if summary is None:
        # Return a minimal error snapshot
        return GraphSnapshot(
            workflow_id=workflow_id,
            workflow_name="unknown",
            status="failed",
            nodes=[],
            edges=[],
            snapshot_at=time.time(),
        )

    history_events = await temporal_client.get_history(workflow_id)
    activities = temporal_client.parse_activities_from_history(history_events)
    hitl_signal_names = temporal_client.detect_hitl_signals(history_events)

    # --- 2. Langfuse traces ---------------------------------------------
    traces = await langfuse_client.get_traces_for_workflow(workflow_id)
    llm_spans = langfuse_client.extract_llm_spans(traces)

    # --- 3. Correlate spans → activities --------------------------------
    # Build a mapping: activity_id → list of llm span dicts
    spans_by_activity: dict[str, list[dict]] = {}
    orphan_spans: list[dict] = []
    for span in llm_spans:
        aid = span.get("activity_id")
        if aid:
            spans_by_activity.setdefault(aid, []).append(span)
        else:
            orphan_spans.append(span)

    # --- 4. Build nodes + edges -----------------------------------------
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    # Root workflow node
    root_id = f"workflow:{workflow_id}"
    nodes.append(
        GraphNode(
            id=root_id,
            type="workflow",
            label=summary.workflow_type or workflow_id,
            status=_map_status(summary.status),
            metadata={
                "workflow_id": summary.workflow_id,
                "run_id": summary.run_id,
                "task_queue": summary.task_queue,
                "start_time": summary.start_time,
                "close_time": summary.close_time,
            },
        )
    )

    prev_activity_id: str | None = None

    for act in activities:
        aid = act["activity_id"]
        activity_node_id = f"activity:{aid}"

        # Determine if this is a HITL gate
        is_hitl = act.get("is_hitl") or bool(hitl_signal_names)
        node_type = "hitl_gate" if is_hitl else "activity"

        # If still running and has associated signal events, mark as waiting
        status = act["status"]
        if is_hitl and status == "running":
            status = "waiting"

        # Compute duration
        duration_s = None
        if act.get("started_time") and act.get("close_time"):
            duration_s = round(act["close_time"] - act["started_time"], 3)

        nodes.append(
            GraphNode(
                id=activity_node_id,
                type=node_type,
                label=act["activity_type"] or aid,
                status=_map_status(status),
                metadata={
                    "activity_id": aid,
                    "activity_type": act["activity_type"],
                    "attempt": act.get("attempt", 1),
                    "scheduled_time": act.get("scheduled_time"),
                    "started_time": act.get("started_time"),
                    "close_time": act.get("close_time"),
                    "duration_s": duration_s,
                    "failure_message": act.get("failure_message"),
                },
            )
        )

        # Edge from root or previous activity
        source = prev_activity_id if prev_activity_id else root_id
        edge_type = "signal" if is_hitl else "dependency"
        edges.append(
            GraphEdge(
                id=f"edge:{source}->{activity_node_id}",
                source=source,
                target=activity_node_id,
                type=edge_type,
            )
        )
        prev_activity_id = activity_node_id

        # LLM span children
        for span in spans_by_activity.get(aid, []):
            span_node_id = f"span:{span['span_id']}"
            nodes.append(
                GraphNode(
                    id=span_node_id,
                    type="llm_span",
                    label=span["name"],
                    status=_map_status(span["status"]),
                    metadata={
                        "span_id": span["span_id"],
                        "trace_id": span["trace_id"],
                        "model": span.get("model"),
                        "prompt_tokens": span.get("prompt_tokens", 0),
                        "completion_tokens": span.get("completion_tokens", 0),
                        "total_tokens": span.get("total_tokens", 0),
                        "cost_usd": span.get("cost_usd"),
                        "latency_ms": span.get("latency_ms"),
                        "start_time": span.get("start_time"),
                        "end_time": span.get("end_time"),
                    },
                )
            )
            edges.append(
                GraphEdge(
                    id=f"edge:{activity_node_id}->{span_node_id}",
                    source=activity_node_id,
                    target=span_node_id,
                    type="spawn",
                )
            )

    # Orphaned LLM spans (no matching activity) — attach directly to workflow root
    for span in orphan_spans:
        span_node_id = f"span:{span['span_id']}"
        nodes.append(
            GraphNode(
                id=span_node_id,
                type="llm_span",
                label=span["name"],
                status=_map_status(span["status"]),
                metadata={
                    "span_id": span["span_id"],
                    "trace_id": span["trace_id"],
                    "model": span.get("model"),
                    "prompt_tokens": span.get("prompt_tokens", 0),
                    "completion_tokens": span.get("completion_tokens", 0),
                    "total_tokens": span.get("total_tokens", 0),
                    "cost_usd": span.get("cost_usd"),
                    "latency_ms": span.get("latency_ms"),
                    "start_time": span.get("start_time"),
                    "end_time": span.get("end_time"),
                },
            )
        )
        edges.append(
            GraphEdge(
                id=f"edge:{root_id}->{span_node_id}",
                source=root_id,
                target=span_node_id,
                type="spawn",
            )
        )

    return GraphSnapshot(
        workflow_id=workflow_id,
        workflow_name=summary.workflow_type or workflow_id,
        status=summary.status,
        nodes=nodes,
        edges=edges,
        snapshot_at=time.time(),
    )


def _map_status(raw: str | None) -> str:
    """Normalize varied status strings to our fixed vocabulary."""
    if raw is None:
        return "pending"
    mapping = {
        "running": "running",
        "completed": "success",
        "success": "success",
        "failed": "failed",
        "error": "failed",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "terminated": "cancelled",
        "timed_out": "failed",
        "pending": "pending",
        "waiting": "waiting",
        "scheduled": "pending",
    }
    return mapping.get(raw.lower(), "pending")


def is_terminal(snapshot: GraphSnapshot) -> bool:
    return snapshot.status.lower() in TERMINAL_STATUSES
