# S1 Validation Known Issues

## Issue #1: total_samples 与 source_counts_sum 不一致

**发现时间**: 2026-03-07
**严重程度**: Medium
**状态**: Open

**描述**:
- Dashboard 显示 total_samples = 105
- source 分布总和 = 119
- 差异：14

**根因**:
- sampler 统计 samples 目录（113 文件）
- dashboard 统计 reports 目录（105 文件）
- 口径不统一

**解决方案**:
- [ ] 统一以 reports 为准
- [ ] 修改 s1-dashboard 显示来源分布

---

## Issue #2: old_topic_recovery 默认 0.50 评分

**发现时间**: 2026-03-07
**严重程度**: High
**状态**: Open

**描述**:
- 所有 synthetic 样本的 old_topic_recovery = 0.50
- 无法达到 >= 0.70 阈值
- Gate 1 无法通过

**根因**:
- `_compute_old_topic_recovery()` 依赖 `is_recall` 事件标记
- synthetic 样本无真实 recall 事件
- 默认返回 0.50

**影响**:
- 当前指标不能代表真实恢复能力
- Gate 1 持续 PENDING

**解决方案**:
- [ ] 优先采集 real_main_agent 样本
- [ ] 修复 session-index 以启用 historical_replay
- [ ] 或改进 synthetic 模板注入可评分事件

---

## Issue #3: historical_replay = 0

**发现时间**: 2026-03-07
**严重程度**: Medium
**状态**: Open

**描述**:
- historical_replay 占比 0%，目标 35%
- 来源结构失衡

**根因**:
- Session index 不可用
- `s1-sampler-v2` 报告 "Warning: Session index not found"

**解决方案**:
- [ ] 检查 session-index 路径
- [ ] 确认 sessions.db 存在且可读

---

## Issue #4: s1-validator-run 缺少 --state 参数

**发现时间**: 2026-03-07
**严重程度**: High (已修复)
**状态**: Fixed

**描述**:
- context-compress 需要 --state 参数
- s1-validator-run 的 step2_shadow_compress 未传递

**修复**:
- 在 step1 中创建初始 state 文件
- 已提交

---

## 追踪

| Issue | Blocker | 修复优先级 |
|---|---|---|
| #1 | No | P2 |
| #2 | Yes (Gate 1) | P0 |
| #3 | No | P1 |
| #4 | Fixed | - |


---

## 2026-03-07 补充：Gate 1 通过前提更新

基于阶段性进度分析，Gate 1 通过前提调整为：

1. **historical_replay > 0**（非象征性 1-2 个，需有意义占比）
2. **scorable_old_topic_samples 明显上升**（目标 >= 30）
3. **old_topic_recovery_on_scorable_samples 接近或超过阈值**（>= 0.70）

**不再追求数量，追求证据质量。**

---

## P0.5: Scoring Scope 定义

**问题**：Gate 1 的 old_topic_recovery 应该看全量还是可评分样本？

**决定**：
- **主观察值**：`old_topic_recovery_on_scorable_samples`
- **辅助值**：全量 `old_topic_recovery`（含不可评分样本）

**口径**：
- `scorable_old_topic_samples`：source_type != synthetic_stress 的样本
- 当前值：23 个
- 目标：>= 30 个

**原因**：不可评分样本（synthetic 默认 0.50）会稀释核心判定。

---

## Synthetic 样本隔离规则

**当前问题**：大量 synthetic 样本 old_topic_recovery = 0.50，拖低全量指标。

**处理方式**：
- 保留样本（不删除）
- 保留报告（不隐藏）
- **从 Gate 1 主指标统计中隔离为 observation-only**
- 仅用于回归测试和压力测试场景

**实施**：
- 在 s1-dashboard 中区分 `primary_metrics` vs `observation_metrics`
- Gate 1 判定只看 `primary_metrics`

