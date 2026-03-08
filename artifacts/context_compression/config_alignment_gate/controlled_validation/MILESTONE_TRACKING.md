# Context Compression Validation Data - Phase C Milestones

## Milestone Tracking

### Current Position: Observe Zone (65%)

```
Position: 131k/200k (0.65)
Zone: observe
Next Milestone: 0.75 (candidate entry)
Distance: 0.10 ratio points (~19k tokens)
```

### Milestone 1: Candidate Entry (0.75)

**Trigger Condition**: budget_ratio >= 0.75

**Expected State Transition**: idle → candidate

**Trace Mode Switch**: LOW → HIGH granularity

**Actions**:
- Log state transition event
- Increase trace frequency to every turn
- Verify compression_state = candidate
- Monitor distance to 0.85

**Required Evidence**:
```json
{
  "milestone": "candidate_entry",
  "ratio": 0.75,
  "timestamp": "ISO8601",
  "state_transition": "idle → candidate",
  "trace_mode": "HIGH"
}
```

### Milestone 2: Threshold Breach (0.85)

**Trigger Condition**: budget_ratio >= 0.85

**Expected State Transition**: candidate → pending

**Trace Mode Switch**: HIGH → MAXIMUM granularity

**Actions**:
- Log state transition event
- Capture counter_before.json
- Capture budget_before.json
- Prepare trigger capture
- Monitor for forced_standard_compression

**Required Evidence**:
```json
{
  "milestone": "threshold_085",
  "ratio": 0.85,
  "timestamp": "ISO8601",
  "state_transition": "candidate → pending",
  "trace_mode": "MAXIMUM",
  "evidence_captured": {
    "counter_before": "path",
    "budget_before": "path"
  }
}
```

### Milestone 3: Compression Execution

**Trigger Condition**: Compression initiated

**Expected State Transition**: pending → executing

**Actions**:
- Monitor eviction plan
- Track capsule generation
- Measure duration
- Capture post-compression state

**Required Evidence**:
```json
{
  "milestone": "compression_execution",
  "state_transition": "pending → executing",
  "eviction_plan": {
    "turns_to_evict": 50,
    "capsules_to_create": 1
  },
  "duration_ms": "TBD"
}
```

### Milestone 4: Compression Complete

**Trigger Condition**: Compression finished successfully

**Expected State Transition**: executing → completed

**Actions**:
- Verify post_compression_ratio < 0.75
- Capture counter_after.json
- Capture budget_after.json
- Capture guardrail_event.json
- Capture capsule_metadata.json
- Verify safety_counters = 0

**Required Evidence**:
```json
{
  "milestone": "compression_complete",
  "state_transition": "executing → completed",
  "post_compression_ratio": "TBD",
  "safety_counters_zero": true,
  "evidence_package_complete": true
}
```

### Milestone 5: Validation Passed

**Trigger Condition**: All milestones completed

**Pass Criteria**:
1. ✅ Trigger at 0.85 (not 0.92)
2. ⏳ pre_assemble_compliant = yes
3. ⏳ Compression succeeded
4. ⏳ Safety counters = 0
5. ⏳ Evidence package complete

**Final Report Fields**:
```json
{
  "trigger_ratio": 0.85,
  "pre_assemble_compliant": "yes",
  "post_compression_ratio": "TBD",
  "safety_counters_remained_zero": "yes",
  "phase_c_result": "PASS"
}
```

---

## Trace Capture Script

### Observe Zone (current)

```bash
# Low granularity trace
echo '{"timestamp":"...","ratio":0.65,"state":"idle","mode":"observe"}' >> trace.jsonl
```

### Candidate Zone (ratio >= 0.75)

```bash
# High granularity trace
echo '{"timestamp":"...","ratio":0.75,"state":"candidate","mode":"HIGH","transition":"idle→candidate","distance_to_085":0.10}' >> trace.jsonl
```

### Trigger Capture Zone (ratio >= 0.85)

```bash
# Maximum granularity trace
echo '{"timestamp":"...","ratio":0.85,"state":"pending","mode":"MAXIMUM","transition":"candidate→pending","guardrail":"2A"}' >> trace.jsonl

# Capture pre-compression evidence
cp counters.json counter_before.json
cp budget.json budget_before.json
```

---

## Progress Tracking

| Milestone | Ratio | Status | Evidence |
|-----------|-------|--------|----------|
| Observe | 0.65 | ✅ CURRENT | trace.jsonl |
| Candidate Entry | 0.75 | ⏳ PENDING | - |
| Threshold Breach | 0.85 | ⏳ PENDING | - |
| Compression | 0.85+ | ⏳ PENDING | - |
| Complete | <0.75 | ⏳ PENDING | - |

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:25:00-06:00
**Purpose**: Milestone Tracking for Phase C
