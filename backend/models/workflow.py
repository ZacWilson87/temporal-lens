"""Pydantic models for Temporal workflow summaries."""
from __future__ import annotations

from pydantic import BaseModel


class WorkflowSummary(BaseModel):
    workflow_id: str
    run_id: str
    workflow_type: str
    status: str  # running | completed | failed | cancelled | timed_out | terminated
    start_time: float | None  # unix timestamp
    close_time: float | None  # unix timestamp, None if still running
    task_queue: str
