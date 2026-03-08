# Trace Mode Rules for Phase C

**Locked**: 2026-03-08T03:24:00-06:00

---

## Automatic Trace Mode Switching

### Mode: Observe (ratio < 0.75)

**Current Mode**: ACTIVE (65%)
**Trace Granularity**: LOW (every 5 turns)
**Fields Captured**: ratio, estimated_tokens, pressure_level, turn

### Mode: Candidate (0.75 ≤ ratio < 0.85)

**Trigger**: ratio >= 0.75
**Trace Granularity**: HIGH (every turn)
**Fields Captured**: 
- ratio, estimated_tokens, pressure_level, turn
- compression_state, recommended_action
- distance_to_085, tokens_to_085
- state_transition_event

**Auto-Actions**:
- Log state transition: idle → candidate
- Increase trace frequency
- Verify state machine flow

### Mode: Trigger Capture (ratio >= 0.85)

**Trigger**: ratio >= 0.85
**Trace Granularity**: MAXIMUM (every operation)
**Fields Captured**:
- All candidate fields PLUS:
- guardrail_id, trigger_condition
- action_taken, execution_result
- capsule_id, compression_event_id
- pre_assemble_compliant
- safety_counters_snapshot

**Auto-Actions**:
- Log state transition: candidate → pending
- Capture counter_before.json
- Capture budget_before.json
- Prepare for event capture
- Monitor for executing state

---

## Execution Rules

```
IF ratio >= 0.75 AND ratio < 0.85:
  MODE = candidate
  trace_granularity = HIGH
  log_state_transition("idle", "candidate")

IF ratio >= 0.85:
  MODE = trigger_capture
  trace_granularity = MAXIMUM
  log_state_transition("candidate", "pending")
  capture_pre_compression_evidence()
```

---

## Current Status

```
ratio: 0.65 (observe zone)
next_milestone: 0.75 (candidate entry)
distance: 0.10 (~20k tokens)
```

---

## Next Actions

1. Continue context ramp to 0.75+
2. On reaching 0.75: Switch to candidate trace mode
3. Continue to 0.85+
4. On reaching 0.85: Switch to trigger capture mode
5. Capture forced_standard_compression event
6. Verify pre_assemble_compliant = yes
7. Complete evidence package

---

*Rules locked: 2026-03-08T03:24:00-06:00*
