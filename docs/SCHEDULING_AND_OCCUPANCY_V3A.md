# Checkpointed Step Loop v3-A - Scheduling and Occupancy Control

## Overview

This document defines the scheduling and occupancy control layer for Checkpointed Step Loop v3-A, built on top of the frozen v2 baseline.

## Core Principle

**v3-A is an incremental scheduling layer, not a replacement for v2.**

All v2 baseline protections remain in force:
- SUMMARY.md is required
- Gate integrity rules apply
- Successful steps must not be re-executed
- Receipt/gate_report consistency is enforced

---

## Worker Slot Registry

### Slot States

| State | Description |
|-------|-------------|
| `free` | Available for allocation |
| `reserved` | Reserved by a scheduler for upcoming step |
| `running` | Currently executing a step |
| `stale` | Running but heartbeat expired |

### Slot Structure

```json
{
  "slot_id": "slot_001",
  "status": "free|reserved|running|stale",
  "holder": {
    "task_id": "task_xxx",
    "step_id": "S01",
    "worker_id": "worker_1"
  },
  "reserved_at": "ISO timestamp",
  "started_at": "ISO timestamp",
  "last_heartbeat_at": "ISO timestamp",
  "timeout_seconds": 300
}
```

### Slot Lifecycle

```
free → reserved → running → free
                  ↓
                stale → free (reclaim)
```

---

## Scheduler Admission Control

### Execution Sequence (Enhanced)

```
1. Load task_state / step_packet
2. CHECK slot availability    ← NEW
3. ACQUIRE slot               ← NEW
4. ACQUIRE lease              ← v2
5. EXECUTE step               ← v2
6. WRITE result/evidence      ← v2
7. RELEASE slot or heartbeat  ← NEW
8. RELEASE lease              ← v2
```

### Admission Rules

1. **No slot, no execution**: Step cannot start without available slot
2. **No lease, no execution**: Step cannot start without valid lease
3. **Both required**: A running step must hold both slot and lease

### Admission Decision

```json
{
  "decision": "admit|reject|queue",
  "reason": "slot_available|no_slot|lease_conflict|...",
  "allocated_slot": "slot_001",
  "queue_position": null,
  "estimated_wait_seconds": null
}
```

---

## Slot + Lease Consistency

### Invariant

A `running` step must have:
- ✅ Valid slot (not free, not stale without reclaim)
- ✅ Valid lease (not expired)

### Reclaim Rules

Before reclaiming a slot/lease:

1. **Check step status**:
   - If `success`: **BLOCK reclaim** (v2 baseline protection)
   - If `running`: Check heartbeat/timeout
   - If `failed_retryable`: Allow reclaim for retry

2. **Check both slot and lease**:
   - Both stale → reclaim both
   - Only one stale → investigate inconsistency

3. **Record reclaim event** in ledger

### Reclaim Protection for Success Steps

```python
def can_reclaim(step_id, task_id):
    step_status = get_step_status(step_id, task_id)
    
    if step_status == "success":
        # v2 baseline: successful steps must not be re-executed
        return False, "step_already_success"
    
    slot = get_slot_for_step(step_id)
    lease = get_lease_for_step(step_id)
    
    if slot.is_stale() and lease.is_expired():
        return True, "both_stale"
    
    return False, "conditions_not_met"
```

---

## Conflict Avoidance

### Conflict Types

| Type | Description | Resolution |
|------|-------------|------------|
| Step contention | Two workers try same step | First wins, second rejected |
| Slot contention | Two steps need same slot | Queue or priority |
| Resource contention | Same file/resource | Detect and block |

### Conflict Detection

1. **Step contention**: Use lease as mutex
2. **Slot contention**: Use slot registry as mutex
3. **Resource contention**: Track resource locks

### Conflict Resolution

```python
def resolve_step_contention(step_id, worker_a, worker_b):
    lease_a = try_acquire_lease(step_id, worker_a)
    
    if lease_a.success:
        return worker_a, "lease_acquired"
    else:
        # worker_b already has lease
        return worker_b, "already_running"
```

---

## Minimum Fairness

### Simple FIFO Rule

When multiple steps are ready to run:
1. Sort by `created_at` ascending
2. Process in order
3. Skip steps whose dependencies not met

### Anti-Starvation

- No single task can occupy all slots for extended time
- After N seconds, slot may be reclaimed if heartbeat missing
- Priority field optional, default is FIFO

### Fairness Guarantee

```python
def get_next_runnable_step(task_id, available_slots):
    pending_steps = get_pending_steps(task_id)
    
    # FIFO order
    pending_steps.sort(key=lambda s: s.created_at)
    
    # Check dependencies
    for step in pending_steps:
        if dependencies_met(step):
            return step
    
    return None
```

---

## Hard Fail vs Soft Fail

### Hard Fail (Block Execution)

- No available slot
- Lease conflict
- Step already success (reclaim attempt)
- Resource locked by another step

### Soft Fail (Warn but Allow)

- Slot nearly full (warning threshold)
- Lease nearly expired
- Non-critical resource contention

---

## Evidence and Receipt Integration

### Slot/Lease in Evidence

Every step execution must record:
- `slot_id` used
- `lease_id` acquired
- Slot allocation timestamp
- Lease acquisition timestamp

### Receipt Enhancement

```json
{
  "step_id": "S01",
  "execution_type": "execute_shell",
  "status": "success",
  "slot": {
    "slot_id": "slot_001",
    "allocated_at": "ISO timestamp",
    "released_at": "ISO timestamp"
  },
  "lease": {
    "lease_id": "...",
    "acquired_at": "ISO timestamp",
    "released_at": "ISO timestamp"
  }
}
```

---

## Breaking Conditions for v3-A

The following would break v3-A integrity:

1. Reclaiming slot/lease for a success step
2. Running step without slot or lease
3. Double allocation of same slot
4. Gate passing with missing slot/lease evidence

---

## Non-Goals for v3-A

- Full multi-worker parallel execution
- Cross-repository task dependencies
- Notification/progress push
- Complex priority scheduling
- Load balancing optimization

---

## Integration with v2 Baseline

### What Changes
- Step execution must go through scheduler
- Evidence includes slot/lease info
- New conflict handling layer

### What Stays Same
- Task dossier structure
- Step packet format
- Gate rules
- "No re-execution of success steps"
- Receipt/gate_report consistency requirements

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v3-A.0 | 2026-03-15 | Initial scheduling layer design |
