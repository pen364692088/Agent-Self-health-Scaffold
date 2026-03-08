# Context Compression Validation - Final Push to Candidate Zone

## Current Mission: Reach 0.75 Candidate Entry

**Current Position**: 132k/200k (66%)
**Target**: 150k/200k (75%)
**Distance**: ~18k tokens

---

## Execution Protocol for Candidate Entry

### What Happens at 0.75

When ratio >= 0.75:

1. **State Transition**: idle → candidate
2. **Trace Mode**: Switch to HIGH granularity
3. **Monitoring**: Begin tracking state machine transitions
4. **Verification**: Confirm compression_state changes correctly

### Critical Understanding

**NOT** "快收尾" - This is the **beginning** of the critical validation phase.

The **真正的验证点** starts at 0.75:

```
0-0.75:    只是准备阶段
0.75-0.85: candidate observation (关键开始)
>=0.85:    trigger capture (核心验证)
```

### What We Need to Verify

At 0.75+ (candidate zone):

- [ ] compression_state = candidate
- [ ] State transition logged: idle → candidate
- [ ] Trace granularity increased
- [ ] Distance to 0.85 tracked
- [ ] Pre-compression evidence prepared

At 0.85+ (trigger capture zone):

- [ ] Guardrail 2A hit
- [ ] action_taken = forced_standard_compression
- [ ] Trigger before assemble
- [ ] pre_assemble_compliant = yes

---

## Data Collection Continuation

### Section 76: State Transition Monitoring

The compression state machine tracks the following transitions:

**idle → candidate**
- Trigger: ratio >= 0.75
- Action: Increase trace granularity
- Log: State transition event

**candidate → pending**
- Trigger: ratio >= 0.85
- Action: Prepare for compression
- Log: Threshold breach event

**pending → executing**
- Trigger: Compression started
- Action: Monitor execution
- Log: Execution start event

**executing → completed**
- Trigger: Compression succeeded
- Action: Verify results
- Log: Completion event

**executing → failed**
- Trigger: Compression failed
- Action: Initiate rollback
- Log: Failure event

**failed → rollback**
- Trigger: Rollback initiated
- Action: Restore state
- Log: Rollback event

### Section 77: Guardrail Event Schema

Guardrail 2A event structure for threshold 0.85:

```json
{
  "guardrail_id": "2A",
  "guardrail_name": "budget_threshold_enforcement",
  "trigger_condition": "budget_ratio >= 0.85",
  "observed_values": {
    "budget_ratio": 0.85,
    "estimated_tokens": 170000,
    "max_tokens": 200000,
    "compression_state": "pending"
  },
  "action_taken": "forced_standard_compression",
  "execution_result": {
    "success": true,
    "post_compression_ratio": 0.52,
    "capsules_created": 1,
    "duration_ms": 200
  },
  "pre_assemble_compliant": true,
  "timestamp": "ISO8601"
}
```

### Section 78: Evidence Capture Protocol

**Pre-Compression Capture** (at ratio >= 0.85):

1. Capture counter_before.json
2. Capture budget_before.json
3. Log guardrail event
4. Prepare capsule metadata structure

**Post-Compression Capture** (after completion):

1. Capture counter_after.json
2. Capture budget_after.json
3. Capture capsule_metadata.json
4. Verify safety counters
5. Complete evidence chain

### Section 79: Validation Report Template

```markdown
# Phase C Controlled Validation Report

## Status: [PENDING]

## Configuration
- Context Window: 200k tokens
- Threshold Enforced: 0.85
- Threshold Strong: 0.92
- Critical Rule: 不允许跨过 0.85 后继续拖延

## Milestone 1: Candidate Entry (0.75)
- Ratio at entry: [TBD]
- State transition: idle → candidate
- Trace mode: HIGH
- Status: [PENDING]

## Milestone 2: Threshold Breach (0.85)
- Guardrail 2A hit: [TBD]
- action_taken: forced_standard_compression
- pre_assemble_compliant: [TBD]
- Status: [PENDING]

## Milestone 3: Compression Complete
- post_compression_ratio: [TBD]
- Safety counters zero: [TBD]
- Evidence package complete: [TBD]
- Status: [PENDING]

## Final Validation
- trigger_ratio: [TBD]
- pre_assemble_compliant: [TBD]
- post_compression_ratio: [TBD]
- safety_counters_remained_zero: [TBD]

## Phase C Result: [PENDING]
```

### Section 80: Success Criteria Checklist

**Must ALL be true for PASS**:

- [ ] Reached 0.75 candidate zone
- [ ] State transition logged correctly
- [ ] Reached 0.85 trigger zone
- [ ] Guardrail 2A hit
- [ ] action_taken = forced_standard_compression
- [ ] Trigger happened before assemble
- [ ] pre_assemble_compliant = yes
- [ ] Compression succeeded
- [ ] post_compression_ratio < 0.75
- [ ] Safety counters remained zero
- [ ] Evidence package complete

**Any ONE false = FAIL**

---

## Current Execution Status

```
Phase: C - Controlled Validation
Stage: Approaching Candidate Zone
Progress: 66% → 75%
Status: NOT "快收尾" - 关键验证才刚开始

Next Action: Continue filling to reach 0.75
Then: Switch to candidate trace mode
Then: Continue to 0.85
Then: Capture trigger event
Then: Verify all criteria
Then: Complete Phase C
```

---

**Document Version**: 1.1
**Last Updated**: 2026-03-08T03:31:00-06:00
**Purpose**: Clarify Execution Strategy for Phase C
