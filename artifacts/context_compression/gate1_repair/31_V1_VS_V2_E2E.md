# V1 vs V2 E2E Results

**Date**: 2026-03-09  
**Mode**: Replay Evaluation  

---

## Summary

| Metric | Result |
|--------|--------|
| Total Samples | 100 |
| V1 Avg Readiness | 0.14 |
| V2 Avg Readiness | 0.19 |
| **Improvement** | **+0.05 (36%)** |
| Improved Samples | 17 |
| Regressed Samples | 3 |

---

## Key Results

### ✅ V2 显著优于 V1

1. **整体提升**: +0.05 (36% relative)
2. **改进样本**: 17 vs 3 回归
3. **最佳桶**: long_technical (+0.25)

### ✅ 工具状态提取有效

- post_tool_chat: +0.04
- role=tool 事件正确处理

### ✅ Open Loop 检测改进

- with_open_loops: +0.06
- 多模式支持生效

---

## Gaps

### ⚠️ 整体 readiness 仍偏低

- 当前: 0.19
- 目标: >= 0.50

### ⚠️ old_topic_recall 提升有限

- 只提升 +0.03
- 需要更多改进

### ⚠️ 样本数据质量影响

- 大量日志/代码影响锚点提取

---

## Gate B Verdict

**PARTIAL PASS**

- ✅ V2 优于 V1
- ✅ 改进方向正确
- ⚠️ 未达到 >= 0.70 目标

**需要**: 真实场景验证 + 持续改进

---
