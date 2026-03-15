from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


LEDGER_DIRNAME = "artifacts/run_ledger"


@dataclass(frozen=True)
class AppendResult:
    written: bool
    reason: str
    event: Dict[str, Any]


class TaskLedger:
    """Append-only JSONL ledger with per-run idempotency protection."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.ledger_dir = self.root / LEDGER_DIRNAME
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

    def ledger_path(self, task_id: str, run_id: str) -> Path:
        safe_task = task_id.replace("/", "_")
        safe_run = run_id.replace("/", "_")
        return self.ledger_dir / f"{safe_task}__{safe_run}.jsonl"

    def append_event(self, event: Dict[str, Any]) -> AppendResult:
        self._validate_event(event)
        path = self.ledger_path(event["task_id"], event["run_id"])
        existing = self.read_events(event["task_id"], event["run_id"])
        dup = self._find_duplicate(existing, event["idempotency_key"])
        if dup is not None:
            return AppendResult(written=False, reason="duplicate_idempotency_key", event=dup)

        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return AppendResult(written=True, reason="appended", event=event)

    def read_events(self, task_id: str, run_id: str) -> List[Dict[str, Any]]:
        path = self.ledger_path(task_id, run_id)
        if not path.exists():
            return []
        events: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                events.append(json.loads(line))
        return events

    def list_run_paths(self) -> List[Path]:
        return sorted(self.ledger_dir.glob("*.jsonl"))

    def list_runs(self) -> List[Dict[str, str]]:
        runs: List[Dict[str, str]] = []
        for path in self.list_run_paths():
            first = self._read_first_event(path)
            if first is None:
                continue
            runs.append({
                "task_id": first["task_id"],
                "run_id": first["run_id"],
                "path": str(path),
            })
        return runs

    def iter_all_events(self) -> Iterable[Dict[str, Any]]:
        for path in self.list_run_paths():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield json.loads(line)

    @staticmethod
    def _validate_event(event: Dict[str, Any]) -> None:
        required = ["event_id", "task_id", "run_id", "type", "ts", "payload", "idempotency_key"]
        missing = [key for key in required if key not in event]
        if missing:
            raise ValueError(f"Missing required event fields: {missing}")
        if not isinstance(event["payload"], dict):
            raise ValueError("payload must be an object")
        if event["parent_run_id"] if "parent_run_id" in event else None:
            if not isinstance(event["parent_run_id"], str):
                raise ValueError("parent_run_id must be string or null")

    @staticmethod
    def _find_duplicate(events: Iterable[Dict[str, Any]], idempotency_key: str) -> Optional[Dict[str, Any]]:
        for event in events:
            if event.get("idempotency_key") == idempotency_key:
                return event
        return None

    @staticmethod
    def _read_first_event(path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    return json.loads(line)
        return None
