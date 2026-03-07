# Replay Guardrail Report

**Validation Run**: 2026-03-07T04:32:00CST
**Purpose**: Monitor historical replay subset performance separately

---

## Summary

**Status**: ✅ GUARDRAIL PASSED

- Replay subset improved by +0.289
- All 18 samples improved
- Zero regression
- Guardrail requirements met

---

## Replay Metrics

### Overall Performance

| Metric | Baseline | Patch | Delta |
|--------|----------|-------|-------|
| Avg Score | 0.207 | 0.496 | **+0.289** |
| >=0.75 | 0 | 0 | - |
| Improved | - | 18 | - |
| Regressed | - | 0 | - |

### Guardrail Requirements

| Requirement | Threshold | Actual | Pass? |
|-------------|-----------|--------|-------|
| No regression | No samples regressed | 0 regressed | ✅ PASS |
| Better than old baseline | Any improvement | +0.289 improvement | ✅ PASS |

---

## Replay Failure Taxonomy

### Samples Not Reaching >=0.75

**All 18 samples** did not reach >=0.75 threshold.

**Root Cause Analysis**:

| Issue | Samples Affected | Description |
|-------|------------------|-------------|
| Limited decision anchors | 12/18 | Only 6 samples have decision anchors |
| Limited entity anchors | 9/18 | Only 1 entity anchor per sample max |
| Limited open_loop anchors | 2/18 | Very few open loop mentions |
| Limited constraint anchors | 4/18 | Constraints rarely extracted |

**Primary Issue**: Historical replay data format differs from real main agent data:
- Historical: Structured event format with limited text content
- Real: Rich conversational text with diverse anchor potential

### Failure Categories

```
Category A: Low anchor diversity (12 samples)
  - decision: 0-2 anchors
  - entity: 0-1 anchors
  - Result: Score < 0.6

Category B: Time-only samples (4 samples)
  - Only time anchors extracted
  - Result: Score ~0.23

Category C: Tool-state dominant (6 samples)
  - tool_state: 12-15 anchors
  - Other types: minimal
  - Result: Score 0.36-0.51
```

---

## Replay Anchor Coverage Weak Spots

### Weak Anchor Types

| Type | Avg Count | Real Avg | Gap |
|------|-----------|----------|-----|
| decision | 0.9 | 10.0 | **-9.1** |
| entity | 0.5 | 7.1 | **-6.6** |
| open_loop | 0.1 | 6.9 | **-6.8** |
| constraint | 0.2 | 9.6 | **-9.4** |
| tool_state | 7.8 | 15.0 | -7.2 |
| time | 5.4 | 10.0 | -4.6 |

**Analysis**: Historical replay samples lack:
1. Rich decision language
2. File/entity references
3. TODO/TBD markers
4. Constraint language

### Why This Is Expected

Historical replay samples are:
- Simulated scenarios
- Limited text content
- Structured event format
- Not actual user-agent conversations

**Conclusion**: The gap is inherent to data format, not a patch failure.

---

## Replay Score Distribution

```
Score Range    | Count | Samples
---------------|-------|--------
0.00 - 0.25    | 4     | historical_focus_4f39b, historical_with_open_loops_446b, ...
0.25 - 0.50    | 5     | historical_focus_55606, historical_recall_93b29, ...
0.50 - 0.75    | 9     | historical_focus_4b1c4, historical_recall_a28c9, ...
0.75 - 1.00    | 0     | (none)
```

**Observation**: All samples improved, but none reach >=0.75 due to data format limitations.

---

## Guardrail Assessment

### Is Replay a Blocker?

**No.**

Reasoning:
1. Replay improved by +0.289 (significant improvement)
2. Zero regression
3. Gap from >=0.75 is due to data format, not patch failure
4. Real samples (actual use case) perform excellently

### Should Replay Guardrail Be Upgraded to Hard Gate?

**Not at this time.**

Rationale:
1. Need more real historical data in proper format
2. Current historical samples are synthetic/limited
3. Guardrail as observation panel is sufficient

**Recommendation**: Continue monitoring, do not block rollout preparation.

---

## Replay-Specific Recommendations

1. **Collect more historical data** in conversational format
2. **Enhance replay data extraction** to capture more anchor types
3. **Keep replay as separate observation** panel
4. **Do not mix replay average with total average**

---

## Conclusion

| Aspect | Status |
|--------|--------|
| No regression | ✅ Passed |
| Improvement over baseline | ✅ Passed (+0.289) |
| >=0.75 threshold | ⚠️ Not met (data format limitation) |
| Block rollout preparation | ❌ No |

**Guardrail Verdict**: PASS - Continue to rollout preparation phase

---

**Keywords**: `replay-guardrail` `observation-panel` `no-blocking`
