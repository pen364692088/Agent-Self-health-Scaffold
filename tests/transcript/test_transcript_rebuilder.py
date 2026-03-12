"""Tests for Transcript Rebuilder."""
import json
import pytest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RUNTIME = ROOT / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from core.task_ledger import TaskLedger
from transcript_rebuilder.transcript_rebuilder import (
    TranscriptRebuilder,
    TranscriptRebuildInput,
    TranscriptSnapshot,
    rebuild_transcript,
)


def build_event(event_type: str, ts: str, step_id: str = None, **extra):
    return {
        "event_id": f"evt-{event_type}-{ts}",
        "task_id": "task-1",
        "run_id": "run-1",
        "type": event_type,
        "ts": ts,
        "step_id": step_id,
        "payload": extra,
        "idempotency_key": f"key-{event_type}-{ts}",
    }


def test_rebuild_happy_path(tmp_path):
    # Setup ledger with events
    ledger = TaskLedger(tmp_path)
    events = [
        build_event("task_created", "2026-03-11T07:00:00Z"),
        build_event("run_started", "2026-03-11T07:00:01Z"),
        build_event("step_started", "2026-03-11T07:00:02Z", step_id="step-a"),
        build_event("step_succeeded", "2026-03-11T07:00:03Z", step_id="step-a"),
        build_event("step_started", "2026-03-11T07:00:04Z", step_id="step-b"),
        build_event("step_succeeded", "2026-03-11T07:00:05Z", step_id="step-b"),
        build_event("run_completed", "2026-03-11T07:00:06Z"),
    ]
    for e in events:
        ledger.append_event(e)

    # Rebuild transcript
    rebuilder = TranscriptRebuilder(tmp_path)
    snapshot = rebuilder.rebuild_transcript(TranscriptRebuildInput(
        task_id="task-1",
        run_id="run-1",
    ))

    assert snapshot.event_count == 7
    assert len(snapshot.step_sequence) == 2
    assert snapshot.step_sequence[0].step_id == "step-a"
    assert snapshot.step_sequence[0].status == "succeeded"
    assert snapshot.step_sequence[1].step_id == "step-b"


def test_rebuild_detects_failed_steps(tmp_path):
    ledger = TaskLedger(tmp_path)
    events = [
        build_event("task_created", "2026-03-11T07:00:00Z"),
        build_event("run_started", "2026-03-11T07:00:01Z"),
        build_event("step_started", "2026-03-11T07:00:02Z", step_id="step-a"),
        build_event("step_failed", "2026-03-11T07:00:03Z", step_id="step-a"),
    ]
    for e in events:
        ledger.append_event(e)

    rebuilder = TranscriptRebuilder(tmp_path)
    snapshot = rebuilder.rebuild_transcript(TranscriptRebuildInput(
        task_id="task-1",
        run_id="run-1",
    ))

    assert snapshot.step_sequence[0].status == "failed"
    assert "failed" in snapshot.summary


def test_rebuild_warns_on_missing_start(tmp_path):
    ledger = TaskLedger(tmp_path)
    events = [
        build_event("task_created", "2026-03-11T07:00:00Z"),
        build_event("run_started", "2026-03-11T07:00:01Z"),
        # step_succeeded without step_started
        build_event("step_succeeded", "2026-03-11T07:00:03Z", step_id="step-a"),
    ]
    for e in events:
        ledger.append_event(e)

    rebuilder = TranscriptRebuilder(tmp_path)
    snapshot = rebuilder.rebuild_transcript(TranscriptRebuildInput(
        task_id="task-1",
        run_id="run-1",
    ))

    assert len(snapshot.warnings) >= 1
    assert "without start event" in snapshot.warnings[0]


def test_rebuild_outputs_markdown_file(tmp_path):
    ledger = TaskLedger(tmp_path)
    events = [
        build_event("task_created", "2026-03-11T07:00:00Z"),
        build_event("run_started", "2026-03-11T07:00:01Z"),
        build_event("step_started", "2026-03-11T07:00:02Z", step_id="step-a"),
        build_event("step_succeeded", "2026-03-11T07:00:03Z", step_id="step-a"),
    ]
    for e in events:
        ledger.append_event(e)

    rebuilder = TranscriptRebuilder(tmp_path)
    rebuilder.rebuild_transcript(TranscriptRebuildInput(
        task_id="task-1",
        run_id="run-1",
        output_format="markdown",
    ))

    transcript_path = tmp_path / "artifacts/transcripts/task-1__run-1.md"
    assert transcript_path.exists()
    content = transcript_path.read_text()
    assert "# Transcript" in content
    assert "step-a" in content


def test_rebuild_outputs_json_file(tmp_path):
    ledger = TaskLedger(tmp_path)
    events = [
        build_event("task_created", "2026-03-11T07:00:00Z"),
        build_event("run_started", "2026-03-11T07:00:01Z"),
        build_event("step_started", "2026-03-11T07:00:02Z", step_id="step-a"),
        build_event("step_succeeded", "2026-03-11T07:00:03Z", step_id="step-a"),
    ]
    for e in events:
        ledger.append_event(e)

    rebuilder = TranscriptRebuilder(tmp_path)
    rebuilder.rebuild_transcript(TranscriptRebuildInput(
        task_id="task-1",
        run_id="run-1",
        output_format="json",
    ))

    transcript_path = tmp_path / "artifacts/transcripts/task-1__run-1.json"
    assert transcript_path.exists()
    data = json.loads(transcript_path.read_text())
    assert data["task_id"] == "task-1"
    assert data["run_id"] == "run-1"


def test_convenience_function(tmp_path):
    ledger = TaskLedger(tmp_path)
    for e in [
        build_event("task_created", "2026-03-11T07:00:00Z"),
        build_event("run_started", "2026-03-11T07:00:01Z"),
    ]:
        ledger.append_event(e)

    snapshot = rebuild_transcript(tmp_path, "task-1", "run-1")
    assert isinstance(snapshot, TranscriptSnapshot)
