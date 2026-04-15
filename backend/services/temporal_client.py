"""Temporal SDK wrapper — list executions, fetch history."""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from temporalio.client import Client, WorkflowExecutionStatus, WorkflowHistory
from temporalio.api.enums.v1 import EventType
from temporalio.api.history.v1 import HistoryEvent

from config import settings
from models.workflow import WorkflowSummary

logger = logging.getLogger(__name__)

# Singleton client; initialized lazily
_client: Client | None = None
_client_lock = asyncio.Lock()

# Map Temporal SDK status enum → our string labels
_STATUS_MAP: dict[WorkflowExecutionStatus, str] = {
    WorkflowExecutionStatus.RUNNING: "running",
    WorkflowExecutionStatus.COMPLETED: "completed",
    WorkflowExecutionStatus.FAILED: "failed",
    WorkflowExecutionStatus.CANCELED: "cancelled",
    WorkflowExecutionStatus.TERMINATED: "terminated",
    WorkflowExecutionStatus.CONTINUED_AS_NEW: "completed",
    WorkflowExecutionStatus.TIMED_OUT: "timed_out",
}

TERMINAL_STATUSES = {"completed", "failed", "cancelled", "terminated", "timed_out"}


async def get_client() -> Client:
    global _client
    async with _client_lock:
        if _client is None:
            kwargs: dict = {
                "target_host": settings.temporal_address,
                "namespace": settings.temporal_namespace,
            }
            if settings.temporal_api_key:
                from temporalio.service import TLSConfig
                kwargs["tls"] = TLSConfig()
                kwargs["api_key"] = settings.temporal_api_key
            _client = await Client.connect(**kwargs)
    return _client


async def is_connected() -> bool:
    """Return True if we can reach the Temporal server."""
    try:
        client = await get_client()
        await client.service_client.operator_service.describe_namespace(
            namespace=settings.temporal_namespace
        )
        return True
    except Exception as exc:
        logger.warning("Temporal health check failed: %s", exc)
        return False


async def list_workflows(limit: int = 50) -> list[WorkflowSummary]:
    """Return the most-recent *limit* workflow executions."""
    client = await get_client()
    summaries: list[WorkflowSummary] = []
    async for exec in client.list_workflows(query=f"", page_size=limit):
        status_str = _STATUS_MAP.get(exec.status, "running")
        summaries.append(
            WorkflowSummary(
                workflow_id=exec.id,
                run_id=exec.run_id,
                workflow_type=exec.workflow_type,
                status=status_str,
                start_time=exec.start_time.timestamp() if exec.start_time else None,
                close_time=exec.close_time.timestamp() if exec.close_time else None,
                task_queue=exec.task_queue or "",
            )
        )
        if len(summaries) >= limit:
            break
    return summaries


async def get_workflow(workflow_id: str) -> WorkflowSummary | None:
    """Fetch a single workflow summary by ID (uses the most recent run)."""
    client = await get_client()
    try:
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        status_str = _STATUS_MAP.get(desc.status, "running")
        return WorkflowSummary(
            workflow_id=desc.id,
            run_id=desc.run_id,
            workflow_type=desc.workflow_type,
            status=status_str,
            start_time=desc.start_time.timestamp() if desc.start_time else None,
            close_time=desc.close_time.timestamp() if desc.close_time else None,
            task_queue=desc.task_queue or "",
        )
    except Exception as exc:
        logger.warning("get_workflow(%s) failed: %s", workflow_id, exc)
        return None


async def get_history(workflow_id: str) -> list[HistoryEvent]:
    """Return the full event history for a workflow execution."""
    client = await get_client()
    handle = client.get_workflow_handle(workflow_id)
    history: WorkflowHistory = await handle.fetch_history()
    return list(history.events)


