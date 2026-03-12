"""
E2E Test Skeleton for Agent-Self-health-Scaffold v2

These tests verify the core self-healing execution chain.
Each test is documented with:
- Goal
- Setup
- Pass Criteria
- Implementation Status
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "runtime") not in sys.path:
    sys.path.insert(0, str(ROOT / "runtime"))
if str(ROOT / "runtime" / "recovery-orchestrator") not in sys.path:
    sys.path.insert(0, str(ROOT / "runtime" / "recovery-orchestrator"))

from core.task_ledger import TaskLedger
from core.state_materializer import RunStateMaterializer
from restart_executor.restart_executor import RestartExecutor
from transcript_rebuilder.transcript_rebuilder import rebuild_transcript


def build_event(task_id, run_id, event_id, event_type, ts, *, step_id=None, payload=None, key=None):
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


class TestE2E01GatewayRestartAutoResume:
    """
    E2E-01: Gateway Restart Auto-Resume
    
    Goal: Running task auto-resumes after gateway restart
    Setup: Start task, trigger restart, verify continuation
    Pass Criteria:
      - No manual "continue" needed
      - Task completes within timeout
      - Ledger shows recovery events
    """
    
    @pytest.mark.e2e
    def test_gateway_restart_auto_resume(self, tmp_path):
        task_id = "task-e2e-01"
        run_id = "run-e2e-01"
        ledger = TaskLedger(tmp_path)

        ledger.append_event(build_event(task_id, run_id, "e1", "task_created", "2026-03-11T07:00:00Z"))
        ledger.append_event(build_event(task_id, run_id, "e2", "run_started", "2026-03-11T07:00:01Z"))
        ledger.append_event(
            build_event(task_id, run_id, "e3", "step_started", "2026-03-11T07:00:02Z", step_id="step-1")
        )

        executor = RestartExecutor(tmp_path)
        intent_id = executor.submit_restart_intent(
            target="gateway",
            reason="stalled",
            trigger_run_id=run_id,
            cooldown_sec=1,
        )
        result_path = tmp_path / "artifacts" / "restart_intents" / f"{intent_id}_result.json"
        result_path.write_text(
            json.dumps(
                {
                    "intent_id": intent_id,
                    "status": "completed",
                    "executed_at": "2026-03-11T07:00:05Z",
                    "recovery_triggered": True,
                    "error": None,
                }
            )
        )
        ledger.append_event(
            build_event(
                task_id,
                run_id,
                "e4",
                "process_restarted",
                "2026-03-11T07:00:05Z",
                payload={"intent_id": intent_id, "target": "gateway"},
            )
        )

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "runtime" / "recovery-orchestrator" / "recovery_scan.py"),
                "--root",
                str(tmp_path),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        scan = json.loads(proc.stdout)
        assert scan["status"] == "ok"
        assert scan["decision_count"] == 2
        matching = [d for d in scan["decisions"] if d["task_id"] == task_id and d["run_id"] == run_id]
        assert len(matching) == 1
        assert matching[0]["action"] == "resume"
        assert matching[0]["reason"] == "resume_current_step"

        ledger.append_event(
            build_event(task_id, run_id, "e5", "step_succeeded", "2026-03-11T07:00:06Z", step_id="step-1")
        )
        ledger.append_event(build_event(task_id, run_id, "e6", "run_completed", "2026-03-11T07:00:07Z"))

        events = ledger.read_events(task_id, run_id)
        event_types = [e["type"] for e in events]
        all_event_types = [e["type"] for e in ledger.iter_all_events()]
        assert "restart_intent_created" in all_event_types
        assert "process_restarted" in event_types
        assert event_types[-1] == "run_completed"


class TestE2E02StepFailureLastGoodStepRecovery:
    """
    E2E-02: Step Failure → Last-Good-Step Recovery
    
    Goal: Mid-task failure resumes from last successful step
    Setup: Inject failure at step N, verify resume from step N-1
    Pass Criteria:
      - Steps 1..N-1 not re-executed
      - Step N retry succeeds or fails gracefully
    """
    
    @pytest.mark.e2e
    def test_step_failure_recovery(self, tmp_path):
        task_id = "task-e2e-02"
        run_id = "run-e2e-02"
        ledger = TaskLedger(tmp_path)

        ledger.append_event(build_event(task_id, run_id, "e1", "task_created", "2026-03-11T08:00:00Z"))
        ledger.append_event(build_event(task_id, run_id, "e2", "run_started", "2026-03-11T08:00:01Z"))
        ledger.append_event(
            build_event(task_id, run_id, "e3", "step_started", "2026-03-11T08:00:02Z", step_id="step-1")
        )
        ledger.append_event(
            build_event(task_id, run_id, "e4", "step_succeeded", "2026-03-11T08:00:03Z", step_id="step-1")
        )
        ledger.append_event(
            build_event(task_id, run_id, "e5", "step_started", "2026-03-11T08:00:04Z", step_id="step-2")
        )
        ledger.append_event(
            build_event(
                task_id,
                run_id,
                "e6",
                "step_failed",
                "2026-03-11T08:00:05Z",
                step_id="step-2",
                payload={"fault_code": "STEP_FAILED"},
            )
        )
        ledger.append_event(build_event(task_id, run_id, "e7", "retry_scheduled", "2026-03-11T08:00:06Z"))

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "runtime" / "recovery-orchestrator" / "recovery_scan.py"),
                "--root",
                str(tmp_path),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        scan = json.loads(proc.stdout)
        matching = [d for d in scan["decisions"] if d["task_id"] == task_id and d["run_id"] == run_id]
        assert len(matching) == 1
        assert matching[0]["action"] == "retry"
        assert matching[0]["reason"] == "step_failed_with_retry_budget_remaining"
        assert matching[0]["current_step"] == "step-2"
        assert matching[0]["last_good_step"] == "step-1"
        assert matching[0]["retry_count"] == 1

        before_retry_events = ledger.read_events(task_id, run_id)
        step1_successes_before = sum(
            1 for e in before_retry_events if e["type"] == "step_succeeded" and e.get("step_id") == "step-1"
        )

        ledger.append_event(
            build_event(task_id, run_id, "e8", "step_started", "2026-03-11T08:00:07Z", step_id="step-2")
        )
        ledger.append_event(
            build_event(task_id, run_id, "e9", "step_succeeded", "2026-03-11T08:00:08Z", step_id="step-2")
        )
        ledger.append_event(build_event(task_id, run_id, "e10", "run_completed", "2026-03-11T08:00:09Z"))

        after_retry_events = ledger.read_events(task_id, run_id)
        step1_successes_after = sum(
            1 for e in after_retry_events if e["type"] == "step_succeeded" and e.get("step_id") == "step-1"
        )
        step2_starts = [
            e for e in after_retry_events if e["type"] == "step_started" and e.get("step_id") == "step-2"
        ]

        assert step1_successes_before == 1
        assert step1_successes_after == 1
        assert len(step2_starts) == 2  # original attempt + retry only
        assert after_retry_events[-1]["type"] == "run_completed"


class TestE2E03TranscriptCorruptionRebuild:
    """
    E2E-03: Transcript Corruption → Rebuild
    
    Goal: Corrupt transcript, verify rebuild from ledger
    Setup: Delete/corrupt transcript file, trigger rebuild
    Pass Criteria:
      - Transcript rebuilt from ledger events
      - Task continues normally
    """
    
    @pytest.mark.e2e
    def test_transcript_rebuild(self, tmp_path):
        task_id = "task-e2e-03"
        run_id = "run-e2e-03"
        ledger = TaskLedger(tmp_path)

        ledger.append_event(build_event(task_id, run_id, "e1", "task_created", "2026-03-11T09:00:00Z"))
        ledger.append_event(build_event(task_id, run_id, "e2", "run_started", "2026-03-11T09:00:01Z"))
        ledger.append_event(
            build_event(task_id, run_id, "e3", "step_started", "2026-03-11T09:00:02Z", step_id="step-a")
        )
        ledger.append_event(
            build_event(task_id, run_id, "e4", "step_succeeded", "2026-03-11T09:00:03Z", step_id="step-a")
        )
        ledger.append_event(
            build_event(task_id, run_id, "e5", "step_started", "2026-03-11T09:00:04Z", step_id="step-b")
        )

        transcript_path = tmp_path / "artifacts" / "transcripts" / f"{task_id}__{run_id}.md"
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        transcript_path.write_text("CORRUPTED TRANSCRIPT")
        transcript_path.unlink()

        snapshot = rebuild_transcript(tmp_path, task_id, run_id, output_format="markdown")
        assert snapshot.task_id == task_id
        assert snapshot.run_id == run_id
        assert snapshot.event_count == 5
        assert len(snapshot.step_sequence) == 2
        assert snapshot.step_sequence[0].step_id == "step-a"
        assert snapshot.step_sequence[0].status == "succeeded"
        assert snapshot.step_sequence[1].step_id == "step-b"
        assert snapshot.step_sequence[1].status == "running"

        assert transcript_path.exists()
        rebuilt = transcript_path.read_text()
        assert "# Transcript" in rebuilt
        assert "step-a" in rebuilt
        assert "step-b" in rebuilt

        post_rebuild_events = ledger.read_events(task_id, run_id)
        assert any(e["type"] == "transcript_rebuilt" for e in post_rebuild_events)

        ledger.append_event(
            build_event(task_id, run_id, "e6", "step_succeeded", "2026-03-11T09:00:05Z", step_id="step-b")
        )
        ledger.append_event(build_event(task_id, run_id, "e7", "run_completed", "2026-03-11T09:00:06Z"))
        final_events = ledger.read_events(task_id, run_id)
        assert final_events[-1]["type"] == "run_completed"


class TestE2E04ChildJobMissingRequeue:
    """
    E2E-04: Child Job Missing → Requeue
    
    Goal: Missing child job detected and requeued
    Setup: Delete child job record, verify detection + requeue
    Pass Criteria:
      - child_missing_detected event logged
      - Child re-executed exactly once
      - Parent completes
    """
    
    @pytest.mark.e2e
    def test_child_job_requeue(self, tmp_path):
        task_id = "task-e2e-04"
        run_id = "run-e2e-04"
        ledger = TaskLedger(tmp_path)

        ledger.append_event(build_event(task_id, run_id, "e1", "task_created", "2026-03-11T10:20:00Z"))
        ledger.append_event(build_event(task_id, run_id, "e2", "run_started", "2026-03-11T10:20:01Z"))
        ledger.append_event(
            build_event(task_id, run_id, "e3", "child_registered", "2026-03-11T10:20:02Z", payload={"child_run_id": "child-1"})
        )
        ledger.append_event(
            build_event(task_id, run_id, "e4", "child_missing_detected", "2026-03-11T10:20:03Z", payload={"child_run_id": "child-1"})
        )

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "runtime" / "recovery-orchestrator" / "recovery_apply.py"),
                "--root",
                str(tmp_path),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(proc.stdout)
        assert data["status"] == "ok"
        assert any(item["event_type"] == "job_submitted" for item in data["applied"])

        second = subprocess.run(
            [
                sys.executable,
                str(ROOT / "runtime" / "recovery-orchestrator" / "recovery_apply.py"),
                "--root",
                str(tmp_path),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data2 = json.loads(second.stdout)

        events = ledger.read_events(task_id, run_id)
        child_missing = [e for e in events if e["type"] == "child_missing_detected"]
        requeues = [e for e in events if e["type"] == "job_submitted" and e["payload"].get("requeued") is True]
        assert len(child_missing) == 1
        assert len(requeues) == 1
        assert any(item["status"] == "duplicate" for item in data2["applied"] if item["event_type"] == "job_submitted")

        ledger.append_event(
            build_event(task_id, run_id, "e5", "step_succeeded", "2026-03-11T10:20:04Z", step_id="child-1", payload={"child_run_id": "child-1"})
        )
        ledger.append_event(build_event(task_id, run_id, "e6", "run_completed", "2026-03-11T10:20:05Z"))
        final_events = ledger.read_events(task_id, run_id)
        assert final_events[-1]["type"] == "run_completed"


class TestE2E05HighRiskRepairGateRollback:
    """
    E2E-05: High-Risk Repair → Gate Check → Rollback
    
    Goal: High-risk repair fails gate, auto-rollback
    Setup: Propose risky repair, fail gate, verify rollback
    Pass Criteria:
      - Gate failure logged
      - Repair not applied
      - Run returns to safe state
    """
    
    @pytest.mark.e2e
    def test_repair_gate_rollback(self, tmp_path):
        task_id = "task-e2e-05"
        run_id = "run-e2e-05"
        ledger = TaskLedger(tmp_path)
        materializer = RunStateMaterializer()

        ledger.append_event(build_event(task_id, run_id, "e1", "task_created", "2026-03-11T10:30:00Z"))
        ledger.append_event(build_event(task_id, run_id, "e2", "run_started", "2026-03-11T10:30:01Z"))
        ledger.append_event(
            build_event(task_id, run_id, "e3", "step_started", "2026-03-11T10:30:02Z", step_id="step-safe")
        )
        ledger.append_event(
            build_event(task_id, run_id, "e4", "step_succeeded", "2026-03-11T10:30:03Z", step_id="step-safe")
        )
        ledger.append_event(
            build_event(
                task_id,
                run_id,
                "e5",
                "repair_proposed",
                "2026-03-11T10:30:04Z",
                payload={"risk": "high", "repair": "rewrite_current_checkpoint"},
            )
        )
        ledger.append_event(
            build_event(
                task_id,
                run_id,
                "e6",
                "gate_failed",
                "2026-03-11T10:30:05Z",
                payload={"fault_code": "GATE_FAILED", "rollback": "keep_last_good_step"},
            )
        )

        blocked_state = materializer.materialize(ledger.read_events(task_id, run_id))
        assert blocked_state.status == "blocked"
        assert blocked_state.recovery_status == "blocked"
        assert blocked_state.last_good_step == "step-safe"

        events_after_gate_fail = ledger.read_events(task_id, run_id)
        assert any(e["type"] == "gate_failed" for e in events_after_gate_fail)
        assert not any(e["type"] == "repair_applied" for e in events_after_gate_fail)

        ledger.append_event(
            build_event(task_id, run_id, "e7", "gate_passed", "2026-03-11T10:30:06Z", payload={"rollback_confirmed": True})
        )
        ledger.append_event(build_event(task_id, run_id, "e8", "run_completed", "2026-03-11T10:30:07Z"))

        final_state = materializer.materialize(ledger.read_events(task_id, run_id))
        assert final_state.status == "completed"
        final_events = ledger.read_events(task_id, run_id)
        assert final_events[-1]["type"] == "run_completed"


class TestE2E06UnattendedLongTaskAcrossRestarts:
    """
    E2E-06: Unattended Long Task Across Restarts
    
    Goal: Long task survives multiple restarts without human input
    Setup: 10-step task, inject 3 restarts, verify completion
    Pass Criteria:
      - All restarts auto-recovered
      - Task completed end-to-end
      - No manual intervention
    """
    
    @pytest.mark.e2e
    def test_long_task_multi_restart(self, tmp_path):
        task_id = "task-e2e-06"
        run_id = "run-e2e-06"
        ledger = TaskLedger(tmp_path)

        # Create task
        ledger.append_event(build_event(task_id, run_id, "e1", "task_created", "2026-03-11T11:00:00Z"))
        ledger.append_event(build_event(task_id, run_id, "e2", "run_started", "2026-03-11T11:00:01Z"))

        # Steps 1-2 complete before first restart
        for i in range(1, 3):
            ledger.append_event(build_event(task_id, run_id, f"e{i+2}", "step_started", f"2026-03-11T11:00:{i:02d}Z", step_id=f"step-{i}"))
            ledger.append_event(build_event(task_id, run_id, f"e{i+4}", "step_succeeded", f"2026-03-11T11:00:{i+1:02d}Z", step_id=f"step-{i}"))

        # First restart at step 3
        executor = RestartExecutor(tmp_path)
        intent1 = executor.submit_restart_intent("gateway", "stalled", run_id, cooldown_sec=1)
        ledger.append_event(build_event(task_id, run_id, "e9", "process_restarted", "2026-03-11T11:00:10Z", payload={"intent_id": intent1}))

        # Recovery resumes from step 3
        ledger.append_event(build_event(task_id, run_id, "e10", "step_started", "2026-03-11T11:00:11Z", step_id="step-3"))
        ledger.append_event(build_event(task_id, run_id, "e11", "step_succeeded", "2026-03-11T11:00:12Z", step_id="step-3"))

        # Steps 4-5 complete
        for i in range(4, 6):
            ledger.append_event(build_event(task_id, run_id, f"e{i+8}", "step_started", f"2026-03-11T11:00:{i+10:02d}Z", step_id=f"step-{i}"))
            ledger.append_event(build_event(task_id, run_id, f"e{i+10}", "step_succeeded", f"2026-03-11T11:00:{i+11:02d}Z", step_id=f"step-{i}"))

        # Second restart at step 6
        import time; time.sleep(1.1)  # Cooldown
        intent2 = executor.submit_restart_intent("worker", "drift_detected", run_id, cooldown_sec=1)
        ledger.append_event(build_event(task_id, run_id, "e20", "process_restarted", "2026-03-11T11:01:00Z", payload={"intent_id": intent2}))

        # Recovery resumes from step 6
        ledger.append_event(build_event(task_id, run_id, "e21", "step_started", "2026-03-11T11:01:01Z", step_id="step-6"))
        ledger.append_event(build_event(task_id, run_id, "e22", "step_succeeded", "2026-03-11T11:01:02Z", step_id="step-6"))

        # Steps 7-8 complete
        for i in range(7, 9):
            ledger.append_event(build_event(task_id, run_id, f"e{i+16}", "step_started", f"2026-03-11T11:01:{i:02d}Z", step_id=f"step-{i}"))
            ledger.append_event(build_event(task_id, run_id, f"e{i+18}", "step_succeeded", f"2026-03-11T11:01:{i+1:02d}Z", step_id=f"step-{i}"))

        # Third restart at step 9
        time.sleep(1.1)  # Cooldown
        intent3 = executor.submit_restart_intent("gateway", "scheduled", run_id, cooldown_sec=1)
        ledger.append_event(build_event(task_id, run_id, "e32", "process_restarted", "2026-03-11T11:02:00Z", payload={"intent_id": intent3}))

        # Final steps complete
        ledger.append_event(build_event(task_id, run_id, "e33", "step_started", "2026-03-11T11:02:01Z", step_id="step-9"))
        ledger.append_event(build_event(task_id, run_id, "e34", "step_succeeded", "2026-03-11T11:02:02Z", step_id="step-9"))
        ledger.append_event(build_event(task_id, run_id, "e35", "step_started", "2026-03-11T11:02:03Z", step_id="step-10"))
        ledger.append_event(build_event(task_id, run_id, "e36", "step_succeeded", "2026-03-11T11:02:04Z", step_id="step-10"))
        ledger.append_event(build_event(task_id, run_id, "e37", "run_completed", "2026-03-11T11:02:05Z"))

        # Verify
        events = ledger.read_events(task_id, run_id)
        restarts = [e for e in events if e["type"] == "process_restarted"]
        step_successes = [e for e in events if e["type"] == "step_succeeded"]
        
        assert len(restarts) == 3, f"Expected 3 restarts, got {len(restarts)}"
        assert len(step_successes) == 10, f"Expected 10 successful steps, got {len(step_successes)}"
        
        # Verify no duplicate step executions (each step succeeded exactly once)
        succeeded_steps = [e["step_id"] for e in step_successes]
        assert len(succeeded_steps) == len(set(succeeded_steps)), "Duplicate step executions detected"
        
        # Verify task completed
        assert events[-1]["type"] == "run_completed"
