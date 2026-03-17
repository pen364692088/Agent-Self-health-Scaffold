# Phase H: 健康状态治理策略

**版本**: 1.0  
**创建日期**: 2026-03-17  
**状态**: 已实施

---

## 概述

本文档定义健康状态的治理策略，将 healthy/warning/critical 从"状态文本"升级为"运行治理策略"。

---

## 治理状态定义

### healthy

**行为**: 正常继续，记录 evidence

**动作**: `continue_with_evidence`

**条件**:
- 所有健康检查通过
- 无异常状态

**治理动作**:
- 记录本次执行的 evidence
- 更新执行状态

---

### warning_once

**行为**: 继续运行，标记风险，加入观察

**动作**: `continue_with_monitoring`

**条件**:
- 单次 warning 出现
- 未达到连续阈值

**治理动作**:
- 强制记录风险到日志
- 标记风险项
- 建议下次检查前恢复

---

### warning_repeated

**行为**: 继续但升级为重点观察对象，限制高风险动作

**动作**: `continue_with_escalation`

**条件**:
- 连续 N 次警告 (N >= 2)
- 问题持续存在

**治理动作**:
- 限制高风险动作
- 加强监控频率
- 准备降级方案

---

### critical_once

**行为**: 阻断当前高风险动作，触发恢复流程

**动作**: `block_and_recover`

**条件**:
- 单次 critical 出现
- 严重问题需立即处理

**治理动作**:
- 立即阻断高风险动作
- 触发 recovery 流程
- 通知需要人工干预
- 创建干预请求

---

### critical_repeated

**行为**: 隔离，切换到 manual_enable_only

**动作**: `quarantine_or_manual_mode`

**条件**:
- 连续 M 次 critical (M >= 2)
- 问题严重且持续

**治理动作**:
- 取消默认接管
- 切换为 manual_enable_only
- 待修复后再恢复
- 进入隔离状态

---

## 升级规则

| 当前状态 | 触发条件 | 升级到 |
|---------|---------|--------|
| warning_once | 连续 N 次 warning (N >= 2) | warning_repeated |
| critical_once | 连续 M 次 critical (M >= 2) | critical_repeated |

**默认阈值**:
- WARNING_THRESHOLD = 2
- CRITICAL_THRESHOLD = 2

---

## 恢复规则

| 当前状态 | 恢复条件 | 恢复到 |
|---------|---------|--------|
| quarantine | 连续 K 次健康 (K >= 5) | manual_enable_only |
| pilot_enabled | 连续 K 次健康 | default_enabled |

**默认阈值**:
- RECOVERY_THRESHOLD = 5

---

## 状态转换流程

```
healthy
   ↓ warning
warning_once
   ↓ warning (consecutive)
warning_repeated
   ↓ critical
critical_once
   ↓ critical (consecutive)
critical_repeated → quarantine

恢复路径:
quarantine → manual_enable_only → pilot_enabled → default_enabled
```

---

## 实施原则

1. **一次异常不隔离**: warning_once 和 critical_once 都允许继续或阻断，但不会立即隔离
2. **重复异常升级**: 连续异常会触发更严格的治理动作
3. **恢复需要稳定**: 恢复需要连续健康才能重新启用
4. **证据驱动**: 所有决策基于历史数据

---

## 治理动作矩阵

| 治理状态 | 允许继续 | 需要干预 | 触发隔离 |
|---------|---------|---------|---------|
| healthy | ✅ | ❌ | ❌ |
| warning_once | ✅ | ❌ | ❌ |
| warning_repeated | ✅ (限制) | ❌ | ❌ |
| critical_once | ❌ | ✅ | ❌ |
| critical_repeated | ❌ | ✅ | ✅ |

---

## 实现参考

- `runtime/health_governance_policy.py`
- `runtime/health_action_matrix.py`

---

## 更新记录

| 日期 | 变更 |
|-----|-----|
| 2026-03-17 | 初始版本，定义五种治理状态 |
