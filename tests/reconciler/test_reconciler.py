import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "runtime" / "recovery-orchestrator") not in sys.path:
    sys.path.insert(0, str(ROOT / "runtime" / "recovery-orchestrator"))

from core.task_ledger import TaskLedger
from core.reconciler import Reconciler


def event(task_id, run_id, event_id, event_type, ts, *, step_id=None, payload=None, key=None):
    return {
        "event_id": event_id,
        "task_id": task_id,
        "run_id": run_id,
        "parent_run_id": None,
        "step_id": step_id,
        "type": event_type,
        "ts": ts,
        "payload": payload or {},
        "idempotency_key": key or f"{task_id}-{run_id}-{event_id}",
    }


def test_reconciler_applies_resume_decision(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event("task-r", "run-r1", "e1", "task_created", "2026-03-11T10:00:00Z"))
    ledger.append_event(event("task-r", "run-r1", "e2", "run_started", "2026-03-11T10:00:01Z"))
    ledger.append_event(event("task-r", "run-r1", "e3", "step_started", "2026-03-11T10:00:02Z", step_id="step-1"))

    applied = Reconciler(tmp_path).scan_and_apply()
    assert len(applied) == 1
    assert applied[0].action == "resume"
    assert applied[0].event_type == "recovery_hook_triggered"

    events = ledger.read_events("task-r", "run-r1")
    assert events[-1]["type"] == "recovery_hook_triggered"
    assert events[-1]["payload"]["action"] == "resume"


def test_reconciler_applies_retry_decision(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event("task-r", "run-r2", "e1", "task_created", "2026-03-11T10:01:00Z"))
    ledger.append_event(event("task-r", "run-r2", "e2", "run_started", "2026-03-11T10:01:01Z"))
    ledger.append_event(event("task-r", "run-r2", "e3", "step_started", "2026-03-11T10:01:02Z", step_id="step-2"))
    ledger.append_event(event("task-r", "run-r2", "e4", "step_failed", "2026-03-11T10:01:03Z", step_id="step-2", payload={"fault_code": "STEP_FAILED"}))
    ledger.append_event(event("task-r", "run-r2", "e5", "retry_scheduled", "2026-03-11T10:01:04Z"))

    applied = Reconciler(tmp_path).scan_and_apply()
    assert len(applied) == 1
    assert applied[0].action == "retry"
    assert applied[0].event_type == "retry_scheduled"

    events = ledger.read_events("task-r", "run-r2")
    retry_events = [e for e in events if e["type"] == "retry_scheduled"]
    assert len(retry_events) == 2
    assert retry_events[-1]["payload"]["action"] == "retry"


def test_reconciler_requeues_missing_child_exactly_once(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event("task-r", "run-rx", "e1", "task_created", "2026-03-11T10:03:00Z"))
    ledger.append_event(event("task-r", "run-rx", "e2", "run_started", "2026-03-11T10:03:01Z"))
    ledger.append_event(event("task-r", "run-rx", "e3", "child_registered", "2026-03-11T10:03:02Z", payload={"child_run_id": "child-1"}))
    ledger.append_event(event("task-r", "run-rx", "e4", "child_missing_detected", "2026-03-11T10:03:03Z", payload={"child_run_id": "child-1"}))

    first = Reconciler(tmp_path).scan_and_apply()
    second = Reconciler(tmp_path).scan_and_apply()

    assert any(a.event_type == "job_submitted" for a in first)
    events = ledger.read_events("task-r", "run-rx")
    requeues = [e for e in events if e["type"] == "job_submitted" and e["payload"].get("requeued") is True]
    assert len(requeues) == 1
    assert any(a.status == "duplicate" for a in second if a.event_type == "job_submitted")


def test_recovery_apply_cli_outputs_applied_actions(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event("task-r", "run-r3", "e1", "task_created", "2026-03-11T10:02:00Z"))
    ledger.append_event(event("task-r", "run-r3", "e2", "run_started", "2026-03-11T10:02:01Z"))
    ledger.append_event(event("task-r", "run-r3", "e3", "step_started", "2026-03-11T10:02:02Z", step_id="step-1"))

    proc = subprocess.run(
        [sys.executable, str(ROOT / "runtime" / "recovery-orchestrator" / "recovery_apply.py"), "--root", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    assert data["status"] == "ok"
    assert data["applied_count"] == 1
    assert data["applied"][0]["action"] == "resume"
