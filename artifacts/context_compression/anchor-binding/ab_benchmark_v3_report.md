# A/B Benchmark v3 Results - Real Samples with Admission Rules

**Run at**: 2026-03-07T03:40:54.735976
**Admission Rules**: ✅ Applied (exclude heartbeat-only, min 2 anchors)

## Summary

| Metric | Baseline (A) | Anchor-Aware (B) | Delta |
|--------|-------------|------------------|-------|
| **Avg Score** | 0.299 | 1.000 | +0.701 |
| **>=0.75 Samples** | 0 | 5 | +5 |
| **Improved** | - | 5 | - |
| **Regressed** | - | 0 | - |

---

## Per-Sample Results

| Sample ID | Source | Baseline | Anchor | Delta | >=0.75 |
|-----------|--------|----------|--------|-------|--------|
| opic_recall_6f39e4a7 | real_main_agent | 0.362 | 1.000 | +0.638 | ✅ |
| opic_recall_3cc19cbd | real_main_agent | 0.294 | 1.000 | +0.706 | ✅ |
| opic_recall_f098c768 | real_main_agent | 0.194 | 1.000 | +0.806 | ✅ |
| opic_recall_ee7ad8b2 | real_main_agent | 0.224 | 1.000 | +0.776 | ✅ |
| opic_recall_f268e9be | real_main_agent | 0.421 | 1.000 | +0.579 | ✅ |

---

## Recommendation

**✅ 显著提升**

- Anchor-aware retrieve 在真实样本上表现良好
- 建议继续做 prompt assemble 的 anchor 显式注入
