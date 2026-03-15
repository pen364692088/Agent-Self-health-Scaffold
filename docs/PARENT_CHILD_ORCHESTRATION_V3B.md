# Checkpointed Step Loop v3-B - Parent-Child Task Orchestration

## Overview

This document defines the parent-child task orchestration layer for Checkpointed Step Loop v3-B, built on top of v3-A scheduling and the frozen v2 baseline.

## Core Principle

**v3-B adds parent-child orchestration, not a replacement for v2/v3-A.**

All baseline protections remain in force:
- v2: SUMMARY.md required, Gate integrity, no re-execution of success steps
- v3-A: Slot + Lease required, admission control, conflict avoidance

---

## Parent-Child Relationship Model

### Relationship Structure

```json
{
  "relationship_id": "rel_xxx",
  "parent_task_id": "task_parent_xxx",
  "child_task_id": "task_child_xxx",
  "relation_type": "required|optional",
  "failure_policy": "block_parent|continue_with_warning|cancel_children",
  "status": "created|dispatched|running|completed|failed|cancelled",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "result_ref": null,
  "child_gate_result": null
}
```

### Relationship Types

| Type | Description | Impact on Parent |
|------|-------------|------------------|
| `required` | Child must succeed for parent to complete | Block parent completion if child fails |
| `optional` | Child enhances parent but not required | Parent can complete even if child fails |

### Failure Policies

| Policy | Child Failure Behavior |
|--------|------------------------|
| `block_parent` | Parent enters `blocked_by_child_failure` state |
| `continue_with_warning` | Parent continues, warning recorded |
| `cancel_children` | When parent cancelled, cancel all running children |

---

## Parent Task States (Extended)

| State | Description |
|-------|-------------|
| `waiting_for_children` | Parent paused, waiting for children to complete |
| `collecting_children` | Parent collecting results from completed children |
| `blocked_by_child_failure` | Parent blocked due to required child failure |
| `children_failed` | One or more children failed (non-blocking policy) |

---

## Child Task Lifecycle

### Creation Flow

```
1. Parent task reaches a step that needs child task
2. Parent creates child task via ChildTaskFactory
3. Child task registered in TaskRelationships
4. Child task enters standard step loop (v2 + v3-A)
5. Parent enters waiting_for_children state
```

### Completion Flow

```
1. Child task completes (success or failure)
2. ChildResultCollector captures child artifacts
3. TaskRelationships updated with result_ref
4. Parent notified (state transition)
5. Parent evaluates failure_policy
6. Parent continues or blocks based on policy
```

---

## Child Result Harvesting

### Result Structure

```json
{
  "child_task_id": "task_child_xxx",
  "parent_task_id": "task_parent_xxx",
  "status": "completed|failed|cancelled",
  "artifacts": {
    "summary_path": "artifacts/tasks/task_child_xxx/final/SUMMARY.md",
    "gate_report_path": "artifacts/tasks/task_child_xxx/final/gate_report.json",
    "receipt_path": "artifacts/tasks/task_child_xxx/final/receipt.json"
  },
  "gate_passed": true,
  "failure_class": null,
  "collected_at": "ISO timestamp"
}
```

### What Parent Must Collect

| Item | Required | Purpose |
|------|----------|---------|
| Child status | ✅ | Decision making |
| Child artifacts paths | ✅ | Evidence linking |
| Child gate result | ✅ | Integrity verification |
| Child failure class | If failed | Error classification |

---

## Cascade Failure Handling

### Failure Scenarios

| Scenario | Policy | Parent Action |
|----------|--------|---------------|
| Required child fails | `block_parent` | Enter `blocked_by_child_failure` |
| Optional child fails | `continue_with_warning` | Log warning, continue |
| Parent cancelled | N/A | Cancel all running children |
| Multiple children, one fails | Per-child policy | Evaluate each independently |

### Cascade Cancel Flow

```
1. Parent receives cancel signal
2. Identify all children with status in [created, dispatched, running]
3. For each child:
   a. Set child status to cancelled
   b. Release child's slots and leases
   c. Record cancellation in child's ledger
4. Record cascade cancel in parent's ledger
5. Parent enters cancelled state
```

---

## Parent Completion Gate

### Pre-Completion Checks

