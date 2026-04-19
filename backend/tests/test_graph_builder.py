"""Tests for graph_builder pure functions (no network required)."""
from services.graph_builder import _map_status, is_terminal
from models.graph import GraphSnapshot


def _snapshot(status: str) -> GraphSnapshot:
    return GraphSnapshot(
        workflow_id="wf1",
        workflow_name="MyWorkflow",
        status=status,
        nodes=[],
        edges=[],
        snapshot_at=0.0,
    )


# ---------------------------------------------------------------------------
# _map_status
# ---------------------------------------------------------------------------

def test_map_status_running():
    assert _map_status("running") == "running"


def test_map_status_completed_to_success():
    assert _map_status("completed") == "success"


def test_map_status_success_passthrough():
    assert _map_status("success") == "success"


def test_map_status_failed():
    assert _map_status("failed") == "failed"
    assert _map_status("error") == "failed"
    assert _map_status("timed_out") == "failed"


def test_map_status_cancelled_variants():
    assert _map_status("cancelled") == "cancelled"
    assert _map_status("canceled") == "cancelled"
    assert _map_status("terminated") == "cancelled"


def test_map_status_pending_variants():
    assert _map_status("pending") == "pending"
    assert _map_status("scheduled") == "pending"


def test_map_status_waiting():
    assert _map_status("waiting") == "waiting"


def test_map_status_none_returns_pending():
    assert _map_status(None) == "pending"


def test_map_status_unknown_returns_pending():
    assert _map_status("some_unknown_value") == "pending"


def test_map_status_case_insensitive():
    assert _map_status("RUNNING") == "running"
    assert _map_status("Completed") == "success"


# ---------------------------------------------------------------------------
# is_terminal
# ---------------------------------------------------------------------------

def test_is_terminal_completed():
    assert is_terminal(_snapshot("completed"))


def test_is_terminal_failed():
    assert is_terminal(_snapshot("failed"))


def test_is_terminal_cancelled():
    assert is_terminal(_snapshot("cancelled"))


def test_is_terminal_terminated():
    assert is_terminal(_snapshot("terminated"))


def test_is_terminal_timed_out():
    assert is_terminal(_snapshot("timed_out"))


def test_is_not_terminal_running():
    assert not is_terminal(_snapshot("running"))


def test_is_not_terminal_pending():
    assert not is_terminal(_snapshot("pending"))
