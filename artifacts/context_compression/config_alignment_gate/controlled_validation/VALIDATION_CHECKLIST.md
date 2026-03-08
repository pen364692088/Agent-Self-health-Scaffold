# Context Compression - Complete Validation Checklist

## Phase C Validation Complete Checklist

### Pre-Validation Checklist

Before starting Phase C validation:

- [ ] Configuration verified
  - [ ] contextWindow = 200000
  - [ ] threshold_enforced = 0.85
  - [ ] threshold_strong = 0.92
  - [ ] mode = light_enforced
- [ ] Tools tested
  - [ ] context-budget-check --test passed
  - [ ] context-compress --test passed
  - [ ] prompt-assemble --test passed
- [ ] Evidence directory prepared
  - [ ] Directory exists
  - [ ] Permissions correct
  - [ ] Sufficient space
- [ ] Kill switch available
  - [ ] Kill switch file location known
  - [ ] Activation procedure documented
  - [ ] Deactivation procedure documented

### Milestone 1: Observe Zone (< 0.75)

- [x] Started in observe zone
- [x] State: idle
- [x] Trace mode: LOW
- [x] Budget ratio tracked
- [x] No compression triggered

**Evidence**:
- [x] Initial trace entries logged
- [x] Budget checks recorded
- [x] State machine at idle

### Milestone 2: Candidate Zone Entry (0.75)

- [ ] Ratio reaches 0.75
- [ ] State transitions: idle → candidate
- [ ] Trace mode switches: LOW → HIGH
- [ ] State transition logged
- [ ] Distance to 0.85 tracked

**Evidence**:
- [ ] Trace entry at 0.75
- [ ] State transition event
- [ ] Mode change logged

### Milestone 3: Trigger Zone Entry (0.85)

- [ ] Ratio reaches 0.85
- [ ] State transitions: candidate → pending
- [ ] Trace mode switches: HIGH → MAXIMUM
- [ ] Guardrail 2A activates
- [ ] Three things verified simultaneously:
  - [ ] Guardrail 2A hit
  - [ ] action_taken = forced_standard_compression
  - [ ] pre_assemble_compliant = yes

**Evidence**:
- [ ] Trace entry at 0.85
- [ ] State transition event
- [ ] Guardrail event logged
- [ ] Pre-compression evidence captured

### Milestone 4: Compression Execution

- [ ] Compression triggered
- [ ] Eviction plan created
- [ ] Capsules generated
- [ ] State updated atomically
- [ ] Post-compression ratio < 0.75

**Evidence**:
- [ ] Compression event ID
- [ ] Eviction plan documented
- [ ] Capsule metadata captured
- [ ] State update verified

### Milestone 5: Post-Compression Validation

- [ ] Post-compression ratio verified < 0.75
- [ ] Safety counters remain zero
- [ ] Evidence package complete
- [ ] All files present
- [ ] Timestamps consistent
- [ ] Counter deltas correct
- [ ] Budget changes valid

**Evidence**:
- [ ] counter_before.json
- [ ] counter_after.json
- [ ] budget_before.json
- [ ] budget_after.json
- [ ] guardrail_event.json
- [ ] capsule_metadata.json

### Final Validation

- [ ] All milestones completed
- [ ] All evidence collected
- [ ] All criteria met:
  - [ ] Trigger at 0.85 (not 0.92)
  - [ ] Guardrail 2A hit
  - [ ] forced_standard_compression executed
  - [ ] pre_assemble_compliant = yes
  - [ ] post_compression_ratio < 0.75
  - [ ] Safety counters = 0
  - [ ] Evidence package complete

- [ ] Phase C result: PASS

---

## Key Understanding Reminders

### What This Is NOT

- ❌ NOT "快收尾" - This is not the end
- ❌ NOT skipping validation steps
- ❌ NOT using natural samples as controlled samples
- ❌ NOT mixing L2 fixes with main line

### What This IS

- ✅ Controlled validation of aligned runtime policy
- ✅ Verification that 0.85 triggers correctly
- ✅ Evidence-based validation
- ✅ Prerequisite for Phase D (Natural Validation)

### Critical Success Factors

1. **Threshold Precision**: Must trigger at exactly 0.85
2. **Timing**: Must execute before prompt assembly
3. **Evidence**: Must capture complete evidence package
4. **Safety**: Must maintain zero safety violations
5. **Documentation**: Must document all steps

---

## Trace Entry Format

Each trace entry should contain:

```json
{
  "timestamp": "ISO8601",
  "phase": "C_milestone_name",
  "context_ratio": 0.XX,
  "estimated_tokens": XXXXX,
  "max_tokens": 200000,
  "compression_state": "state_name",
  "mode": "trace_mode",
  "milestone": "milestone_name",
  "distance_to_next": 0.XX,
  "tokens_to_next": XXXXX
}
```

---

## Evidence Package Validation

### File Existence

All six files must exist:
- [ ] counter_before.json
- [ ] counter_after.json
- [ ] budget_before.json
- [ ] budget_after.json
- [ ] guardrail_event.json
- [ ] capsule_metadata.json

### Timestamp Consistency

- [ ] All timestamps within same session
- [ ] before < after chronologically
- [ ] Reasonable duration (< 60 seconds)

### Counter Deltas

- [ ] enforced_trigger_count: +1
- [ ] budget_check_call_count: +1
- [ ] sessions_over_threshold: +1
- [ ] compression_opportunity_count: +1
- [ ] Safety counters: 0 (no change)

### Budget Changes

- [ ] before.ratio >= 0.85
- [ ] after.ratio < 0.75
- [ ] Token reduction reasonable (10-60%)

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:22:00-06:00
