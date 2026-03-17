# Phase H: Agent 启用分层策略

**版本**: 1.0  
**创建日期**: 2026-03-17  
**状态**: 已实施

---

## 概述

本文档定义 Agent 的启用分层策略，明确哪些 Agent 可以默认启用，哪些需要灰度，哪些仅允许手动启用。

---

## 启用层级定义

### Tier 1: default_enabled

**描述**: 默认接管，已通过多轮验证

**特性**:
- 自动执行: ✅
- 需要干预: ❌
- 允许自动接管所有任务

**准入条件**:
- 冷启动稳定 (100% 成功)
- 规则遵循稳定
- 写回稳定 (无丢失)
- warning/critical 口径稳定
- 至少经过 50 次任务观察

**当前 Agent**:
- implementer
- planner
- verifier

---

### Tier 2: pilot_enabled

**描述**: 灰度试点，受控条件下运行

**特性**:
- 自动执行: ✅ (受控)
- 需要干预: ❌
- 限制高风险动作
- 持续观察指标

**准入条件**:
- 已接入底座能力
- 已通过基础验证 (E2E, 冷启动)
- 但未经过足够观察样本

**当前 Agent**: (待扩展)

---

### Tier 3: manual_enable_only

**描述**: 仅手动启用，高风险或新接入

**特性**:
- 自动执行: ❌
- 需要干预: ✅
- 禁止自动接管
- 必须人工触发

**适用场景**:
- 高风险 Agent
- 新接入未验证
- 规则尚未稳定
- 职责特殊的 Agent

**当前 Agent**: (待扩展)

---

### Tier 4: quarantine

**描述**: 隔离状态，禁止自动运行

**特性**:
- 自动执行: ❌
- 需要干预: ✅
- 禁止所有自动操作
- 等待修复后恢复

**触发条件**:
- 连续 critical (>= 3 次)
- 严重治理失败
- 系统判定需要隔离

---

## 状态转换规则

```
manual_enable_only
      ↑ rollout
      ↓ rollback
pilot_enabled
      ↑ rollout
      ↓ rollback
default_enabled
      ↓ quarantine
quarantine
      ↓ recover
manual_enable_only
```

### 允许的转换

| 当前状态 | 可转换到 |
|---------|---------|
| manual_enable_only | pilot_enabled |
| pilot_enabled | default_enabled, manual_enable_only |
| default_enabled | pilot_enabled, quarantine |
| quarantine | manual_enable_only |

---

## 升级条件

### manual_enable_only → pilot_enabled

- 通过 Phase D/E/F/G 等价验证
- 冷启动样本成功
- E2E 测试通过
- 隔离性验证通过

### pilot_enabled → default_enabled

- 观察期内稳定 (>= 20 次任务)
- warning_rate < 20%
- critical_rate < 5%
- 写回成功率 100%

---

## 降级条件

### default_enabled → pilot_enabled

- warning_rate > 30%
- 写回失败
- 需要进一步观察

### pilot_enabled → manual_enable_only

- critical_rate > 10%
- 冷启动失败
- 规则遵循异常

### default_enabled → quarantine

- 连续 critical >= 3 次
- 严重治理失败
- 系统安全风险

---

## 启用矩阵

| Agent ID | 当前层级 | 自动执行 | 备注 |
|----------|---------|---------|------|
| implementer | default_enabled | ✅ | 已验证稳定 |
| planner | default_enabled | ✅ | 已验证稳定 |
| verifier | default_enabled | ✅ | 已验证稳定 |

---

## 实施原则

1. **渐进式扩容**: 不一次性全开，按层级逐步推进
2. **可回退**: 任何状态都可回退到更低层级
3. **证据驱动**: 状态转换必须有证据链
4. **异常隔离**: critical 立即隔离，不尝试自动恢复

---

## 更新记录

| 日期 | 变更 |
|-----|-----|
| 2026-03-17 | 初始版本，定义三层启用策略 |