Before parent can complete:

1. **All required children must be completed**
   - Status in [completed, failed, cancelled]
   - No children in [pending, running]

2. **Required child artifacts must exist**
   - SUMMARY.md path exists
   - gate_report.json path exists
   - receipt.json path exists

3. **Required child gates must pass**
   - `gate_report.all_passed = true` for each required child

4. **Failure policy compliance**
   - If any required child failed with `block_parent`: parent CANNOT complete
   - If optional child failed: warning must be recorded

5. **No orphaned children**
   - All children accounted for in relationships table

### Gate Structure

```json
{
  "gate": "parent_completion",
  "checks": [
    {
      "check": "all_required_children_completed",
      "passed": true,
      "details": "2/2 required children completed"
    },
    {
      "check": "required_child_artifacts_exist",
      "passed": true,
      "details": "All artifact paths verified"
    },
    {
      "check": "required_child_gates_passed",
      "passed": true,
      "details": "All required child gates passed"
    },
    {
      "check": "no_blocking_child_failures",
      "passed": true,
      "details": "No required child failures with block_parent policy"
    }
  ],
  "all_passed": true
}
```

---

## Integration with v2/v3-A

### What Changes

- Parent task can create child tasks
- Parent task has extended states
- New relationship and result schemas
- Completion gate includes child checks

### What Stays Same

- v2 step loop mechanics
- v3-A scheduler admission control
- Gate integrity rules
- Evidence/receipt consistency

### Child Task Execution

Child tasks use the **exact same execution path** as standalone tasks:

1. Load task_state / step_packet
2. CHECK slot availability (v3-A)
3. ACQUIRE slot (v3-A)
4. ACQUIRE lease (v2)
5. EXECUTE step (v2)
6. WRITE result/evidence (v2)
7. RELEASE slot/lease (v3-A/v2)

No special handling for child tasks in the executor.

---

## Persistence Requirements

### Task Relationships File

Path: `artifacts/tasks/{parent_task_id}/relationships.json`

```json
{
  "parent_task_id": "task_parent_xxx",
  "children": [
    {
      "relationship_id": "rel_001",
      "child_task_id": "task_child_a",
      "relation_type": "required",
      "failure_policy": "block_parent",
      "status": "completed",
      "result_ref": "artifacts/tasks/task_child_a/final/SUMMARY.md"
    },
    {
      "relationship_id": "rel_002",
      "child_task_id": "task_child_b",
      "relation_type": "optional",
      "failure_policy": "continue_with_warning",
      "status": "running",
      "result_ref": null
    }
  ],
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

### Child Results File

Path: `artifacts/tasks/{parent_task_id}/child_results.json`

```json
{
  "parent_task_id": "task_parent_xxx",
  "collected_results": [
    {
      "child_task_id": "task_child_a",
      "status": "completed",
      "gate_passed": true,
      "artifacts": {
        "summary_path": "...",
        "gate_report_path": "...",
        "receipt_path": "..."
      },
      "collected_at": "ISO timestamp"
    }
  ]
}
```

---

## Breaking Conditions for v3-B

The following would break v3-B integrity:

1. Parent completing while required child still running
2. Parent completing without collecting all required child results
3. Parent ignoring child failure with `block_parent` policy
4. Child task not going through v3-A scheduler
5. Orphaned children (not tracked in relationships)
6. Child result only in memory/chat, not persisted

---

## Non-Goals for v3-B

- Multi-level nested child tasks (grandchildren)
- Cross-repository parent-child relationships
- Complex DAG orchestration
- Priority-based child scheduling
- Notification/progress push to external systems
- Parallel child execution optimization

---

## Pilot Task Suggestion

**Parent Task**: `pilot_v3b_docs_index_with_children`

**Description**: Update docs index with child-scanned categories

**Child Tasks**:
- Child A (required): Scan docs directory and categorize files
- Child B (optional): Validate index file integrity

**Failure Policy Test**:
- Child A: `block_parent` (required)
- Child B: `continue_with_warning` (optional)

**Verification**:
- Parent waits for both children
- Parent collects results from both
- If Child B fails, parent continues with warning
- Parent completion gate includes child checks

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v3-B.0 | 2026-03-15 | Initial parent-child orchestration design |
