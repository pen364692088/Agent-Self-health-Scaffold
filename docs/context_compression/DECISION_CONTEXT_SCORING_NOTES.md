# Decision Context Scoring Notes

## Purpose

记录 decision_context 在 readiness 评分中的集成策略。

---

## Scoring Approach

### Chosen Strategy: Soft Enhancement (Option B)

```python
if decision_context.present:
    score += 0.20  # Small bonus
    completeness_score += 0.2
```

**Rationale**:
- Encourages extraction without blocking recovery
- Maintains backward compatibility with V2
- Allows partial recovery even without decision_context

### Alternative Strategies Considered

| Option | Approach | Risk | Verdict |
|--------|----------|------|---------|
| A. Hard Gate | readiness *= 0.5 if missing | Too aggressive | ❌ Rejected |
| B. Soft Enhancement | +0.20 if present | Safe, incremental | ✅ Selected |
| C. Completeness Tier | Separate completeness metric | Useful but complex | ⏳ Future |

---

## Implementation

### V3 Readiness Formula

```
Base (gate passed): 0.20
+ next_action:      0.30
+ decision_context: 0.20  (NEW)
+ tool_state:       0.15
+ open_loops:       0.15
= Maximum:          1.00
```

### Backward Compatibility

- V2 samples without decision_context: still evaluated correctly
- V3 samples with decision_context: get bonus
- No breaking changes to existing capsules

---

## Coverage Impact

| Metric | V2 | V3 (Expected) |
|--------|----|--------------|
| decision_context coverage | 0% | 60-80% |
| Average readiness (gate-passed) | 0.35 | 0.45-0.55 |
| FP rate | 7% | <= 9% (target) |

---

## Monitoring Points

1. **Coverage**: decision_context extraction rate
2. **Precision**: FP rate in decision_context extraction
3. **Impact**: Readiness score distribution shift
4. **Outcome**: Recovery completeness improvement

---

## Rollback Plan

If issues arise:
1. Revert to capsule-builder-v2.py
2. Decision context signal ignored
3. V2 baseline restored

---

*Version: 1.0*
*Created: 2026-03-09*
*Phase: D3 - Rubric Integration*
