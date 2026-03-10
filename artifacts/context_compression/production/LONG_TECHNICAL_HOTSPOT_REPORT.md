# long_technical Hotspot Report

## Metadata
- **Generated**: 2026-03-09T12:00:00 CST
- **Bucket**: long_technical
- **Sample Count**: 3
- **Issue**: 100% FP rate (V2 gives 0.65 readiness, human says insufficient)

---

## Executive Summary

**结论**：long_technical 的 "FP" 实际上**不是假阳性**。

V2 的 0.65 评分是**合理的**，因为：
- Gate 通过：topic_present, task_active
- Signals 存在：next_action=True, tool_state=True
- Outcome 确实是 partial（可以部分恢复）

Human 认为"信息不足"的原因是：
- `decision_context` 缺失（所有样本）
- 缺少"为什么做这个决策"的上下文

**根因**：这是 **rubric 精度问题**，不是 **evaluator 错误**。

---

## Sample Analysis

### Sample 1: sample_synthetic_stress_long_technical_d63722cc

| Dimension | Value |
|-----------|-------|
| Readiness Score | 0.65 |
| Human Score | 0 |
| Human Reason | 信息不足 |
| V2 Gates | topic_present=True, task_active=True, passed=True |
| V2 Signals | next_action=True, decision_context=False, tool_state=True, open_loops=False |
| Outcome | partial |

**Why V2 gives 0.65?**
- Gate 通过：基础条件满足
- 2/4 signals 存在：next_action + tool_state
- 公式：(gate_score * 0.5) + (signal_score * 0.5) = 0.5 + 0.15 = 0.65

**Why human says insufficient?**
- 长技术文本，信息量大但缺少"决策点"
- 不知道"为什么"要执行这些步骤
- `decision_context` 缺失是关键

**Is recovery possible?**
- ✅ 知道 topic 和 task
- ✅ 知道下一步要做什么
- ✅ 知道工具状态
- ❌ 不知道决策背景和原因
- **结论**：可以**部分恢复**，需要补充决策上下文

---

## Pattern Analysis

### Common Pattern (All 3 samples)

```
Gate Score:     ████████████████████ (passed all)
Signal Score:   ████████░░░░░░░░░░░░ (2/4 present)
  - next_action:        ✓
  - tool_state:         ✓
  - decision_context:   ✗
  - open_loops:         ✗

Human Judgment: 信息不足 (score = 0)
V2 Judgment:    0.65 (medium-high)
Outcome:        partial (can partially recover)
```

### Root Cause

**不是 "长文本误判为高 readiness"**，而是：

1. **Rubric 精度不足**：
   - V2 正确识别了 topic, task, next_action, tool_state
   - 但 `decision_context` 的权重可能需要更高

2. **Human 标准差异**：
   - Human 认为"信息不足" = 无法完整恢复
   - V2 认为"有部分信号" = 可以部分恢复
   - **两者都在说真话，但标准不同**

3. **Signal 定义问题**：
   - `decision_context` 在所有通过样本中都是 False
   - 说明 capsule 本身缺少这个信号，不是 evaluator 问题

---

## Recommendations

### Immediate
1. ✅ **不要降低 long_technical 的评分**（当前 0.65 是合理的）
2. ⏳ **增加 decision_context 的权重或显式标注**
3. ⏳ **在 report 中区分"完全恢复"和"部分恢复"**

### Short-term
1. 修改 capsule-builder 提取 decision_context
2. 在 readiness report 中增加 "missing_critical_signals" 字段
3. 对 long_technical bucket 单独评估时，标注"缺少决策上下文"

### Long-term
1. 建立 signal importance ranking
2. 区分"必要信号"和"增强信号"
3. 对不同 bucket 使用不同的评分策略

---

## Verdict

| Question | Answer |
|----------|--------|
| V2 评分是否错误？ | ❌ 否，0.65 是合理的 |
| 是否是假阳性？ | ❌ 否，outcome 是 partial，不是 fail |
| 根因是什么？ | Rubric 精度 + decision_context 缺失 |
| 如何修复？ | 增加 decision_context 权重/显式标注 |

---

*Hotspot Analysis Complete*
*Next: Update rubric or signal extraction*
