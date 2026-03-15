from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.task_ledger import TaskLedger
from core.state_materializer import RunStateMaterializer, RunState


@dataclass
class RecoveryDecision:
    task_id: str
    run_id: str
    status: str
    recovery_status: str
    action: str
    reason: str
    current_step: Optional[str]
    last_good_step: Optional[str]
    pending_children: List[str]
    retry_count: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class RecoveryOrchestrator:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.ledger = TaskLedger(self.root)
        self.materializer = RunStateMaterializer()

    def scan(self) -> List[RecoveryDecision]:
        decisions: List[RecoveryDecision] = []
        for run in self.ledger.list_runs():
            events = self.ledger.read_events(run['task_id'], run['run_id'])
            if not events:
                continue
            state = self.materializer.materialize(events)
            decisions.append(self.decide(state))
        return sorted(decisions, key=lambda d: (d.task_id, d.run_id))

    def decide(self, state: RunState) -> RecoveryDecision:
        action = 'observe'
        reason = 'no_action_needed'

        if state.status == 'completed':
            action = 'none'
            reason = 'run_already_completed'
        elif state.status == 'abandoned':
            action = 'none'
            reason = 'run_already_abandoned'
        elif state.recovery_status == 'blocked':
            action = 'block'
            reason = 'gate_or_policy_block'
        elif state.recovery_status == 'needs_repair':
            if state.pending_children:
                action = 'repair'
                reason = 'missing_or_unreconciled_child_jobs'
            else:
                action = 'repair'
                reason = 'drift_or_transcript_repair_required'
        elif state.recovery_status == 'retryable':
            action = 'retry'
            reason = 'step_failed_with_retry_budget_remaining'
        elif state.recovery_status == 'eligible':
            if state.current_step:
                action = 'resume'
                reason = 'resume_current_step'
            elif state.last_good_step:
                action = 'resume'
                reason = 'resume_from_last_good_step'
            else:
                action = 'resume'
                reason = 'resume_from_run_start'

        return RecoveryDecision(
            task_id=state.task_id,
            run_id=state.run_id,
            status=state.status,
            recovery_status=state.recovery_status,
            action=action,
            reason=reason,
            current_step=state.current_step,
            last_good_step=state.last_good_step,
            pending_children=list(state.pending_children),
            retry_count=state.retry_count,
        )
