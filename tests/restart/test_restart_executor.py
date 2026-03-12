"""Tests for Out-of-band Restart Executor."""
import json
import pytest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import sys
import os
# Add runtime to path
RUNTIME = Path(__file__).resolve().parents[2] / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from restart_executor.restart_executor import (
    RestartExecutor,
    RestartIntent,
    RestartResult,
    submit_restart_intent,
    check_restart_status,
)


def test_submit_restart_intent_creates_file(tmp_path):
    executor = RestartExecutor(tmp_path)
    intent_id = executor.submit_restart_intent(
        target="gateway",
        reason="stalled",
        trigger_run_id="run-1",
    )
    assert intent_id

    intent_path = tmp_path / "artifacts/restart_intents" / f"{intent_id}.json"
    assert intent_path.exists()

    with intent_path.open() as f:
        data = json.load(f)
    assert data["target"] == "gateway"
    assert data["reason"] == "stalled"


def test_check_restart_status_pending(tmp_path):
    executor = RestartExecutor(tmp_path)
    intent_id = executor.submit_restart_intent(target="worker", reason="manual")
    result = executor.check_restart_status(intent_id)
    assert result.status in ("pending", "executing")


def test_cooldown_blocks_immediate_repeat(tmp_path):
    executor = RestartExecutor(tmp_path)
    executor.submit_restart_intent(target="gateway", reason="stalled", cooldown_sec=300)

    with pytest.raises(RuntimeError, match="Cooldown active"):
        executor.submit_restart_intent(target="gateway", reason="drift_detected")


def test_ledger_event_logged_when_trigger_run_provided(tmp_path):
    executor = RestartExecutor(tmp_path)
    executor.submit_restart_intent(
        target="gateway",
        reason="stalled",
        trigger_run_id="run-123",
    )

    # Check ledger event
    ledger_path = tmp_path / "artifacts/run_ledger"
    ledger_files = list(ledger_path.glob("*.jsonl"))
    assert len(ledger_files) >= 1

    with ledger_files[0].open() as f:
        events = [json.loads(line) for line in f if line.strip()]

    assert any(e["type"] == "restart_intent_created" for e in events)


def test_convenience_functions(tmp_path):
    intent_id = submit_restart_intent(
        root=tmp_path,
        target="gateway",
        reason="manual",
    )
    assert intent_id

    result = check_restart_status(tmp_path, intent_id)
    assert isinstance(result, RestartResult)


def test_generated_script_triggers_recovery_apply(tmp_path):
    executor = RestartExecutor(tmp_path)
    intent = RestartIntent(
        intent_id="test-id",
        target="gateway",
        reason="manual",
        trigger_run_id="run-1",
        requested_at="2026-03-11T07:00:00Z",
        cooldown_until="2026-03-11T07:01:00Z",
    )
    script = executor._generate_restart_script(intent)
    assert "runtime/recovery-orchestrator/recovery_apply.py" in script
    assert "recovery_scan.py" not in script


def test_intent_serialization():
    intent = RestartIntent(
        intent_id="test-id",
        target="gateway",
        reason="manual",
        trigger_run_id="run-1",
        requested_at="2026-03-11T07:00:00Z",
        cooldown_until="2026-03-11T07:01:00Z",
    )
    d = intent.to_dict()
    restored = RestartIntent.from_dict(d)
    assert restored.intent_id == intent.intent_id
    assert restored.target == intent.target
