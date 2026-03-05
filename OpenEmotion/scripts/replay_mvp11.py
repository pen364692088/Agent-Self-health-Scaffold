#!/usr/bin/env python3
"""Replay utilities for MVP11 deterministic verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emotiond.loop_mvp10 import LoopMVP10


def load_run(run_id: str, artifacts_dir: str = "artifacts/mvp11") -> List[Dict[str, Any]]:
    log_path = Path(artifacts_dir) / f"{run_id}.jsonl"
    if not log_path.exists():
        raise FileNotFoundError(f"run log not found: {log_path}")

    events: List[Dict[str, Any]] = []
    with log_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def _canonical_event(event: Dict[str, Any]) -> Dict[str, Any]:
    # Strip volatile fields to compare semantic determinism.
    e = dict(event)
    e.pop("ts", None)
    e.pop("run_id", None)
    return e


def compute_event_hash(event: Dict[str, Any]) -> str:
    payload = json.dumps(_canonical_event(event), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def replay_run(run_id: str, artifacts_dir: str = "artifacts/mvp11") -> Dict[str, Any]:
    artifacts = Path(artifacts_dir)
    summary_path = artifacts / f"summary_{run_id}.json"
    if not summary_path.exists():
        return {"error": f"summary not found: {summary_path}"}

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    seed = int(summary.get("seed", 42))
    ticks = int(summary.get("ticks_executed", 0))
    goals = summary.get("goals") or [f"goal_{i}" for i in range(8)]
    intervention = summary.get("intervention")

    original = load_run(run_id, artifacts_dir=artifacts_dir)

    with tempfile.TemporaryDirectory(prefix="mvp11_replay_") as tmp:
        loop = LoopMVP10(seed=seed, artifacts_dir=tmp, intervention=intervention, use_mock_planner=True)
        loop.start(goals=goals)
        for _ in range(ticks):
            loop.tick()
        replay_summary = loop.stop()
        replay_events = load_run(replay_summary["run_id"], artifacts_dir=tmp)

    size = min(len(original), len(replay_events))
    if size == 0:
        return {
            "original_events": len(original),
            "replay_events": len(replay_events),
            "hash_match_rate": 0.0,
            "matched": 0,
            "compared": 0,
        }

    matched = 0
    mismatches: List[int] = []
    for idx in range(size):
        if compute_event_hash(original[idx]) == compute_event_hash(replay_events[idx]):
            matched += 1
        else:
            mismatches.append(idx)

    return {
        "original_run_id": run_id,
        "replay_run_id": replay_summary["run_id"],
        "seed": seed,
        "intervention": intervention,
        "original_events": len(original),
        "replay_events": len(replay_events),
        "matched": matched,
        "compared": size,
        "hash_match_rate": round(matched / size, 6),
        "mismatches": mismatches[:20],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--artifacts-dir", default="artifacts/mvp11")
    args = ap.parse_args()

    result = replay_run(args.run_id, artifacts_dir=args.artifacts_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
