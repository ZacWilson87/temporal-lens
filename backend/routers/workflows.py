"""REST endpoints for listing and fetching workflow summaries."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.workflow import WorkflowSummary
from services import temporal_client

router = APIRouter(prefix="/workflows")


@router.get("", response_model=list[WorkflowSummary])
async def list_workflows(limit: int = 50) -> list[WorkflowSummary]:
    """Return the most-recent *limit* workflow executions."""
    return await temporal_client.list_workflows(limit=min(limit, 200))


@router.get("/{workflow_id}", response_model=WorkflowSummary)
async def get_workflow(workflow_id: str) -> WorkflowSummary:
    summary = await temporal_client.get_workflow(workflow_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return summary
