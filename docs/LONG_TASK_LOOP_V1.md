# Long Task Loop v1 - Design Document

## Overview

This document defines the **Checkpointed Step Loop v1**, a durable execution framework for long-running tasks that must survive context loss, agent restart, and partial failure.

## Core Principle

**Task truth is primary; transcript is derived.**

The system must be able to continue execution without relying on chat history or model memory. All state must be persisted in machine-readable formats that enable deterministic recovery.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Checkpointed Step Loop                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Task Dossier │───▶│ Step Packet  │───▶│ Step Executor│      │
│  │   (规划)      │    │   (执行包)    │    │   (执行)     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ task_state   │    │ step_result  │    │  evidence/   │      │
│  │    .json     │    │    .json     │    │  handoff/    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             ▼                                   │
│                    ┌──────────────┐                             │
│                    │    Ledger    │                             │
│                    │   (事件日志)  │                             │
│                    └──────────────┘                             │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Step Lease   │    │Resume Engine │    │ Completion   │      │
│  │   (租约)      │    │  (恢复引擎)   │    │ Gatekeeper   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
artifacts/tasks/<task_id>/
├── TASK.md                    # Human-readable contract
├── task_state.json            # Machine truth (control plane)
├── PLAN.md                    # Execution plan
├── plan_graph.json            # Dependency graph
├── steps/                     # Step execution packets
│   ├── S01/
│   │   ├── step_packet.json
│   │   ├── result.json
│   │   └── lease.json
│   ├── S02/
│   └── ...
├── evidence/                  # Execution evidence
│   ├── S01/
│   │   ├── file_changes.diff
│   │   ├── test_output.txt
│   │   └── ...
│   └── ...
├── handoff/                   # Human-readable handoffs
│   ├── S01.md
│   ├── S02.md
│   └── ...
└── final/                     # Final deliverables
    ├── SUMMARY.md
    ├── receipt.json
    └── gate_report.json
```

## State Machine

### Task States

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ created │────▶│ running │────▶│ blocked │────▶│ running │
└─────────┘     └────┬────┘     └─────────┘     └────┬────┘
                     │                               │
                     │         ┌─────────┐          │
                     └────────▶│ completed│◀────────┘
                     │         └─────────┘          │
                     │         ┌─────────┐          │
                     └────────▶│  failed │◀─────────┘
                               └─────────┘
```

### Step States

```
pending → running → success
                 → failed (retryable)
                 → failed (blocked)
                 → failed (terminal)
```

## Recovery Protocol

### Resume Sequence

1. **Load task_state.json** - Get current task state
2. **Read ledger** - Find last N events
3. **Identify incomplete step** - Find step not in `success` state
4. **Check lease validity** - Is current step lease expired?
5. **Rebuild step context** - Load step packet + previous evidence
6. **Continue execution** - Execute or retry from last known state

### Lease Mechanism

Each step has a lease to prevent:
- Duplicate execution by multiple workers
- Stale worker continuing after crash
- Race conditions on resume

```
lease = {
  owner: worker_id,
  acquired_at: timestamp,
  expires_at: timestamp + ttl,
  heartbeat: last_heartbeat_timestamp
}

# On resume:
if lease.expired:
  new_owner = current_worker
  acquire_lease(new_owner)
else:
  wait_or_fail()
```

## Step Packet Structure

Every step must be self-contained:

```json
{
  "step_id": "S01",
  "title": "Step title",
  "goal": "What this step achieves",
  "inputs": [
    {"name": "input1", "path": "artifacts/tasks/xxx/evidence/S00/..." }
  ],
  "allowed_files": ["path/to/file1", "path/to/file2"],
  "expected_outputs": [
    {"name": "output1", "path": "...", "validator": "..."}
  ],
  "exit_criteria": [
    "condition 1",
    "condition 2"
  ],
  "failure_policy": {
    "max_retries": 3,
    "backoff": "exponential",
    "on_failure": "block|skip|abort"
  },
  "depends_on": []
}
```

## Result Structure

After each step execution:

```json
{
  "step_id": "S01",
  "status": "success|failed|blocked|retryable",
  "started_at": "ISO timestamp",
  "completed_at": "ISO timestamp",
  "changed_files": ["path/to/file1", "path/to/file2"],
  "outputs": {
    "output1": "value or path"
  },
  "tests": {
    "run": true,
    "passed": 5,
    "failed": 0
  },
  "evidence_path": "artifacts/tasks/xxx/evidence/S01/",
  "next_step_hint": "S02",
  "uncertainty": null,
  "error": null
}
```

## Completion Gate

Before any task can be marked "completed", must pass:

### Gate A: Contract
- [ ] All required deliverables exist
- [ ] Schema validation passes
- [ ] Evidence present for each step

### Gate B: E2E Verification
- [ ] Tests pass
- [ ] Expected outputs exist
- [ ] No blocked steps remaining

### Gate C: Integrity
- [ ] task_state matches ledger
- [ ] No missing evidence
- [ ] No "summary-only" completion

## Anti-Patterns (Forbidden)

1. **Handoff-only recovery** - Cannot rely solely on handoff.md
2. **Transcript as truth** - Chat history is not control plane
3. **Summary without evidence** - Cannot claim completion without proof
4. **Gate bypass** - No "looks right, skip verification"
5. **Parallel runtime** - Must extend existing core/runtime, not create new

## File Responsibilities

| File | Purpose | Audience |
|------|---------|----------|
| TASK.md | Human contract | Human |
| task_state.json | Machine truth | System |
| step_packet.json | Execution instruction | Executor |
| result.json | Step outcome | System |
| handoff/S01.md | Human explanation | Human |
| evidence/S01/* | Proofs | Audit |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-15 | Initial design |
