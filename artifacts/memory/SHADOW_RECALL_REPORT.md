# Shadow Recall Report

**Date**: 2026-03-16T00:05:00Z
**Validation**: Memory Kernel M5a Controlled Recall v1

---

## Summary

Recall 验证通过。所有边界条件成立。

---

## Test Scenarios

| Query | Expected | Hit | Records | Status |
|-------|----------|-----|---------|--------|
| API versioning | approved | ✅ | 1 | ✅ |
| configuration | approved | ✅ | 1 | ✅ |
| openemotion | approved | ✅ | 1 | ✅ |
| nonexistent query xyz | miss | ❌ | 0 | ✅ |

---

## Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| total_queries | 4 | - | ✅ |
| approved_hits | 3 | - | ✅ |
| approved_hit_rate | 75% | ≥50% | ✅ |
| candidate_leaked_production | 0 | 0 | ✅ |
| candidate_visible_shadow | 1 | >0 | ✅ |
| scope_filtered | 0 | - | ✅ |
| truth_quotes | 1 | - | ✅ |
| truth_correct | 1 | - | ✅ |
| truth_correct_rate | 100% | 100% | ✅ |

---

## Candidate Visibility Test

| Mode | Expected | Actual | Status |
|------|----------|--------|--------|
| production | candidate 不可见 | 0 leaked | ✅ |
| shadow | candidate 可见 | 1 visible | ✅ |

**关键发现**: Production 模式下 candidate 完全隔离，shadow 模式下可见。

---

## Truth Quote Test

| Record | Content Type | Quote Verified | Status |
|--------|--------------|----------------|--------|
| Configuration Path | Truth | ✅ | ✅ |

**关键发现**: Truth 记录使用精确引用，无摘要冒充。

---

## Key Findings

### ✅ Passed

1. **Candidate 不越权**: Production 模式下 0 条 candidate 泄露
2. **Shadow 模式正确**: Shadow 模式下 candidate 可见
3. **Truth 精确引用**: 100% 精确引用，无摘要冒充
4. **命中率达标**: 75% 命中率，超过 50% 阈值

### No Issues Found

所有边界条件均成立，无异常。

---

## Recommendations

1. **可进入下一阶段**: M5a 边界验证通过
2. **无需修复**: 所有测试通过
3. **建议**: 继续观察生产环境中的召回行为

---

## Evidence

- 验证脚本: `scripts/shadow_validation.py`
- 结果文件: `artifacts/memory/shadow_validation_results.json`

---

**Conclusion**: ✅ PASSED
