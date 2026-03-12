"""
Event-to-Transcript Rebuilder

Rebuilds transcript from ledger events, allowing recovery from
session/compaction/ordering corruption without losing task truth.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.task_ledger import TaskLedger

TRANSCRIPTS_DIR = "artifacts/transcripts"


@dataclass
class StepRecord:
    step_id: str
    status: str  # succeeded | failed | skipped | running
    ts: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class TranscriptSnapshot:
    task_id: str
    run_id: str
    rebuilt_at: str
    event_count: int
    step_sequence: List[StepRecord]
    summary: str
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["step_sequence"] = [s.to_dict() for s in self.step_sequence]
        return d


@dataclass
class TranscriptRebuildInput:
    task_id: str
    run_id: str
    from_ledger_path: Optional[str] = None
    output_format: str = "markdown"  # markdown | json
    include_events: Optional[List[str]] = None


class TranscriptRebuilder:
    """Rebuilds transcript from ledger events."""

    STEP_EVENTS = {"step_started", "step_succeeded", "step_failed", "step_heartbeat"}
    TERMINAL_EVENTS = {"step_succeeded", "step_failed"}

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.transcripts_dir = self.root / TRANSCRIPTS_DIR
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = TaskLedger(self.root)

    def rebuild_transcript(self, input: TranscriptRebuildInput) -> TranscriptSnapshot:
        """Rebuild transcript from ledger events."""
        # Read events from ledger
        events = self.ledger.read_events(input.task_id, input.run_id)
        if not events:
            raise ValueError(f"No events found for task={input.task_id} run={input.run_id}")

        # Filter events if specified
        if input.include_events:
            events = [e for e in events if e["type"] in input.include_events]

        # Build step sequence
        steps: Dict[str, StepRecord] = {}
        step_order: List[str] = []
        warnings: List[str] = []

        for event in events:
            etype = event["type"]
            step_id = event.get("step_id") or event.get("payload", {}).get("step_id")
            ts = event["ts"]

            if etype == "step_started" and step_id:
                if step_id not in steps:
                    steps[step_id] = StepRecord(step_id=step_id, status="running", ts=ts)
                    step_order.append(step_id)
            elif etype == "step_succeeded" and step_id:
                if step_id in steps:
                    steps[step_id].status = "succeeded"
                else:
                    # Step completed without start event
                    steps[step_id] = StepRecord(step_id=step_id, status="succeeded", ts=ts)
                    step_order.append(step_id)
                    warnings.append(f"Step {step_id} completed without start event")
            elif etype == "step_failed" and step_id:
                if step_id in steps:
                    steps[step_id].status = "failed"
                else:
                    steps[step_id] = StepRecord(step_id=step_id, status="failed", ts=ts)
                    step_order.append(step_id)
                    warnings.append(f"Step {step_id} failed without start event")

        # Build summary
        succeeded = sum(1 for s in steps.values() if s.status == "succeeded")
        failed = sum(1 for s in steps.values() if s.status == "failed")
        running = sum(1 for s in steps.values() if s.status == "running")

        if failed > 0:
            summary = f"Task: {succeeded} succeeded, {failed} failed, {running} running"
        else:
            summary = f"Task: {succeeded} steps completed successfully"

        snapshot = TranscriptSnapshot(
            task_id=input.task_id,
            run_id=input.run_id,
            rebuilt_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            event_count=len(events),
            step_sequence=[steps[sid] for sid in step_order if sid in steps],
            summary=summary,
            warnings=warnings,
        )

        # Write to file
        self._write_snapshot(snapshot, input.output_format)

        # Log to ledger
        self._log_transcript_rebuilt(snapshot)

        return snapshot

    def _write_snapshot(self, snapshot: TranscriptSnapshot, output_format: str) -> None:
        """Write snapshot to file."""
        path = self.transcripts_dir / f"{snapshot.task_id}__{snapshot.run_id}"

        if output_format == "json":
            path = path.with_suffix(".json")
            with path.open("w") as f:
                json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)
        else:
            path = path.with_suffix(".md")
            lines = [
                f"# Transcript: {snapshot.task_id}/{snapshot.run_id}",
                f"",
                f"**Rebuilt**: {snapshot.rebuilt_at}",
                f"**Events**: {snapshot.event_count}",
                f"",
                f"## Step Sequence",
                f"",
            ]
            for step in snapshot.step_sequence:
                status_icon = {"succeeded": "✅", "failed": "❌", "running": "🔄", "skipped": "⏭️"}.get(step.status, "❓")
                lines.append(f"- {status_icon} **{step.step_id}** ({step.status}) @ {step.ts}")

            lines.append(f"")
            lines.append(f"## Summary")
            lines.append(f"")
            lines.append(snapshot.summary)

            if snapshot.warnings:
                lines.append(f"")
                lines.append(f"## Warnings")
                lines.append(f"")
                for w in snapshot.warnings:
                    lines.append(f"- ⚠️ {w}")

            with path.open("w") as f:
                f.write("\n".join(lines))

    def _log_transcript_rebuilt(self, snapshot: TranscriptSnapshot) -> None:
        """Log transcript rebuild to ledger."""
        event = {
            "event_id": f"evt-transcript-{snapshot.task_id}-{snapshot.run_id}",
            "task_id": snapshot.task_id,
            "run_id": snapshot.run_id,
            "type": "transcript_rebuilt",
            "ts": snapshot.rebuilt_at,
            "payload": {
                "event_count": snapshot.event_count,
                "step_count": len(snapshot.step_sequence),
                "warnings_count": len(snapshot.warnings),
            },
            "idempotency_key": f"transcript-rebuild-{snapshot.task_id}-{snapshot.run_id}",
        }
        self.ledger.append_event(event)


def rebuild_transcript(
    root: Path | str,
    task_id: str,
    run_id: str,
    output_format: str = "markdown",
) -> TranscriptSnapshot:
    """Convenience function to rebuild transcript."""
    rebuilder = TranscriptRebuilder(root)
    input = TranscriptRebuildInput(
        task_id=task_id,
        run_id=run_id,
        output_format=output_format,
    )
    return rebuilder.rebuild_transcript(input)
