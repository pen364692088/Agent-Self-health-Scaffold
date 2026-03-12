# v2 Interface Freeze

**Frozen**: 2026-03-11
**Status**: STABLE

---

## 1. Restart Executor Interfaces

### RestartIntent
```json
{
  "intent_id": "string (uuid)",
  "target": "gateway | worker | all",
  "reason": "stalled | drift_detected | manual | scheduled",
  "trigger_run_id": "string | null",
  "requested_at": "iso8601",
  "cooldown_until": "iso8601 | null"
}
```

### RestartResult
```json
{
  "intent_id": "string",
  "status": "pending | executing | completed | failed",
  "executed_at": "iso8601 | null",
  "recovery_triggered": "boolean",
  "error": "string | null"
}
```

### Restart Hook Contract
```python
def submit_restart_intent(intent: RestartIntent) -> str:
    """Returns intent_id, executes out-of-band"""
    
def check_restart_status(intent_id: str) -> RestartResult:
    """Poll for completion"""
```

---

## 2. Transcript Rebuilder Interfaces

### TranscriptRebuildInput
```json
{
  "task_id": "string",
  "run_id": "string",
  "from_ledger_path": "string",
  "output_format": "markdown | json",
  "include_events": ["step_started", "step_succeeded", "step_failed", "..."]
}
```

### TranscriptSnapshot
```json
{
  "task_id": "string",
  "run_id": "string",
  "rebuilt_at": "iso8601",
  "event_count": "integer",
  "step_sequence": [
    {"step_id": "string", "status": "succeeded|failed|skipped", "ts": "iso8601"}
  ],
  "summary": "string",
  "warnings": ["string"]
}
```

### Rebuilder Contract
```python
def rebuild_transcript(input: TranscriptRebuildInput) -> TranscriptSnapshot:
    """Read ledger, materialize transcript, return snapshot"""
```

---

## 3. Job Orchestrator Interfaces

### JobSpec
```json
{
  "job_id": "string",
  "task_id": "string",
  "run_id": "string",
  "agent_role": "manager | coder | auditor",
  "command": "string",
  "args": ["string"],
  "timeout_sec": "integer",
  "retry_policy": {
    "max_attempts": "integer",
    "backoff": "fixed | linear | exponential"
  },
  "depends_on": ["job_id"],
  "idempotency_key": "string"
}
```

### JobRunState
```json
{
  "job_id": "string",
  "status": "pending | running | succeeded | failed | retrying",
  "attempt": "integer",
  "started_at": "iso8601 | null",
  "completed_at": "iso8601 | null",
  "exit_code": "integer | null",
  "output_path": "string | null",
  "error": "string | null"
}
```

### ParentChildDependency
```json
{
  "parent_job_id": "string",
  "child_job_ids": ["string"],
  "wait_strategy": "all | any | none",
  "on_child_failure": "fail | continue | retry_child"
}
```

### Orchestrator Contract
```python
def submit_job(spec: JobSpec) -> str:
    """Returns job_id, persists to ledger"""
    
def get_job_state(job_id: str) -> JobRunState:
    """Query current state"""
    
def await_children(parent_job_id: str, timeout_sec: int) -> List[JobRunState]:
    """Block until children complete"""
```

---

## 4. Recovery Hook Interface

### RecoveryHook
```python
@dataclass
class RecoveryHook:
    name: str
    trigger: Callable[[RunState], bool]
    action: Callable[[RunState], str]  # Returns action taken
    priority: int  # Lower = higher priority
```

### Hook Registration
```python
def register_recovery_hook(hook: RecoveryHook) -> None:
    """Add hook to registry"""
    
def run_recovery_hooks(state: RunState) -> List[str]:
    """Run applicable hooks in priority order, return actions taken"""
```

---

## 5. E2E Test Skeleton

### E2E-01: Gateway Restart Auto-Resume
**Goal**: Running task auto-resumes after gateway restart
**Setup**: Start task, trigger restart, verify continuation
**Pass Criteria**: 
- No manual "continue" needed
- Task completes within timeout
- Ledger shows recovery events

### E2E-02: Step Failure → Last-Good-Step Recovery
**Goal**: Mid-task failure resumes from last successful step
**Setup**: Inject failure at step N, verify resume from step N-1
**Pass Criteria**:
- Steps 1..N-1 not re-executed
- Step N retry succeeds or fails gracefully

### E2E-03: Transcript Corruption → Rebuild
**Goal**: Corrupt transcript, verify rebuild from ledger
**Setup**: Delete/corrupt transcript file, trigger rebuild
**Pass Criteria**:
- Transcript rebuilt from ledger events
- Task continues normally

### E2E-04: Child Job Missing → Requeue
**Goal**: Missing child job detected and requeued
**Setup**: Delete child job record, verify detection + requeue
**Pass Criteria**:
- `child_missing_detected` event logged
- Child re-executed exactly once
- Parent completes

### E2E-05: High-Risk Repair → Gate Check → Rollback
**Goal**: High-risk repair fails gate, auto-rollback
**Setup**: Propose risky repair, fail gate, verify rollback
**Pass Criteria**:
- Gate failure logged
- Repair not applied
- Run returns to safe state

### E2E-06: Unattended Long Task Across Restarts
**Goal**: Long task survives multiple restarts without human input
**Setup**: 10-step task, inject 3 restarts, verify completion
**Pass Criteria**:
- All restarts auto-recovered
- Task completed end-to-end
- No manual intervention

---

## 6. Ledger Event Extensions

Additional event types for v2:
- `restart_intent_created`
- `restart_completed`
- `transcript_rebuilt`
- `job_submitted`
- `job_started`
- `job_succeeded`
- `job_failed`
- `dependency_resolved`
- `recovery_hook_triggered`

---

## Stability Rules

1. These interfaces are FROZEN for v2 implementation
2. Changes require explicit version bump
3. All implementations must validate against schemas
4. Backward compatibility required for ledger events
