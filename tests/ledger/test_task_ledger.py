from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.task_ledger import TaskLedger


def event(event_id: str, event_type: str, idempotency_key: str):
    return {
        "event_id": event_id,
        "task_id": "task-1",
        "run_id": "run-1",
        "parent_run_id": None,
        "step_id": None,
        "type": event_type,
        "ts": "2026-03-11T03:30:00Z",
        "payload": {},
        "idempotency_key": idempotency_key,
    }


def test_append_and_read_events(tmp_path):
    ledger = TaskLedger(tmp_path)
    result = ledger.append_event(event("e1", "task_created", "k1"))
    assert result.written is True
    events = ledger.read_events("task-1", "run-1")
    assert [e["event_id"] for e in events] == ["e1"]


def test_idempotency_key_prevents_duplicate_append(tmp_path):
    ledger = TaskLedger(tmp_path)
    first = ledger.append_event(event("e1", "task_created", "same-key"))
    second = ledger.append_event(event("e2", "task_created", "same-key"))
    assert first.written is True
    assert second.written is False
    assert second.reason == "duplicate_idempotency_key"
    events = ledger.read_events("task-1", "run-1")
    assert len(events) == 1
    assert events[0]["event_id"] == "e1"


def test_list_runs_from_ledger(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event("e1", "task_created", "k1"))
    runs = ledger.list_runs()
    assert runs == [{
        "task_id": "task-1",
        "run_id": "run-1",
        "path": str(ledger.ledger_path("task-1", "run-1")),
    }]
