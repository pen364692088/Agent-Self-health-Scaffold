# Evidence Hot Zone Mechanism

**Purpose**: 预埋自动取证点，确保不丢失首个自然 trigger 证据

---

## Activation Threshold

| Zone | Budget Ratio | Trace Granularity |
|------|--------------|-------------------|
| Normal | < 0.84 | Per-turn summary |
| **Hot Zone** | >= 0.84 | Per-assemble full capture |
| Triggered | >= 0.85 | Complete evidence package |

---

## Auto-Capture Points (Hot Zone)

When budget_ratio >= 0.84, capture on **every assemble**:

### Before Assemble
```
1. counter_snapshot_before.json
2. budget_snapshot_before.json
3. session_note.md
```

### After Assemble (if triggered)
```
4. counter_snapshot_after.json
5. budget_snapshot_after.json
6. guardrail_event.json
7. capsule_metadata.json
8. trigger_report.json
```

---

## Evidence Directory Structure

```
natural_validation/
├── SESSION_ID/
│   ├── evidence_hot_zone/
│   │   ├── turn_N_before_assemble/
│   │   │   ├── counter.json
│   │   │   ├── budget.json
│   │   │   └── session_note.md
│   │   └── turn_N_after_assemble/
│   │       ├── counter.json
│   │       ├── budget.json
│   │       ├── guardrail_event.json
│   │       └── capsule_metadata.json
│   └── first_natural_trigger/
│       ├── complete_evidence_package.zip
│       └── TRIGGER_REPORT.md
```

---

## Critical Timing

**最容易丢失的证据**: 阈值附近那一轮的 before/after

**解决方案**: 
- 进入 hot zone (0.84+) 后，每轮 assemble 前后都自动落盘
- 不等触发后回捞日志

---

## Current State

```
Current Ratio: ~0.825
Hot Zone Threshold: 0.84
Distance: ~0.015

Status: APPROACHING_HOT_ZONE
```

---

*Evidence hot zone defined: 2026-03-07T23:58:00-06:00*
