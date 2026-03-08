# Context Compression - Complete System Behavior Documentation

## System Behavior at Each Phase

### Phase 1: Observe Phase (ratio < 0.75)

**System State**: Idle
**Trace Mode**: LOW
**Actions**: Monitor only

**What Happens**:
- Budget check runs on each message
- Ratio calculated and logged
- No compression actions taken
- System waits for threshold crossing

**Trace Output**:
```json
{
  "ratio": 0.65,
  "state": "idle",
  "mode": "observe",
  "action": "monitor"
}
```

### Phase 2: Candidate Phase (0.75 <= ratio < 0.85)

**System State**: Candidate
**Trace Mode**: HIGH
**Actions**: Prepare for compression

**What Happens**:
- Budget check frequency increases
- State transitions logged
- Evidence preparation begins
- System primes for trigger

**Trace Output**:
```json
{
  "ratio": 0.80,
  "state": "candidate",
  "mode": "HIGH",
  "action": "prepare",
  "distance_to_trigger": 0.05
}
```

### Phase 3: Trigger Phase (ratio >= 0.85)

**System State**: Pending
**Trace Mode**: MAXIMUM
**Actions**: Execute compression

**What Happens**:
- Guardrail 2A activates
- Compression decision made
- Eviction plan created
- Capsules generated
- State updated
- Evidence captured

**Trace Output**:
```json
{
  "ratio": 0.85,
  "state": "pending",
  "mode": "MAXIMUM",
  "action": "compress",
  "guardrail_id": "2A",
  "transition": "candidate→pending"
}
```

### Phase 4: Compression Execution

**System State**: Executing
**Trace Mode**: MAXIMUM
**Actions**: Execute eviction and capsule generation

**What Happens**:
- Eviction plan executed
- Turns removed from context
- Capsules generated for evicted content
- Session state updated
- Evidence package created

**Trace Output**:
```json
{
  "state": "executing",
  "eviction_plan": {
    "turns_to_evict": 50,
    "preserve_count": 50
  },
  "capsules_created": 1,
  "duration_ms": 200
}
```

### Phase 5: Completion Phase

**System State**: Completed
**Trace Mode**: HIGH → LOW
**Actions**: Verify and return to observe

**What Happens**:
- Post-compression ratio verified
- Safety counters checked
- Evidence validated
- State returns to idle

**Trace Output**:
```json
{
  "state": "completed",
  "post_ratio": 0.52,
  "safety_counters": {
    "real_reply_corruption": 0,
    "active_session_pollution": 0
  },
  "transition": "completed→idle"
}
```

---

## State Transition Summary

```
idle (ratio < 0.75)
  ↓ [ratio >= 0.75]
candidate (0.75 <= ratio < 0.85)
  ↓ [ratio >= 0.85]
pending (ratio >= 0.85)
  ↓ [compression started]
executing
  ↓ [success]
completed
  ↓ [ratio < 0.75]
idle

Or on failure:
executing
  ↓ [error]
failed
  ↓ [recovery]
rollback
  ↓ [restored]
idle
```

---

## Evidence Collection Timeline

### At Trigger (ratio >= 0.85)
1. Capture counter_before.json
2. Capture budget_before.json
3. Log guardrail_event.json (started)

### During Compression
4. Log eviction plan
5. Log capsule generation
6. Track duration

### After Compression
7. Capture counter_after.json
8. Capture budget_after.json
9. Capture capsule_metadata.json
10. Complete guardrail_event.json

### Validation
11. Verify all files present
12. Verify timestamps consistent
13. Verify counter deltas correct
14. Verify budget changes valid

---

## Critical Rule Enforcement

**Rule**: 不允许跨过 0.85 后继续拖延

**Enforcement Mechanism**:
1. At ratio >= 0.85, guardrail activates
2. Compression decision is mandatory
3. No skip or delay allowed
4. Must execute before prompt assembly

**Violation Detection**:
- If ratio > 0.85 without compression: Alert
- If prompt assembled without compression: Error
- If state remains pending too long: Warning

**Correct Behavior**:
- Ratio crosses 0.85
- State becomes pending
- Compression executes immediately
- State becomes completed
- Ratio falls below 0.75

---

## Performance at Each Phase

### Observe Phase Performance
- Budget check: < 100ms
- Trace overhead: < 10ms
- Total: < 110ms

### Candidate Phase Performance
- Budget check: < 100ms
- Trace overhead: < 20ms (increased)
- Total: < 120ms

### Trigger Phase Performance
- Budget check: < 100ms
- Guardrail check: < 10ms
- Compression: < 500ms
- Evidence capture: < 50ms
- Total: < 660ms

### Total Pipeline Performance
- Minimum: < 200ms
- Typical: < 400ms
- Maximum: < 700ms

---

## Safety Monitoring Throughout

### Continuous Safety Checks

**Check 1: Kill Switch**
- Frequency: Every operation
- Action: Block if active
- Alert: On activation

**Check 2: Safety Counters**
- Frequency: Every compression
- Action: Alert if non-zero
- Recovery: Investigate immediately

**Check 3: Scope Filter**
- Frequency: Every session
- Action: Exclude if high-risk
- Log: All exclusions

**Check 4: Evidence Integrity**
- Frequency: After each capture
- Action: Validate immediately
- Recovery: Re-capture if invalid

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:14:00-06:00
**Purpose**: Complete System Behavior Documentation
