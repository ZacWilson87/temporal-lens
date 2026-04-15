"""REST + SSE endpoints for DAG graph data."""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from config import settings
from models.graph import GraphSnapshot
from services.graph_builder import build_graph, is_terminal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows")


@router.get("/{workflow_id}/graph", response_model=GraphSnapshot)
async def get_graph(workflow_id: str) -> GraphSnapshot:
    """Single-fetch: return a GraphSnapshot for the given workflow."""
    snapshot = await build_graph(workflow_id)
    if not snapshot.nodes:
        raise HTTPException(status_code=404, detail="Workflow not found or has no events")
    return snapshot


@router.get("/{workflow_id}/graph/stream")
async def stream_graph(workflow_id: str, request: Request) -> StreamingResponse:
    """
    SSE stream: emit a GraphSnapshot every POLL_INTERVAL_S seconds.
    Stops when the workflow reaches a terminal state or the client disconnects.
    """

    async def event_generator():
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("SSE client disconnected for workflow %s", workflow_id)
                break

            try:
                snapshot = await build_graph(workflow_id)
                payload = snapshot.model_dump_json()
                yield f"data: {payload}\n\n"

                if is_terminal(snapshot):
                    logger.info(
                        "Workflow %s reached terminal state %s; closing SSE stream",
                        workflow_id,
                        snapshot.status,
                    )
                    break
            except Exception as exc:
                logger.error("SSE error for workflow %s: %s", workflow_id, exc)
                # Send an error event so the client knows something went wrong
                yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
                break

            await asyncio.sleep(settings.poll_interval_s)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
