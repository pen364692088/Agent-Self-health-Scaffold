# Phase 2 Report: Trigger Policy + Cooldown/Hysteresis

**Date**: 2026-03-09
**Phase**: 2 of 6
**Status**: ✅ Complete

---

## Deliverables

| Deliverable | Status | Location |
|-------------|--------|----------|
| AUTO_COMPACTION_POLICY.md | ✅ Created | docs/context_compression/ |
| COMPACTION_BLOCKERS.md | ✅ Created | docs/context_compression/ |
| trigger-policy | ✅ Created | tools/ |
| 02_TRIGGER_POLICY_REPORT.md | ✅ Created | docs/context_compression/ |

---

## Acceptance Criteria Verification

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Normal trigger rule defined (ratio >= 0.80) | ✅ Pass | AUTO_COMPACTION_POLICY.md, trigger-policy self-test |
| 2 | Emergency trigger rule defined (ratio >= 0.90) | ✅ Pass | AUTO_COMPACTION_POLICY.md, trigger-policy self-test |
| 3 | Cooldown mechanism defined | ✅ Pass | AUTO_COMPACTION_POLICY.md § Cooldown |
| 4 | Hysteresis logic defined | ✅ Pass | AUTO_COMPACTION_POLICY.md § Hysteresis, zone_classification test |
| 5 | Blockers documented with detection methods | ✅ Pass | COMPACTION_BLOCKERS.md, BlockerDetector class |
| 6 | trigger-policy tool works (self-test passes) | ✅ Pass | 10/10 tests pass |

---

## Implementation Summary

### 1. AUTO_COMPACTION_POLICY.md

**Key Features**:
- Normal compression: trigger at 0.80, target 0.55-0.65
- Emergency compression: trigger at 0.90, target 0.45-0.55
- Cooldown intervals: 30 min (normal), 15 min (emergency)
- Hysteresis: 5% buffer for zone transitions

**Decision Flow**:
```
ratio >= 0.90 → EMERGENCY (bypass blockers if allowed)
ratio >= 0.80 → Check blockers → NORMAL or BLOCKED
ratio < 0.80  → NO ACTION
```

### 2. COMPACTION_BLOCKERS.md

**Blocker Categories**:
- STATE: Unpersisted data (working buffer, open loops, tool state)
- GIT: Uncommitted changes, immature branches
- WFLOW: Critical gates, subagent tasks, user interactions
- TIME: Cooldown period
- CRIT: Operations that cannot be interrupted

**Detection Implementation**:
- Each blocker has a Python detection function
- Severity levels: critical, high, medium, low
- Bypass conditions defined per blocker
- Critical blockers (no bypass): Gate in progress, Critical operation

### 3. trigger-policy Tool

**Usage**:
```bash
# Basic usage
trigger-policy --ratio 0.82

# With JSON output
trigger-policy --ratio 0.82 --json

# With blocker detection
trigger-policy --ratio 0.82 --detect-blockers

# Force bypass (emergency)
trigger-policy --ratio 0.92 --force

# Self-test
trigger-policy --test

# Health check
trigger-policy --health
```

**Output Format**:
```json
{
  "timestamp": "...",
  "ratio": 0.82,
  "zone": "warning",
  "action": "normal",
  "reason": "ratio_threshold_exceeded",
  "blockers": [],
  "cooldown": {"active": false, "remaining_seconds": 0},
  "target_ratio": 0.60
}
```

**Self-Test Results**:
| Test | Status |
|------|--------|
| zone_classification | ✅ Pass |
| normal_trigger | ✅ Pass |
| emergency_trigger | ✅ Pass |
| below_threshold | ✅ Pass |
| blocked_by_blockers | ✅ Pass |
| emergency_with_bypassable_blockers | ✅ Pass |
| critical_blocker_no_bypass | ✅ Pass |
| force_bypass | ✅ Pass |
| cooldown_state | ✅ Pass |
| blocker_detection | ✅ Pass |

**Total**: 10/10 tests pass

---

## Integration Points

### Phase 1 Integration
- Uses `context-budget-watcher` output (ratio, zone, trend)
- Reads cooldown state from `artifacts/context_compression/cooldown_state.json`

### Phase 3 Preparation
- Output feeds into executor decision
- `action` field determines executor behavior
- `target_ratio` guides compression depth
- `blockers` list informs pre-compression steps

---

## Technical Details

### Hysteresis Thresholds

| Transition | Threshold | Purpose |
|------------|-----------|---------|
| Normal → Warning | 0.80 | Trigger threshold |
| Warning → Normal | 0.75 | Exit with buffer |
| Warning → Emergency | 0.90 | Escalation |
| Emergency → Warning | 0.85 | Exit with buffer |

### Cooldown Intervals

| Mode Pair | Interval |
|-----------|----------|
| Normal → Normal | 30 minutes |
| Emergency → Normal | 15 minutes |
| Emergency → Emergency | 10 minutes |

### Blocker Severities

| Severity | Emergency Bypass | Force Flag Bypass |
|----------|------------------|-------------------|
| critical | No | No |
| high | Yes | Yes |
| medium | Yes | Yes |
| low | Yes | Yes |

---

## Edge Cases Handled

1. **Ratio exactly at threshold**: Triggers action (>= comparison)
2. **Cooldown file missing**: Treats as no cooldown
3. **Critical blocker during emergency**: Blocks compression
4. **Force flag with critical blocker**: Still blocked
5. **Empty blockers list**: Proceeds with compression
6. **Multiple blockers**: All reported, highest severity determines

---

## Files Created

```
docs/context_compression/
├── AUTO_COMPACTION_POLICY.md    (trigger rules, cooldown, hysteresis)
├── COMPACTION_BLOCKERS.md       (blocker definitions, detection)
└── 02_TRIGGER_POLICY_REPORT.md  (this report)

tools/
└── trigger-policy               (decision engine CLI)
```

---

## Next Steps (Phase 3)

1. **Executor Implementation**: Implement compaction execution logic
2. **Handoff Protocol**: Define state preservation during compaction
3. **Integration Testing**: Test full pipeline with real sessions
4. **Error Recovery**: Handle failed compressions gracefully

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-09 | Phase 2 complete |
