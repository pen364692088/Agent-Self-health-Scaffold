# Context Compression - Trigger Zone Preparation

## Understanding the Trigger Zone

The trigger zone (ratio >= 0.85) is where compression becomes mandatory. This is the critical enforcement point defined by the policy:

**Critical Rule**: 不允许跨过 0.85 后继续拖延

### Trigger Zone Definition

**Ratio**: >= 0.85
**State**: pending
**Trace Mode**: MAXIMUM granularity
**Action**: forced_standard_compression

### What Makes 0.85 Special

At 0.85, three things happen simultaneously:

1. **Guardrail 2A Activates**
   - Monitors budget ratio
   - Detects threshold crossing
   - Triggers compression action

2. **State Machine Transitions**
   - From: candidate
   - To: pending
   - Must compress before assemble

3. **Evidence Capture Begins**
   - Pre-compression state captured
   - Guardrail event logged
   - System enters MAX trace mode

### Pre-Assemble Requirement

Compression MUST occur BEFORE prompt assembly:

```
Message Received
    ↓
Budget Check (ratio = 0.85)
    ↓
Guardrail 2A Triggered
    ↓
Compression Executed
    ↓
State Updated
    ↓
Prompt Assembled
    ↓
LLM Called
```

The compression step cannot be skipped or delayed.

### Trigger Zone Behavior

**What Happens**:

1. Budget ratio crosses 0.85
2. State transitions to pending
3. Compression decision made
4. Eviction plan created
5. Capsules generated
6. State updated
7. Evidence captured
8. Prompt assembled with reduced context

**What Does NOT Happen**:

- No waiting until 0.92
- No skipping compression
- No delayed action
- No context overflow

### Verification at Trigger

When compression triggers at 0.85, verify:

**Evidence Fields**:
```json
{
  "trigger_ratio": 0.85,
  "guardrail_id": "2A",
  "action_taken": "forced_standard_compression",
  "pre_assemble_compliant": true,
  "compression_state": "pending→executing→completed"
}
```

**Success Indicators**:
- Trigger ratio is exactly 0.85 (or slightly above)
- Guardrail 2A event logged
- Compression executed
- Post-ratio < 0.75
- Safety counters remain zero

### Trigger Zone Monitoring

In trigger zone, every operation is traced:

**Trace Fields**:
- All candidate fields
- guardrail_id
- trigger_condition
- action_taken
- execution_result
- pre_assemble_compliant
- safety_counters_snapshot

**Trace Frequency**:
- Every operation
- Every state change
- Every evidence capture
- Complete audit trail

### Expected Compression Result

When compression completes at 0.85 trigger:

**Before Compression**:
```
Ratio: 0.85
Tokens: 170k
State: pending
Pressure: standard
```

**After Compression**:
```
Ratio: < 0.75
Tokens: ~100k
State: completed
Pressure: normal
```

**Compression Gain**:
- Token reduction: ~40%
- Turn reduction: ~40%
- Capsules created: 1-2

---

## Preparation Checklist

Before entering trigger zone:

- [x] Candidate zone reached
- [x] State machine tracking active
- [x] Trace mode HIGH
- [x] Evidence directory ready
- [ ] Trigger zone reached
- [ ] Guardrail 2A captured
- [ ] Compression executed
- [ ] Evidence complete

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:13:00-06:00
**Purpose**: Trigger Zone Preparation Documentation
