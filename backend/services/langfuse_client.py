"""Langfuse SDK wrapper — fetch traces filtered by workflow_id tag."""
from __future__ import annotations

import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Terminal Langfuse observation statuses we map to our vocabulary
_STATUS_MAP = {
    "SUCCESS": "success",
    "ERROR": "failed",
    "DEFAULT": "success",
    None: "success",
}


async def is_connected() -> bool:
    """Return True if Langfuse is reachable and credentials are valid."""
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.langfuse_host}/api/public/health",
                auth=(settings.langfuse_public_key, settings.langfuse_secret_key),
            )
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("Langfuse health check failed: %s", exc)
        return False


async def get_traces_for_workflow(workflow_id: str) -> list[dict]:
    """
    Fetch Langfuse traces tagged with temporal_workflow_id=<workflow_id>.
    Returns a list of raw trace dicts (id, name, tags, observations).
    """
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.langfuse_host}/api/public/traces",
                params={"tags": f"temporal_workflow_id:{workflow_id}", "limit": 100},
                auth=(settings.langfuse_public_key, settings.langfuse_secret_key),
            )
            if resp.status_code != 200:
                logger.warning(
                    "Langfuse traces request returned %d: %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return []
            data = resp.json()
            traces = data.get("data", [])
            # Enrich each trace with its observations (spans/generations)
            enriched = []
            for trace in traces:
                obs = await _get_observations(client, trace["id"])
                trace["observations"] = obs
                enriched.append(trace)
            return enriched
    except Exception as exc:
        logger.warning("get_traces_for_workflow(%s) failed: %s", workflow_id, exc)
        return []


async def _get_observations(client: httpx.AsyncClient, trace_id: str) -> list[dict]:
    """Fetch all observations (spans/generations) for a single trace."""
    try:
        resp = await client.get(
            f"{settings.langfuse_host}/api/public/observations",
            params={"traceId": trace_id, "limit": 100},
            auth=(settings.langfuse_public_key, settings.langfuse_secret_key),
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("data", [])
    except Exception:
        return []


def extract_llm_spans(traces: list[dict]) -> list[dict]:
    """
    Convert Langfuse trace observations into our LLM span dicts.

    Returns a list of:
    {
        "span_id": str,
        "trace_id": str,
        "activity_id": str | None,   # from temporal_activity_id tag
        "activity_type": str | None,
        "name": str,
        "status": str,
        "model": str | None,
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int,
        "cost_usd": float | None,
        "latency_ms": int | None,
        "start_time": float | None,
        "end_time": float | None,
    }
    """
    spans: list[dict] = []

    for trace in traces:
        # Extract temporal_activity_id from trace tags
        tags: dict = {}
        raw_tags = trace.get("tags") or []
        for tag in raw_tags:
            if ":" in tag:
                k, v = tag.split(":", 1)
                tags[k] = v

        activity_id = tags.get("temporal_activity_id")
        activity_type = tags.get("temporal_activity_type")

        for obs in trace.get("observations", []):
            if obs.get("type") not in ("GENERATION", "SPAN"):
                continue

            usage = obs.get("usage") or {}
            model = obs.get("model") or (obs.get("input") or {}).get("model")

            # Calculate latency
            latency_ms = None
            if obs.get("startTime") and obs.get("endTime"):
                from datetime import datetime
                try:
                    start = datetime.fromisoformat(obs["startTime"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(obs["endTime"].replace("Z", "+00:00"))
                    latency_ms = int((end - start).total_seconds() * 1000)
                except Exception:
                    pass

            # Parse timestamps
            start_ts = None
            end_ts = None
            try:
                from datetime import datetime
                if obs.get("startTime"):
                    start_ts = datetime.fromisoformat(
                        obs["startTime"].replace("Z", "+00:00")
                    ).timestamp()
                if obs.get("endTime"):
                    end_ts = datetime.fromisoformat(
                        obs["endTime"].replace("Z", "+00:00")
                    ).timestamp()
            except Exception:
                pass

            status_raw = obs.get("level") or obs.get("statusMessage")
            status = _STATUS_MAP.get(status_raw, "success")

            spans.append(
                {
                    "span_id": obs.get("id", ""),
                    "trace_id": trace.get("id", ""),
                    "activity_id": activity_id,
                    "activity_type": activity_type,
                    "name": obs.get("name") or trace.get("name") or "llm-call",
                    "status": status,
                    "model": model,
                    "prompt_tokens": usage.get("input") or usage.get("promptTokens") or 0,
                    "completion_tokens": usage.get("output") or usage.get("completionTokens") or 0,
                    "total_tokens": usage.get("total") or usage.get("totalTokens") or 0,
                    "cost_usd": obs.get("calculatedTotalCost"),
                    "latency_ms": latency_ms,
                    "start_time": start_ts,
                    "end_time": end_ts,
                }
            )

    return spans
