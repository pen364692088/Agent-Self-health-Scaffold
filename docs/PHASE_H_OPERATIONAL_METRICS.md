# Phase H: 运行指标

**版本**: 1.0  
**创建日期**: 2026-03-17  
**状态**: 已实施

---

## 概述

本文档定义最小运营指标，用于决定是否扩容。

---

## 核心指标

### cold_start_success_rate

**描述**: 冷启动成功率

**阈值**: 100%

**意义**: Agent 能否可靠启动

---

### memory_restore_success_rate

**描述**: 记忆恢复成功率

**阈值**: 100%

**意义**: 记忆链是否完整

---

### writeback_success_rate

**描述**: 状态写回成功率

**阈值**: 100%

**意义**: 写回链是否稳定

---

### warning_rate

**描述**: warning 比例

**阈值**: <= 20%

**意义**: 异常频率是否可接受

---

### critical_rate

**描述**: critical 比例

**阈值**: <= 5%

**意义**: 严重问题频率

---

### block_accuracy

**描述**: 阻断准确率

**阈值**: >= 90%

**意义**: 阻断是否合理

---

### recovery_success_rate

**描述**: 恢复成功率

**阈值**: >= 80%

**意义**: 恢复流程是否有效

---

## 观察窗口

### 短窗口

- 最近 20 次任务
- 或最近 3 天

用于日常监控。

### 中窗口

- 最近 50 次任务
- 或最近 7 天

用于趋势分析。

---

## Rollout Gating Rules

### 暂停 Rollout

条件（任一）:
- critical_rate > 5%
- writeback_success_rate < 100%

### 允许 Rollout

条件（全部）:
- cold_start_success_rate >= 100%
- writeback_success_rate >= 100%
- critical_rate <= 5%
- warning_rate <= 20%

---

## 实施原则

1. **指标驱动**: 不靠体感决定扩容
2. **阈值明确**: 每个指标都有阈值
3. **窗口合理**: 短/中窗口结合
4. **自动决策**: 可根据指标自动判断

---

## 工具参考

```python
from runtime.operational_metrics import OperationalMetrics

metrics = OperationalMetrics(project_root)

# 记录
metrics.record(snapshot)

# 汇总
summary = metrics.summarize(agent_id)

# 判断
should_pause = metrics.should_pause_rollout(agent_id)
can_rollout = metrics.is_healthy_for_rollout(agent_id)
```

---

## 更新记录

| 日期 | 变更 |
|-----|-----|
| 2026-03-17 | 初始版本 |