def parse_activities_from_history(events: list[HistoryEvent]) -> list[dict]:
    """
    Extract activity metadata from history events.

    Returns a list of dicts:
    {
        "activity_id": str,
        "activity_type": str,
        "status": "pending" | "running" | "success" | "failed" | "waiting",
        "scheduled_time": float | None,
        "started_time": float | None,
        "close_time": float | None,
        "attempt": int,
        "failure_message": str | None,
        "is_hitl": bool,  # True if it appears to be waiting on a signal
    }
    """
    # Index events by type for correlation
    scheduled: dict[int, HistoryEvent] = {}
    started: dict[int, HistoryEvent] = {}

    activity_data: dict[str, dict] = {}

    for event in events:
        etype = event.event_type

        if etype == EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED:
            attrs = event.activity_task_scheduled_event_attributes
            activity_id = attrs.activity_id
            scheduled[event.event_id] = event
            activity_data[activity_id] = {
                "activity_id": activity_id,
                "activity_type": attrs.activity_type.name if attrs.activity_type else "",
                "status": "pending",
                "scheduled_time": event.event_time.ToSeconds() if event.event_time else None,
                "started_time": None,
                "close_time": None,
                "attempt": 1,
                "failure_message": None,
                "is_hitl": False,
                "_scheduled_event_id": event.event_id,
            }

        elif etype == EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED:
            attrs = event.activity_task_started_event_attributes
            sched_id = attrs.scheduled_event_id
            started[sched_id] = event
            # Find the activity whose scheduled event id matches
            for aid, data in activity_data.items():
                if data.get("_scheduled_event_id") == sched_id:
                    data["status"] = "running"
                    data["started_time"] = event.event_time.ToSeconds() if event.event_time else None
                    data["attempt"] = attrs.attempt

        elif etype == EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED:
            attrs = event.activity_task_completed_event_attributes
            sched_id = attrs.scheduled_event_id
            for aid, data in activity_data.items():
                if data.get("_scheduled_event_id") == sched_id:
                    data["status"] = "success"
                    data["close_time"] = event.event_time.ToSeconds() if event.event_time else None

        elif etype == EventType.EVENT_TYPE_ACTIVITY_TASK_FAILED:
            attrs = event.activity_task_failed_event_attributes
            sched_id = attrs.scheduled_event_id
            for aid, data in activity_data.items():
                if data.get("_scheduled_event_id") == sched_id:
                    data["status"] = "failed"
                    data["close_time"] = event.event_time.ToSeconds() if event.event_time else None
                    if attrs.failure and attrs.failure.message:
                        data["failure_message"] = attrs.failure.message

        elif etype == EventType.EVENT_TYPE_ACTIVITY_TASK_TIMED_OUT:
            attrs = event.activity_task_timed_out_event_attributes
            sched_id = attrs.scheduled_event_id
            for aid, data in activity_data.items():
                if data.get("_scheduled_event_id") == sched_id:
                    data["status"] = "failed"
                    data["close_time"] = event.event_time.ToSeconds() if event.event_time else None
                    data["failure_message"] = "timed out"

        elif etype == EventType.EVENT_TYPE_ACTIVITY_TASK_CANCELED:
            attrs = event.activity_task_canceled_event_attributes
            sched_id = attrs.scheduled_event_id
            for aid, data in activity_data.items():
                if data.get("_scheduled_event_id") == sched_id:
                    data["status"] = "cancelled"
                    data["close_time"] = event.event_time.ToSeconds() if event.event_time else None

    return list(activity_data.values())


def detect_hitl_signals(events: list[HistoryEvent]) -> set[str]:
    """
    Return a set of activity_ids that are HITL gates — i.e. the workflow
    received a WorkflowExecutionSignaled event whose name contains 'approve',
    'reject', or 'hitl'.
    """
    signal_names: set[str] = set()
    for event in events:
        if event.event_type == EventType.EVENT_TYPE_WORKFLOW_EXECUTION_SIGNALED:
            attrs = event.workflow_execution_signaled_event_attributes
            signal_names.add(attrs.signal_name.lower())
    hitl_keywords = {"approve", "reject", "hitl", "human", "review"}
    return {s for s in signal_names if any(k in s for k in hitl_keywords)}
