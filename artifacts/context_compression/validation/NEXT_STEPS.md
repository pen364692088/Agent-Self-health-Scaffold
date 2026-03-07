# S1 下一步优先级清单

## 当前阶段定义

> S1 覆盖补齐已完成；当前进入 Gate 1 证据提纯阶段。

缺的不是 coverage，而是 evidence quality。

---

## 最优执行顺序

### P0: 修复 session-index，打通 historical_replay

**目标**：
- 让三路低流量策略真正生效
- 给 old_topic_recall 提供更真实的可评分样本
- 降低 synthetic 默认 0.50 对总体指标的扭曲

**验收**：
- historical_replay >= 10 个样本
- session-index 可正常读取

**工具**：
- 检查 `.session-index/sessions.db` 路径
- 修复 `s1-sampler-v2` 的历史回放逻辑

---

### P0.5: Scoring Scope 校验（并行）

**目标**：
- 写死 Gate 1 口径：主观察值 = `old_topic_recovery_on_scorable_samples`
- 隔离 observation-only 样本

**验收**：
- s1-dashboard 区分 primary_metrics vs observation_metrics
- Gate 1 判定只看 primary_metrics

**工具**：
- 修改 `s1-dashboard` 的指标计算逻辑

---

### P1: 专门补 real recall 样本（不泛补）

**目标样本类型**：
1. old_topic_recall 的真实切回样本
2. with_open_loops + old_topic_recall 叠加样本

**验收**：
- scorable_old_topic_samples >= 30
- old_topic_recovery_on_scorable_samples 有提升

**工具**：
- 从真实对话中提取 recall 事件
- 手动标注 is_recall 标记

---

### P2: 收紧 synthetic

**目标**：
- 将不可评分或默认 0.50 的 synthetic old_topic 样本隔离
- 保留样本和报告，但不计入 Gate 1 主指标

**验收**：
- synthetic 样本标记为 observation-only
- Gate 1 指标计算排除 observation-only 样本

---

## Gate 1 通过前提（最终版）

1. historical_replay > 0，而且不是象征性 1-2 个
2. scorable_old_topic_samples 明显上升（>= 30）
3. old_topic_recovery_on_scorable_samples 接近或超过阈值（>= 0.70）

**核心原则**：
> 不追求数量，追求证据质量。

---

## 数据完整性闭环

| 口径 | 定义 | 计入 Gate |
|------|------|-----------|
| samples 目录 | 创建的样本 | ❌ |
| reports 目录 | 完成评分的样本 | 部分 |
| execution_failures | 验证失败的样本 | ❌ |
| observation-only | synthetic 样本 | ❌ |
| primary | 可评分样本（非 synthetic） | ✅ |

**规则**：
- samples - reports = execution_failures
- reports 中 synthetic = observation-only
- Gate 1 只看 primary 样本

