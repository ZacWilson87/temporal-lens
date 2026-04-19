"""Tests for temporal_client pure functions (no network required)."""
from dataclasses import dataclass, field
from typing import Any

from temporalio.api.enums.v1 import EventType

from services.temporal_client import parse_activities_from_history, detect_hitl_signals


# ---------------------------------------------------------------------------
# Minimal fake proto types (avoid MagicMock name-attribute quirks)
# ---------------------------------------------------------------------------

class _FakeTimestamp:
    def __init__(self, seconds: float) -> None:
        self._s = seconds

    def ToSeconds(self) -> float:
        return self._s


@dataclass
class _FakeEvent:
    event_type: Any
    event_id: int
    event_time: Any
    activity_task_scheduled_event_attributes: Any = None
    activity_task_started_event_attributes: Any = None
    activity_task_completed_event_attributes: Any = None
    activity_task_failed_event_attributes: Any = None
    activity_task_timed_out_event_attributes: Any = None
    activity_task_canceled_event_attributes: Any = None
    workflow_execution_signaled_event_attributes: Any = None


@dataclass
class _ScheduledAttrs:
    activity_id: str
    activity_type: Any  # needs .name


@dataclass
class _ActivityType:
    name: str


@dataclass
class _StartedAttrs:
    scheduled_event_id: int
    attempt: int


@dataclass
class _CompletedAttrs:
    scheduled_event_id: int


@dataclass
class _FailedAttrs:
    scheduled_event_id: int
    failure: Any


@dataclass
class _Failure:
    message: str


@dataclass
class _TimedOutAttrs:
    scheduled_event_id: int


@dataclass
class _CanceledAttrs:
    scheduled_event_id: int


@dataclass
class _SignaledAttrs:
    signal_name: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(s: float) -> _FakeTimestamp:
    return _FakeTimestamp(s)


def _scheduled(event_id: int, activity_id: str, activity_type: str, t: float) -> _FakeEvent:
    return _FakeEvent(
        event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED,
        event_id=event_id,
        event_time=_ts(t),
        activity_task_scheduled_event_attributes=_ScheduledAttrs(
            activity_id=activity_id,
            activity_type=_ActivityType(name=activity_type),
        ),
    )


def _started(scheduled_event_id: int, attempt: int, t: float) -> _FakeEvent:
    return _FakeEvent(
        event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED,
        event_id=scheduled_event_id + 1,
        event_time=_ts(t),
        activity_task_started_event_attributes=_StartedAttrs(
            scheduled_event_id=scheduled_event_id,
            attempt=attempt,
        ),
    )


def _completed(scheduled_event_id: int, t: float) -> _FakeEvent:
    return _FakeEvent(
        event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED,
        event_id=scheduled_event_id + 2,
        event_time=_ts(t),
        activity_task_completed_event_attributes=_CompletedAttrs(
            scheduled_event_id=scheduled_event_id,
        ),
    )


def _failed(scheduled_event_id: int, t: float, message: str) -> _FakeEvent:
    return _FakeEvent(
        event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_FAILED,
        event_id=scheduled_event_id + 2,
        event_time=_ts(t),
        activity_task_failed_event_attributes=_FailedAttrs(
            scheduled_event_id=scheduled_event_id,
            failure=_Failure(message=message),
        ),
    )


def _timed_out(scheduled_event_id: int, t: float) -> _FakeEvent:
    return _FakeEvent(
        event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_TIMED_OUT,
        event_id=scheduled_event_id + 2,
        event_time=_ts(t),
        activity_task_timed_out_event_attributes=_TimedOutAttrs(
            scheduled_event_id=scheduled_event_id,
        ),
    )


def _canceled(scheduled_event_id: int, t: float) -> _FakeEvent:
    return _FakeEvent(
        event_type=EventType.EVENT_TYPE_ACTIVITY_TASK_CANCELED,
        event_id=scheduled_event_id + 2,
        event_time=_ts(t),
        activity_task_canceled_event_attributes=_CanceledAttrs(
            scheduled_event_id=scheduled_event_id,
        ),
    )


