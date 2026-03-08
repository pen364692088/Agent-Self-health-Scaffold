# Natural Trigger Evidence Template

**Purpose**: 首个自然 trigger 出现后，快速填值封板

---

## Step 4: Trigger Capture

**When**: budget_ratio >= 0.85 + assemble phase

```yaml
trigger_timestamp: "___"
session_id: "___"
trigger_type: natural

# Core Evidence
trigger_ratio: ___
pre_assemble_compliant: yes / no
post_compression_ratio: ___

# Safety
safety_counters_remained_zero: yes / no
real_reply_corruption_count: 0
active_session_pollution_count: 0

# Compression
compression_gain_percent: ___
capsule_size_tokens: ___
```

---

## Step 5: Evidence Package

```yaml
evidence_package:
  counter_snapshot_before: "path/to/before.json"
  counter_snapshot_after: "path/to/after.json"
  budget_before: "path/to/budget_before.json"
  budget_after: "path/to/budget_after.json"
  guardrail_event: "path/to/guardrail.json"
  capsule_metadata: "path/to/capsule.json"
  session_note: "path/to/note.md"
```

---

## Step 6: Declaration

```markdown
## Natural Traffic Validation: PASSED

**Date**: [timestamp]
**Natural Triggers**: 1
**First Natural Trigger Ratio**: [value]
**Compression Result**: [before] → [after] ([gain]%)
**Safety**: All zeros
**Evidence Package**: [link]

---

## Timing Analysis

- Distance from hot zone entry to trigger: [turns/time]
- Natural growth rate: [ratio per turn]
- Compression timing: appropriate / early / late

---

## Evidence Integrity

- [ ] Counter before/after captured
- [ ] Budget before/after captured
- [ ] Guardrail event logged
- [ ] Capsule preserved
- [ ] Session note attached
- [ ] All timestamps consistent

---

## Conclusion

Default 100k configuration produces natural trigger at reasonable timing.
Light Enforced mechanism validated for production readiness.

**Milestone B**: COMPLETE
```

---

## Quick Fill Checklist

When trigger occurs, fill in order:

1. [ ] Trigger ratio
2. [ ] Pre-assemble compliant
3. [ ] Post-compression ratio
4. [ ] Safety counters zero
5. [ ] Compression gain
6. [ ] Evidence paths
7. [ ] Timestamps
8. [ ] Declare PASSED

---

*Template ready: 2026-03-08T00:07:00-06:00*
