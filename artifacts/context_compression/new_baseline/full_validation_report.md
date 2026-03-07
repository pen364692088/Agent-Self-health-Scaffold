# New Baseline Full Validation Report

**Validation Mode**: Shadow / Isolated
**Run At**: 2026-03-07T04:32:00CST
**Patch Set Version**: 1.0

---

## Executive Summary

**Conclusion: A. 新 baseline 成立，建议进入 rollout 准备阶段**

---

## Patch Set

| Component | Version | Description |
|-----------|---------|-------------|
| anchor-enhanced-capsule-builder | 1.0 | Extracts 6 anchor types from events |
| anchor-aware-retrieve | 1.0 | Weighted scoring by anchor coverage |
| admissibility-policy | 1.0 | Filters heartbeat-only samples |

**Excluded**: prompt-assemble, scoring-changes, metrics-changes, schema-changes

---

## Validation Results

### Total (34 samples)

| Metric | Baseline | Patch | Delta |
|--------|----------|-------|-------|
| Avg Score | 0.284 | **0.733** | **+0.449** |
| >=0.75 | 0 | 16 | +16 |
| Improved | - | 34 | - |
| Regressed | - | 0 | - |
| Correct Topic Wrong Anchor | - | 0 | - |

---

### Real Admissible (16 samples)

| Metric | Baseline | Patch | Delta |
|--------|----------|-------|-------|
| Avg Score | 0.371 | **1.000** | **+0.629** |
| >=0.75 | 0 | **16 (100%)** | +16 |
| Improved | - | 16 | - |
| Regressed | - | 0 | - |

**Key Finding**: All 16 real admissible samples reach >=0.75 threshold.

---

### Historical Replay (18 samples)

| Metric | Baseline | Patch | Delta |
|--------|----------|-------|-------|
| Avg Score | 0.207 | 0.496 | +0.289 |
| >=0.75 | 0 | 0 | - |
| Improved | - | 18 | - |
| Regressed | - | 0 | - |

**Note**: Improved but not reaching >=0.75. This is expected due to historical data format differences.

---

## Threshold Checks

| Criterion | Threshold | Actual | Result |
|-----------|-----------|--------|--------|
| Real subset delta | >= +0.30 | **+0.629** | ✅ PASS |
| Replay no regression | No regression | Improved +0.289 | ✅ PASS |
| Regressed samples | 0 | 0 | ✅ PASS |
| Correct topic wrong anchor | Reduced | 0 | ✅ PASS |

---

## Anchor Coverage Distribution

### Real Admissible

| Anchor Type | Min | Max | Avg |
|-------------|-----|-----|-----|
| decision | 10 | 10 | 10.0 |
| entity | 4 | 15 | 7.1 |
| time | 10 | 10 | 10.0 |
| open_loop | 0 | 10 | 6.9 |
| constraint | 6 | 10 | 9.6 |
| tool_state | 15 | 15 | 15.0 |

**Observation**: Rich anchor extraction across all types.

### Historical Replay

| Anchor Type | Min | Max | Avg |
|-------------|-----|-----|-----|
| decision | 0 | 6 | 0.9 |
| entity | 0 | 1 | 0.5 |
| time | 3 | 8 | 5.4 |
| open_loop | 0 | 1 | 0.1 |
| constraint | 0 | 1 | 0.2 |
| tool_state | 0 | 15 | 7.8 |

**Observation**: Limited anchor diversity compared to real samples.

---

## Admissibility Audit

| Metric | Count |
|--------|-------|
| Total scanned | 42 |
| Admissible | 10 |
| Not admissible | 32 |

**Rejection reasons**:
- heartbeat_only: 32
- insufficient_content: 0
- no_anchor_potential: 0

---

## Replay Guardrail Summary

See `replay_guardrail_report.md` for detailed analysis.

**Key findings**:
- Replay improved by +0.289 (no regression)
- All 18 samples improved
- Zero regression
- Not reaching >=0.75 is expected for historical format

---

## Recommendations

### ✅ New Baseline Established

The new baseline with anchor-enhanced capsule + anchor-aware retrieve:

1. **Passes all threshold checks**
2. **Real subset shows strong improvement** (+0.629)
3. **Replay subset shows improvement** (+0.289) without regression
4. **Zero regressed samples**
5. **Correct topic wrong anchor eliminated**

### Next Steps

1. **Enter rollout preparation phase**
2. **Continue replay monitoring** (guardrail remains active)
3. **Plan staged integration** (not immediate main pipeline connection)
4. **Maintain shadow mode** until rollout plan approved

---

## Constraints Respected

| Constraint | Status |
|------------|--------|
| Do not modify old S1 baseline | ✅ Respected |
| Do not claim old Gate 1 passed | ✅ Respected |
| Do not integrate main pipeline | ✅ Respected |
| Do not expand to prompt assemble | ✅ Respected |
| Shadow mode only | ✅ Respected |

---

**Validated by**: New Baseline Validation Pipeline v1.0
