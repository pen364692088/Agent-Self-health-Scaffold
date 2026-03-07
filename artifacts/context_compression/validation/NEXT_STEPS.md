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

## Gate 1 通过前提（最终版 v2）

### 必须同时满足以下 4 条：

1. **historical_replay_reports >= 10**
   - 覆盖至少 2-3 个关键桶（优先 old_topic_recall、with_open_loops）
   - 不允许 80% 都来自同一个历史 session

2. **scorable_old_topic_samples >= 30**
   - 来源：historical_replay + real_main_agent + 其他非 synthetic

3. **historical_replay + real_main_agent scorable old_topic samples >= 15**
   - 保证不是靠 observation-only synthetic 把分母堆出来

4. **old_topic_recovery_on_scorable_samples >= 0.70**
   - 基于 scorable 样本计算，排除 synthetic 默认分

### 当前状态

| 前提 | 当前 | 目标 | 状态 |
|------|------|------|------|
| historical_replay_reports | 0 | >= 10 | ❌ |
| scorable_old_topic_samples | 23 | >= 30 | ❌ |
| replay+real scorable old_topic | 18 | >= 15 | ✅ |
| old_topic_recovery_on_scorable | 0.50 | >= 0.70 | ❌ |

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


---

## 执行顺序约束（强制）⭐⭐⭐

### 规则：口径先于样本

```
P0 修 replay 之前，不要动 scoring
P0.5 写死口径之后，再开始提纯样本
```

### 原因

一旦边补 replay 边改 scoring，会回到"指标变化到底是口径还是能力"的问题。

### 正确流程

```
1. P0: 修 session-index，打通 historical_replay
   ↓
2. P0.5: 写死 Scoring Scope 口径
   ↓
3. P1: 提纯 scorable 样本
   ↓
4. P2: 隔离 observation-only synthetic
   ↓
5. 再看 Gate 1 指标
```

### 禁止行为

- ❌ 边补样本边改口径
- ❌ 在 P0 完成前开始 P1
- ❌ 在 P0.5 完成前解读指标变化

