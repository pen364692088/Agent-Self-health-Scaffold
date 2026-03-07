# A/B Benchmark v2 Results - Anchor-Enhanced Capsule Builder

**Run at**: 2026-03-07T03:28:56.772640

## Summary

| Metric | Baseline (A) | Anchor-Aware (B) | Delta |
|--------|-------------|------------------|-------|
| **Avg Score** | 0.241 | 0.531 | +0.290 |
| **>=0.75 Samples** | 0 | 3 | +3 |
| **Improved** | - | 12 | - |
| **Regressed** | - | 0 | - |

### Key Metrics

- **correct_topic_wrong_anchor**: 0
- **top1 anchor hit rate**: 25.0%

---

## By Source Type

### Historical Replay (7 samples)

| Metric | Baseline | Anchor-Aware | Delta |
|--------|----------|--------------|-------|
| Avg Score | 0.413 | 0.746 | +0.333 |
| >=0.75 | 0 | 3 | +3 |

### Real Main Agent (5 samples)

| Metric | Baseline | Anchor-Aware | Delta |
|--------|----------|--------------|-------|
| Avg Score | 0.000 | 0.230 | +0.230 |
| >=0.75 | 0 | 0 | +0 |

---

## Per-Sample Results

| Sample ID | Source | Baseline | Anchor | Delta | >=0.75 |
|-----------|--------|----------|--------|-------|--------|
| pic_focus_4b1c43c501 | historical_repl | 0.500 | 0.887 | +0.387 | ✅ |
| pic_focus_d1f1efede8 | historical_repl | 0.500 | 0.803 | +0.303 | ✅ |
| pic_focus_c5ec44456c | historical_repl | 0.633 | 0.640 | +0.007 | ❌ |
| pic_focus_455a807d7d | historical_repl | 0.267 | 0.640 | +0.373 | ❌ |
| pic_focus_4f39b50590 | historical_repl | 0.250 | 0.640 | +0.390 | ❌ |
| pic_focus_556067aef0 | historical_repl | 0.300 | 0.640 | +0.340 | ❌ |
| opic_recall_a28c92e6 | historical_repl | 0.440 | 0.970 | +0.530 | ✅ |
| opic_recall_4e781246 | real_main_agent | 0.000 | 0.230 | +0.230 | ❌ |
| opic_recall_2a926844 | real_main_agent | 0.000 | 0.230 | +0.230 | ❌ |
| opic_recall_e90ff040 | real_main_agent | 0.000 | 0.230 | +0.230 | ❌ |
| opic_recall_750683fa | real_main_agent | 0.000 | 0.230 | +0.230 | ❌ |
| opic_recall_1301849c | real_main_agent | 0.000 | 0.230 | +0.230 | ❌ |

---

## Recommendation

**✅ 值得进入下一轮修复**

- real_main_agent 子集表现提升
- historical_replay 子集未退化
- 建议继续做 prompt assemble 的 anchor 显式注入
