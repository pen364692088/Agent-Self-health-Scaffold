# Architecture Overview

This document provides a high‑level description of the **Agent‑Self‑health‑Scaffold v2** project.

## Project Goal

> Build a **constrained self-healing execution kernel** that allows OpenClaw to automatically detect drift, execute constrained repairs, verify results, and resume task progress after exceptions, restarts, context drift, and tool failures.

## Core Principles

1. **Task is truth, session is display** - Ledger is the single source of truth
2. **Recovery after restart** - No manual "continue" needed
3. **Constrained repair actions** - All repairs validated, rollbackable
4. **Unattended continuation** - System auto-resumes without human intervention

---

## Architecture Layers

### Layer 1: Task Control Plane
- `schemas/task-spec.schema.json` - TaskSpec definition
- `schemas/run-state.schema.json` - RunState materialization
- Defines desired state, success criteria, gates, retry policy

### Layer 2: Run Ledger (Truth Layer)
- `core/task_ledger.py` - Append-only JSONL ledger
- `core/state_materializer.py` - Derives RunState from events
- Event types: task_created, run_started, step_*, repair_*, gate_*, etc.

### Layer 3: Reconciler
- `core/reconciler/reconciler.py` - Compares desired vs actual state
- Triggers recovery actions based on drift detection

### Layer 4: Supervisor Tree
- L0: Process layer (gateway, worker)
- L1: Task layer (manager, coder, auditor runs)
- L2: Step layer (individual operations)

### Layer 5: Repair Library
- `docs/REPAIR_ACTIONS.md` - Constrained repair action definitions
- Each action: preconditions, risk level, validator, rollback

### Layer 6: Verification & Rollback
- `pipelines/gate-runner/` - Gate A/B/C validation
- All repairs must pass gates before commit

---

## Runtime Components

1. **Recovery Orchestrator** (`runtime/recovery-orchestrator/`)
   - `recovery_scan.py` - Scans ledger for incomplete runs
   - `recovery_apply.py` - Applies recovery decisions
   - `recovery_orchestrator.py` - Decision engine

2. **Out-of-band Restart Executor** (`runtime/restart_executor/`)
   - Submits restart intents (not in exec chain)
   - Cooldown protection
   - Triggers recovery after restart

3. **Transcript Rebuilder** (`runtime/transcript_rebuilder/`)
   - Rebuilds transcript from ledger events
   - Markdown + JSON output
   - No side effects on task truth

4. **Job Orchestrator** (`runtime/job_orchestrator/`)
   - Parent/child job DAG
   - Idempotency via idempotency_key
   - Retry/backoff policies

5. **Gate Runner** (`pipelines/gate-runner/`)
   - Gate A: Contract/Schema/Safety
   - Gate B: E2E Continuity
   - Gate C: Preflight/Operational Readiness

---

## Interaction Flow

```
Task Created → Run Started → Steps Execute → 
[On Failure] → Reconciler detects drift → Repair proposed → 
Gate validation → Repair applied → Task continues → Run Completed

[On Restart] → Recovery scan → Resume from last-good-step → Continue
```

The modular layout allows CI/CD systems to invoke components independently.

---

## E2E Test Coverage

| Test | Scenario |
|------|----------|
| E2E-01 | Gateway restart auto-resume |
| E2E-02 | Step failure → last-good-step recovery |
| E2E-03 | Transcript corruption → rebuild |
| E2E-04 | Child job missing → requeue |
| E2E-05 | High-risk repair → gate rollback |
| E2E-06 | Unattended long task across restarts |

See `docs/E2E_TEST_MATRIX.md` for details.
