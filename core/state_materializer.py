from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Set

TERMINAL_STATUSES = {"completed", "abandoned"}
HEARTBEAT_EVENT_TYPES = {"step_heartbeat", "step_started", "step_succeeded", "step_failed"}


@dataclass
class RunState:
    task_id: str
    run_id: str
    status: str
    current_step: Optional[str]
    last_good_step: Optional[str]
    pending_children: List[str]
    retry_count: int
    last_heartbeat: Optional[str]
    recovery_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RunStateMaterializer:
    def materialize(self, events: Iterable[Dict[str, Any]]) -> RunState:
        ordered = list(events)
        if not ordered:
            raise ValueError("Cannot materialize empty event stream")

        first = ordered[0]
        state = RunState(
            task_id=first["task_id"],
            run_id=first["run_id"],
            status="planned",
            current_step=None,
            last_good_step=None,
            pending_children=[],
            retry_count=0,
            last_heartbeat=None,
            recovery_status="eligible",
        )

        pending_children: Set[str] = set()
        repair_or_drift = False
        last_failure: Optional[str] = None

        for event in ordered:
            etype = event["type"]
            payload = event.get("payload", {})
            step_id = event.get("step_id") or payload.get("step_id")

            if etype in {"task_created"}:
                state.status = "planned"
            elif etype in {"run_started", "process_restarted"}:
                state.status = "running"
            elif etype == "step_started":
                state.status = "running"
                state.current_step = step_id
            elif etype == "step_heartbeat":
                if step_id:
                    state.current_step = step_id
            elif etype == "step_succeeded":
                state.status = "running"
                if step_id:
                    state.last_good_step = step_id
                if state.current_step == step_id:
                    state.current_step = None
                child_run_id = payload.get("child_run_id")
                if child_run_id:
                    pending_children.discard(child_run_id)
                last_failure = None
            elif etype == "step_failed":
                state.status = "running"
                state.current_step = step_id or state.current_step
                last_failure = payload.get("fault_code") or "STEP_FAILED"
            elif etype == "retry_scheduled":
                state.retry_count += 1
                state.status = "running"
            elif etype == "child_registered":
                child_run_id = payload.get("child_run_id")
                if child_run_id:
                    pending_children.add(child_run_id)
            elif etype == "child_missing_detected":
                repair_or_drift = True
                child_run_id = payload.get("child_run_id")
                if child_run_id:
                    pending_children.add(child_run_id)
                last_failure = "CHILD_JOB_MISSING"
            elif etype in {"repair_proposed", "repair_applied", "transcript_rebuilt"}:
                repair_or_drift = True
            elif etype == "gate_failed":
                state.status = "blocked"
                last_failure = payload.get("fault_code") or "GATE_FAILED"
            elif etype == "gate_passed":
                if state.status == "blocked":
                    state.status = "running"
            elif etype == "run_completed":
                state.status = "completed"
                state.current_step = None
            elif etype == "run_abandoned":
                state.status = "abandoned"
                state.current_step = None

            if etype in HEARTBEAT_EVENT_TYPES:
                state.last_heartbeat = event["ts"]

        state.pending_children = sorted(pending_children)
        state.recovery_status = self._derive_recovery_status(state, repair_or_drift, last_failure)
        return state

    def _derive_recovery_status(self, state: RunState, repair_or_drift: bool, last_failure: Optional[str]) -> str:
        if state.status == "completed":
            return "abandoned"
        if state.status == "abandoned":
            return "abandoned"
        if state.status == "blocked":
            return "blocked"
        if repair_or_drift or last_failure in {"TRANSCRIPT_CORRUPTED", "CHILD_JOB_MISSING", "STEP_POINTER_LOST"}:
            return "needs_repair"
        if last_failure is not None:
            return "retryable"
        return "eligible"
