# V1 vs V2 Replay Summary

**Date**: 2026-03-09 10:50 CST  
**Samples**: 100  

---

## Overall Results

| Metric | V1 | V2 | Delta |
|--------|----|----|-------|
| Avg Readiness | 0.14 | 0.19 | **+0.05** |
| Improved | - | 17 | - |
| Regressed | - | 3 | - |
| Same | - | 80 | - |

---

## Bucket Breakdown

| Bucket | V1 | V2 | Delta | Status |
|--------|----|----|-------|--------|
| long_technical | 0.00 | 0.25 | **+0.25** | ✅ Best |
| with_open_loops | 0.21 | 0.26 | +0.06 | ✅ Good |
| user_correction | 0.23 | 0.27 | +0.04 | ✅ Good |
| post_tool_chat | 0.21 | 0.25 | +0.04 | ✅ Good |
| old_topic_recall | 0.16 | 0.19 | +0.03 | ⚠️ Needs more |
| multi_topic_switch | 0.00 | 0.00 | +0.00 | ❌ No data |

---

## Key Findings

### 1. V2 显著优于 V1

- **17 样本改进** vs 3 样本回归
- 整体 readiness 提升 +0.05 (36% relative improvement)

### 2. long_technical 提升最大

- V1: 0.00 → V2: 0.25
- 原因：V2 能正确提取文件路径和技术决策锚点

### 3. with_open_loops 改进明显

- V1: 0.21 → V2: 0.26
- 原因：V2 支持多种 open loop 模式

### 4. post_tool_chat 工具状态提取有效

- V1: 0.21 → V2: 0.25
- 原因：V2 正确处理 role=tool 事件

---

## Issues Identified

### 1. 整体 readiness 仍然偏低

- 当前: 0.19
- 目标: >= 0.50

**原因**:
- 样本数据质量问题（大量日志/代码）
- 缺少明确的决策语句
- 文件路径以相对路径形式出现

### 2. multi_topic_switch 无数据

- 该桶样本在当前样本集中缺失或格式不同

### 3. old_topic_recall 提升有限

- 只提升 +0.03
- 需要进一步改进决策锚点提取

---

## Failure Type Migration

| Failure Type | V1 Count | V2 Count |
|--------------|----------|----------|
| correct_topic_wrong_anchor | ~70 | ~60 |
| topic_recalled_but_tool_state_missing | ~20 | ~10 |
| insufficient_anchors | ~10 | ~30 |

**分析**:
- correct_topic_wrong_anchor 仍是主导失败类型，但数量下降
- tool_state_missing 显著减少
- insufficient_anchors 增加（V2 更严格）

---

## Recommendations

### 短期
1. 改进样本数据筛选
2. 增加决策锚点模式
3. 支持更多文件路径格式

### 中期
1. 在真实压缩场景验证
2. 收集用户反馈
3. 迭代改进

---

## Verdict

**V2 改进有效，但距离 Gate 1 目标 (>=0.70) 仍有差距。**

需要：
1. 继续改进锚点提取逻辑
2. 在真实场景验证
3. 考虑样本数据质量优化

---
