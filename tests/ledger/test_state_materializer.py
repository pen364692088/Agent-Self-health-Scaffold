from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.state_materializer import RunStateMaterializer


def build(event_type, ts, **extra):
    base = {
        "event_id": f"evt-{event_type}-{ts}",
        "task_id": "task-1",
        "run_id": "run-1",
        "parent_run_id": None,
        "step_id": extra.pop("step_id", None),
        "type": event_type,
        "ts": ts,
        "payload": extra.pop("payload", {}),
        "idempotency_key": f"key-{event_type}-{ts}",
    }
    base.update(extra)
    return base


def test_materialize_happy_path_completion():
    materializer = RunStateMaterializer()
    state = materializer.materialize([
        build("task_created", "2026-03-11T03:00:00Z"),
        build("run_started", "2026-03-11T03:00:01Z"),
        build("step_started", "2026-03-11T03:00:02Z", step_id="step-a"),
        build("step_succeeded", "2026-03-11T03:00:03Z", step_id="step-a"),
        build("run_completed", "2026-03-11T03:00:04Z"),
    ])
    assert state.status == "completed"
    assert state.last_good_step == "step-a"
    assert state.current_step is None
    assert state.recovery_status == "abandoned"


def test_materialize_retryable_failed_step():
    materializer = RunStateMaterializer()
    state = materializer.materialize([
        build("task_created", "2026-03-11T03:00:00Z"),
        build("run_started", "2026-03-11T03:00:01Z"),
        build("step_started", "2026-03-11T03:00:02Z", step_id="step-a"),
        build("step_failed", "2026-03-11T03:00:03Z", step_id="step-a", payload={"fault_code": "STEP_FAILED"}),
        build("retry_scheduled", "2026-03-11T03:00:04Z"),
    ])
    assert state.status == "running"
    assert state.current_step == "step-a"
    assert state.retry_count == 1
    assert state.recovery_status == "retryable"


def test_materialize_needs_repair_for_missing_child():
    materializer = RunStateMaterializer()
    state = materializer.materialize([
        build("task_created", "2026-03-11T03:00:00Z"),
        build("run_started", "2026-03-11T03:00:01Z"),
        build("child_registered", "2026-03-11T03:00:02Z", payload={"child_run_id": "child-1"}),
        build("child_missing_detected", "2026-03-11T03:00:03Z", payload={"child_run_id": "child-1"}),
    ])
    assert state.pending_children == ["child-1"]
    assert state.recovery_status == "needs_repair"


def test_materialize_blocked_after_gate_failure():
    materializer = RunStateMaterializer()
    state = materializer.materialize([
        build("task_created", "2026-03-11T03:00:00Z"),
        build("run_started", "2026-03-11T03:00:01Z"),
        build("gate_failed", "2026-03-11T03:00:02Z", payload={"fault_code": "GATE_FAILED"}),
    ])
    assert state.status == "blocked"
    assert state.recovery_status == "blocked"
