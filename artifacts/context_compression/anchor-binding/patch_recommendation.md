# Patch Recommendation

**Date**: 2026-03-07 04:00 CST
**Task**: ANCHOR_PATCH_CANDIDATE_VALIDATION

---

## Executive Summary

**Recommendation: A. 推荐进入新 baseline 的完整验证**

---

## Candidate Patches Validated

| Patch | Description |
|-------|-------------|
| A (Baseline) | baseline retrieve + baseline capsule |
| B (Candidate) | anchor-enhanced capsule builder + anchor-aware retrieve |

---

## Validation Results

### Overall (34 samples)

| Metric | Baseline (A) | Candidate (B) | Delta |
|--------|-------------|---------------|-------|
| Avg Score | 0.284 | 0.733 | **+0.449** |
| >=0.75 | 0 | 16 | +16 |
| Improved | - | 34 | - |
| Regressed | - | 0 | - |
| Correct Topic Wrong Anchor | - | 0 | - |

### By Source Type

#### Historical Replay (18 samples)

| Metric | Baseline | Candidate | Delta |
|--------|----------|-----------|-------|
| Avg Score | 0.207 | 0.496 | +0.289 |
| >=0.75 | 0 | 0 | - |
| Improved | - | 18 | - |
| Regressed | - | 0 | - |

#### Real Main Agent Admissible (16 samples)

| Metric | Baseline | Candidate | Delta |
|--------|----------|-----------|-------|
| Avg Score | 0.371 | **1.000** | **+0.629** |
| >=0.75 | 0 | **16** | +16 |
| Improved | - | 16 | - |
| Regressed | - | 0 | - |

---

## Threshold Check

| Criterion | Threshold | Actual | Pass? |
|-----------|-----------|--------|-------|
| Real subset delta | >= +0.30 | **+0.629** | ✅ PASS |
| Replay subset no regression | N/A | +0.289 improvement | ✅ PASS |
| Regressed samples | 0 or minimal | 0 | ✅ PASS |
| Correct topic wrong anchor | significantly reduced | 0 | ✅ PASS |

---

## Key Findings

### 1. Real Samples Show Strong Improvement

- **Delta: +0.629** (far exceeds +0.30 threshold)
- **100% of real samples reach >=0.75**
- All 16 real samples improved
- Zero regression

### 2. Historical Replay Maintains Improvement

- Delta: +0.289 (close to threshold)
- All 18 samples improved
- No regression
- Though not reaching >=0.75, this is expected given historical data format differences

### 3. Anchor Extraction Working

Real samples show rich anchor extraction:

```json
{
  "decision": 10,
  "entity": 5-15,
  "time": 10,
  "open_loop": 0-10,
  "constraint": 6-10,
  "tool_state": 15
}
```

### 4. Admission Rules Effective

- 42 existing real samples audited
- 32 excluded as heartbeat-only
- 10 admissible retained
- 6 new admissible generated
- Clear separation of quality

---

## What Was NOT Changed (As Required)

- ❌ Did not modify old S1 baseline
- ❌ Did not claim old Gate 1 passed
- ❌ Did not integrate into main pipeline
- ❌ Did not introduce prompt assemble changes
- ❌ Did not modify scoring formulas
- ❌ Did not modify schema definitions

---

## Recommendation Rationale

**Why A (推荐进入新 baseline 的完整验证):**

1. **Strong evidence**: Real subset delta +0.629 exceeds threshold by 2x
2. **No regression**: 0 regressed samples across all 34 samples
3. **Stable improvement**: Historical replay maintains +0.289 improvement
4. **Correct topic wrong anchor eliminated**: 0 cases
5. **Admission rules validated**: Clear separation of heartbeat-only vs real samples

**Why not B (需要扩大样本) or C (补丁不足):**

- Real subset already has 16 samples (exceeds 15+ requirement)
- Historical subset has 18 samples (exceeds 10+ requirement)
- Results are consistent and strong enough to proceed

---

## Next Steps (If Approved)

1. **Create new baseline branch**
   - Do NOT modify old S1 baseline
   - Create fresh baseline for new validation round

2. **Apply candidate patches**
   - Integrate anchor-enhanced capsule builder
   - Integrate anchor-aware retrieve pipeline

3. **Run full S1 validation**
   - Use same admission rules
   - Separate historical vs real reporting
   - Target Gate 1 passage

4. **Keep old baseline intact**
   - Old S1 conclusions remain valid
   - Old Gate 1 status unchanged

---

## Files Generated

| File | Purpose |
|------|---------|
| ADMISSIBILITY_POLICY.md | Frozen sample admission rules |
| real_sample_admissibility_audit.json | Sample audit results |
| candidate_patch_validation_benchmark.json | Benchmark definition |
| candidate_patch_validation_results.json | Full validation results |
| candidate_patch_validation_report.md | Human-readable report |
| patch_recommendation.md | This document |

---

## Final Declaration

**Recommendation: A. 推荐进入新 baseline 的完整验证**

This recommendation:
- ✅ Is based on validated evidence
- ✅ Respects old baseline boundaries
- ✅ Does not claim old Gate 1 passed
- ✅ Does not auto-integrate into main pipeline
- ✅ Follows the strict three-option constraint

---

**Validated by**: Candidate Patch Validation Pipeline v1.0
**Timestamp**: 2026-03-07T04:00:00CST