def _signaled(signal_name: str) -> _FakeEvent:
    return _FakeEvent(
        event_type=EventType.EVENT_TYPE_WORKFLOW_EXECUTION_SIGNALED,
        event_id=99,
        event_time=_ts(0),
        workflow_execution_signaled_event_attributes=_SignaledAttrs(
            signal_name=signal_name,
        ),
    )


# ---------------------------------------------------------------------------
# parse_activities_from_history
# ---------------------------------------------------------------------------

def test_parse_empty_history():
    assert parse_activities_from_history([]) == []


def test_parse_scheduled_only():
    events = [_scheduled(1, "act1", "MyActivity", 1000.0)]
    result = parse_activities_from_history(events)
    assert len(result) == 1
    act = result[0]
    assert act["activity_id"] == "act1"
    assert act["activity_type"] == "MyActivity"
    assert act["status"] == "pending"
    assert act["scheduled_time"] == 1000.0
    assert act["started_time"] is None
    assert act["close_time"] is None
    assert act["is_hitl"] is False


def test_parse_completed_activity():
    events = [
        _scheduled(1, "act1", "RunInference", 1000.0),
        _started(1, 1, 1001.0),
        _completed(1, 1005.0),
    ]
    result = parse_activities_from_history(events)
    assert len(result) == 1
    act = result[0]
    assert act["status"] == "success"
    assert act["started_time"] == 1001.0
    assert act["close_time"] == 1005.0
    assert act["attempt"] == 1


def test_parse_failed_activity_with_message():
    events = [
        _scheduled(1, "act1", "FlakyStep", 1000.0),
        _started(1, 2, 1001.0),
        _failed(1, 1003.0, "connection refused"),
    ]
    result = parse_activities_from_history(events)
    assert len(result) == 1
    act = result[0]
    assert act["status"] == "failed"
    assert act["failure_message"] == "connection refused"
    assert act["attempt"] == 2


def test_parse_timed_out_activity():
    events = [
        _scheduled(1, "act1", "SlowStep", 1000.0),
        _started(1, 1, 1001.0),
        _timed_out(1, 1060.0),
    ]
    result = parse_activities_from_history(events)
    act = result[0]
    assert act["status"] == "failed"
    assert act["failure_message"] == "timed out"


def test_parse_canceled_activity():
    events = [
        _scheduled(1, "act1", "CancelableStep", 1000.0),
        _started(1, 1, 1001.0),
        _canceled(1, 1002.0),
    ]
    result = parse_activities_from_history(events)
    act = result[0]
    assert act["status"] == "cancelled"


def test_parse_multiple_activities():
    events = [
        _scheduled(1, "act1", "StepA", 1000.0),
        _scheduled(3, "act2", "StepB", 1002.0),
        _completed(1, 1003.0),
        _started(3, 1, 1003.5),
    ]
    result = parse_activities_from_history(events)
    assert len(result) == 2
    by_id = {r["activity_id"]: r for r in result}
    assert by_id["act1"]["status"] == "success"
    assert by_id["act2"]["status"] == "running"


# ---------------------------------------------------------------------------
# detect_hitl_signals
# ---------------------------------------------------------------------------

def test_detect_hitl_empty():
    assert detect_hitl_signals([]) == set()


def test_detect_hitl_no_signals():
    events = [_scheduled(1, "act1", "A", 0.0)]
    assert detect_hitl_signals(events) == set()


def test_detect_hitl_approve_signal():
    events = [_signaled("approve-request")]
    result = detect_hitl_signals(events)
    assert "approve-request" in result


def test_detect_hitl_reject_signal():
    events = [_signaled("human-reject")]
    result = detect_hitl_signals(events)
    assert "human-reject" in result


def test_detect_hitl_non_matching_signal():
    events = [_signaled("update-config")]
    assert detect_hitl_signals(events) == set()


def test_detect_hitl_mixed_signals():
    events = [_signaled("approve-order"), _signaled("system-tick")]
    result = detect_hitl_signals(events)
    assert "approve-order" in result
    assert "system-tick" not in result
