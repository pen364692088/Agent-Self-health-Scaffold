from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "runtime" / "recovery-orchestrator") not in sys.path:
    sys.path.insert(0, str(ROOT / "runtime" / "recovery-orchestrator"))

from core.task_ledger import TaskLedger
from recovery_orchestrator import RecoveryOrchestrator, RecoveryDecision


@dataclass
class AppliedDecision:
    task_id: str
    run_id: str
    action: str
    reason: str
    status: str
    event_type: str
    event_id: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


class Reconciler:
    """Consumes recovery decisions and materializes durable continuation events."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.ledger = TaskLedger(self.root)
        self.orchestrator = RecoveryOrchestrator(self.root)

    def scan_and_apply(self) -> List[AppliedDecision]:
        decisions = self.orchestrator.scan()
        applied: List[AppliedDecision] = []
        for decision in decisions:
            results = self.apply_decision(decision)
            applied.extend(results)
        return applied

    def apply_decision(self, decision: RecoveryDecision) -> List[AppliedDecision]:
        if decision.action == "repair" and decision.pending_children:
            return self._apply_missing_child_requeue(decision)

        event_type = self._event_type_for(decision.action)
        if event_type is None:
            return []

        return [self._append_decision_event(decision, event_type)]

    def _append_decision_event(self, decision: RecoveryDecision, event_type: str) -> AppliedDecision:
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        event_id = f"evt-{event_type}-{decision.task_id}-{decision.run_id}"
        event = {
            "event_id": event_id,
            "task_id": decision.task_id,
            "run_id": decision.run_id,
            "parent_run_id": None,
            "step_id": decision.current_step,
            "type": event_type,
            "ts": ts,
            "payload": {
                "action": decision.action,
                "reason": decision.reason,
                "recovery_status": decision.recovery_status,
                "current_step": decision.current_step,
                "last_good_step": decision.last_good_step,
                "pending_children": list(decision.pending_children),
                "retry_count": decision.retry_count,
            },
            "idempotency_key": f"{event_type}:{decision.task_id}:{decision.run_id}:{decision.action}:{decision.current_step or '-'}:{decision.retry_count}",
        }
        append = self.ledger.append_event(event)
        status = "applied" if append.written else "duplicate"
        return AppliedDecision(
            task_id=decision.task_id,
            run_id=decision.run_id,
            action=decision.action,
            reason=decision.reason,
            status=status,
            event_type=event_type,
            event_id=append.event["event_id"],
        )

    def _apply_missing_child_requeue(self, decision: RecoveryDecision) -> List[AppliedDecision]:
        applied: List[AppliedDecision] = [self._append_decision_event(decision, "repair_proposed")]
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        for child_id in decision.pending_children:
            event = {
                "event_id": f"evt-job-submitted-{decision.task_id}-{decision.run_id}-{child_id}",
                "task_id": decision.task_id,
                "run_id": decision.run_id,
                "parent_run_id": None,
                "step_id": child_id,
                "type": "job_submitted",
                "ts": ts,
                "payload": {
                    "job_id": child_id,
                    "requeued": True,
                    "source": "reconciler",
                    "reason": decision.reason,
                },
                "idempotency_key": f"job_submitted:requeue:{decision.task_id}:{decision.run_id}:{child_id}",
            }
            append = self.ledger.append_event(event)
            applied.append(
                AppliedDecision(
                    task_id=decision.task_id,
                    run_id=decision.run_id,
                    action="repair",
                    reason=f"requeue_missing_child:{child_id}",
                    status="applied" if append.written else "duplicate",
                    event_type="job_submitted",
                    event_id=append.event["event_id"],
                )
            )
        return applied

    @staticmethod
    def _event_type_for(action: str) -> str | None:
        mapping = {
            "resume": "recovery_hook_triggered",
            "retry": "retry_scheduled",
            "repair": "repair_proposed",
        }
        return mapping.get(action)


def apply_recovery_scan(root: Path | str) -> List[AppliedDecision]:
    return Reconciler(root).scan_and_apply()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    applied = apply_recovery_scan(args.root)
    out = {
        "status": "ok",
        "applied_count": len(applied),
        "applied": [x.to_dict() for x in applied],
    }
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for item in applied:
            print(f"{item.task_id} {item.run_id} -> {item.action} [{item.status}]")
