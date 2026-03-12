from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'runtime' / 'recovery-orchestrator'))

from core.task_ledger import TaskLedger
from recovery_orchestrator import RecoveryOrchestrator


def event(task_id, run_id, event_id, event_type, ts, *, step_id=None, payload=None, key=None):
    return {
        'event_id': event_id,
        'task_id': task_id,
        'run_id': run_id,
        'parent_run_id': None,
        'step_id': step_id,
        'type': event_type,
        'ts': ts,
        'payload': payload or {},
        'idempotency_key': key or f'{task_id}-{run_id}-{event_id}',
    }


def test_scan_returns_resume_for_eligible_run(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event('task-a', 'run-1', 'e1', 'task_created', '2026-03-11T03:00:00Z'))
    ledger.append_event(event('task-a', 'run-1', 'e2', 'run_started', '2026-03-11T03:00:01Z'))
    ledger.append_event(event('task-a', 'run-1', 'e3', 'step_started', '2026-03-11T03:00:02Z', step_id='step-1'))

    decisions = RecoveryOrchestrator(tmp_path).scan()
    assert len(decisions) == 1
    assert decisions[0].action == 'resume'
    assert decisions[0].reason == 'resume_current_step'


def test_scan_returns_retry_for_retryable_run(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event('task-b', 'run-2', 'e1', 'task_created', '2026-03-11T03:00:00Z'))
    ledger.append_event(event('task-b', 'run-2', 'e2', 'run_started', '2026-03-11T03:00:01Z'))
    ledger.append_event(event('task-b', 'run-2', 'e3', 'step_started', '2026-03-11T03:00:02Z', step_id='step-1'))
    ledger.append_event(event('task-b', 'run-2', 'e4', 'step_failed', '2026-03-11T03:00:03Z', step_id='step-1', payload={'fault_code': 'STEP_FAILED'}))
    ledger.append_event(event('task-b', 'run-2', 'e5', 'retry_scheduled', '2026-03-11T03:00:04Z'))

    decisions = RecoveryOrchestrator(tmp_path).scan()
    assert decisions[0].action == 'retry'
    assert decisions[0].reason == 'step_failed_with_retry_budget_remaining'


def test_scan_returns_repair_for_missing_child(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event('task-c', 'run-3', 'e1', 'task_created', '2026-03-11T03:00:00Z'))
    ledger.append_event(event('task-c', 'run-3', 'e2', 'run_started', '2026-03-11T03:00:01Z'))
    ledger.append_event(event('task-c', 'run-3', 'e3', 'child_registered', '2026-03-11T03:00:02Z', payload={'child_run_id': 'child-1'}))
    ledger.append_event(event('task-c', 'run-3', 'e4', 'child_missing_detected', '2026-03-11T03:00:03Z', payload={'child_run_id': 'child-1'}))

    decisions = RecoveryOrchestrator(tmp_path).scan()
    assert decisions[0].action == 'repair'
    assert decisions[0].reason == 'missing_or_unreconciled_child_jobs'
    assert decisions[0].pending_children == ['child-1']


def test_scan_returns_none_for_completed_run(tmp_path):
    ledger = TaskLedger(tmp_path)
    ledger.append_event(event('task-d', 'run-4', 'e1', 'task_created', '2026-03-11T03:00:00Z'))
    ledger.append_event(event('task-d', 'run-4', 'e2', 'run_started', '2026-03-11T03:00:01Z'))
    ledger.append_event(event('task-d', 'run-4', 'e3', 'run_completed', '2026-03-11T03:00:02Z'))

    decisions = RecoveryOrchestrator(tmp_path).scan()
    assert decisions[0].action == 'none'
    assert decisions[0].reason == 'run_already_completed'
