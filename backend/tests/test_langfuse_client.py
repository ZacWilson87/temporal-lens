"""Tests for langfuse_client pure functions (no network required)."""
from services.langfuse_client import extract_llm_spans


def _obs(
    obs_id: str = "obs1",
    obs_type: str = "GENERATION",
    name: str = "chat",
    model: str | None = "gpt-4",
    usage: dict | None = None,
    cost: float | None = None,
    start: str | None = "2024-01-01T00:00:00Z",
    end: str | None = "2024-01-01T00:00:01Z",
    level: str | None = "DEFAULT",
) -> dict:
    return {
        "id": obs_id,
        "type": obs_type,
        "name": name,
        "model": model,
        "usage": usage or {},
        "calculatedTotalCost": cost,
        "startTime": start,
        "endTime": end,
        "level": level,
    }


def _trace(
    trace_id: str = "t1",
    name: str = "MyTrace",
    tags: list[str] | None = None,
    observations: list[dict] | None = None,
) -> dict:
    return {
        "id": trace_id,
        "name": name,
        "tags": tags or [],
        "observations": observations or [],
    }


# ---------------------------------------------------------------------------
# Basic cases
# ---------------------------------------------------------------------------

def test_extract_empty():
    assert extract_llm_spans([]) == []


def test_extract_no_observations():
    assert extract_llm_spans([_trace(observations=[])]) == []


def test_extract_skips_non_generation_types():
    trace = _trace(observations=[_obs(obs_type="EVENT")])
    assert extract_llm_spans([trace]) == []


# ---------------------------------------------------------------------------
# Full GENERATION span with activity tags
# ---------------------------------------------------------------------------

def test_extract_generation_with_activity_tags():
    trace = _trace(
        tags=[
            "temporal_workflow_id:wf1",
            "temporal_activity_id:act1",
            "temporal_activity_type:CallLLM",
        ],
        observations=[
            _obs(
                obs_id="obs1",
                model="gpt-4",
                usage={"input": 100, "output": 50, "total": 150},
                cost=0.003,
                start="2024-01-01T00:00:00Z",
                end="2024-01-01T00:00:01Z",
                level="DEFAULT",
            )
        ],
    )
    spans = extract_llm_spans([trace])
    assert len(spans) == 1
    s = spans[0]
    assert s["span_id"] == "obs1"
    assert s["trace_id"] == "t1"
    assert s["activity_id"] == "act1"
    assert s["activity_type"] == "CallLLM"
    assert s["model"] == "gpt-4"
    assert s["prompt_tokens"] == 100
    assert s["completion_tokens"] == 50
    assert s["total_tokens"] == 150
    assert s["cost_usd"] == 0.003
    assert s["latency_ms"] == 1000
    assert s["status"] == "success"


# ---------------------------------------------------------------------------
# Orphan span (no activity tag)
# ---------------------------------------------------------------------------

def test_extract_orphan_span_has_no_activity_id():
    trace = _trace(
        tags=[],
        observations=[_obs(obs_id="obs2", model="claude-3")],
    )
    spans = extract_llm_spans([trace])
    assert len(spans) == 1
    assert spans[0]["activity_id"] is None


# ---------------------------------------------------------------------------
# Status mapping
# ---------------------------------------------------------------------------

def test_extract_status_error():
    trace = _trace(observations=[_obs(level="ERROR")])
    spans = extract_llm_spans([trace])
    assert spans[0]["status"] == "failed"


def test_extract_status_none_defaults_to_success():
    trace = _trace(observations=[_obs(level=None)])
    spans = extract_llm_spans([trace])
    assert spans[0]["status"] == "success"


# ---------------------------------------------------------------------------
# Token field aliases
# ---------------------------------------------------------------------------

def test_extract_prompttokens_alias():
    trace = _trace(
        observations=[
            _obs(usage={"promptTokens": 20, "completionTokens": 10, "totalTokens": 30})
        ]
    )
    spans = extract_llm_spans([trace])
    s = spans[0]
    assert s["prompt_tokens"] == 20
    assert s["completion_tokens"] == 10
    assert s["total_tokens"] == 30


# ---------------------------------------------------------------------------
# Latency edge cases
# ---------------------------------------------------------------------------

def test_extract_no_timestamps():
    trace = _trace(observations=[_obs(start=None, end=None)])
    spans = extract_llm_spans([trace])
    assert spans[0]["latency_ms"] is None


def test_extract_multiple_observations():
    trace = _trace(
        observations=[
            _obs(obs_id="o1"),
            _obs(obs_id="o2", obs_type="SPAN"),
            _obs(obs_id="o3", obs_type="EVENT"),
        ]
    )
    spans = extract_llm_spans([trace])
    assert len(spans) == 2
    ids = {s["span_id"] for s in spans}
    assert ids == {"o1", "o2"}
