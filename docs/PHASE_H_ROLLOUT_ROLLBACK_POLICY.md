# Phase H: Rollout/Rollback/Quarantine 策略

**版本**: 1.0  
**创建日期**: 2026-03-17  
**状态**: 已实施

---

## 概述

本文档定义 Agent 启用状态的 rollout、rollback、quarantine 和 recovery 机制。

---

## 状态机

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

---

## Rollout

### 定义

将 Agent 推进到更高启用层级。

### 允许的转换

| 当前状态 | 可 rollout 到 |
|---------|--------------|
| manual_enable_only | pilot_enabled |
| pilot_enabled | default_enabled |

### 流程

1. 检查准入条件
2. 更新启用状态
3. 记录 rollout evidence
4. 开始观察期

### CLI

```bash
python tools/enablement_manager.py rollout \
  --agent-id new_agent \
  --tier pilot_enabled \
  --reason "Passed Phase D/E/F/G verification"
```

---

## Rollback

### 定义

将 Agent 回退到更低启用层级。

### 允许的转换

| 当前状态 | 可 rollback 到 |
|---------|---------------|
| default_enabled | pilot_enabled |
| pilot_enabled | manual_enable_only |

### 触发条件

- warning_rate > 30%
- 写回失败
- 需要进一步观察
- 人工决策

### 流程

1. 决定回退原因
2. 更新启用状态
3. 保留所有 memory/state
4. 记录 rollback evidence

### CLI

```bash
python tools/enablement_manager.py rollback \
  --agent-id some_agent \
  --reason "High warning rate, needs observation"
```

---

## Quarantine

### 定义

立即隔离 Agent，禁止自动运行。

### 触发条件

- 连续 critical >= 3 次
- 严重治理失败
- 系统安全风险

### 效果

- 取消默认接管
- 禁止所有自动操作
- 进入隔离状态

### 流程

1. 检测到隔离条件
2. 立即切换到 quarantine 状态
3. 阻断所有高风险动作
4. 创建干预请求
5. 通知需要修复

### CLI

```bash
python tools/enablement_manager.py quarantine \
  --agent-id problematic_agent \
  --reason "Consecutive critical errors"
```

---

## Recovery

### 定义

从隔离状态恢复到手动模式。

### 条件

- 问题已修复
- 连续健康 >= 5 次
- 通过验证

### 流程

1. 修复问题
2. 执行验证
3. 记录连续健康
4. 达到阈值后恢复
5. 进入 manual_enable_only 状态

### CLI

```bash
python tools/enablement_manager.py recover \
  --agent-id recovered_agent \
  --reason "Issue fixed, passed verification"
```

---

## 证据链

所有状态转换都必须记录证据：

- 转换时间
- 前后状态
- 转换原因
- 相关证据文件

证据存储在: `logs/enablement_history/`

---

## 实施原则

1. **可回退**: 任何升级都可以回退
2. **可隔离**: 任何 Agent 都可以隔离
3. **可恢复**: 隔离后可以恢复
4. **证据驱动**: 所有操作都有证据链

---

## 工具参考

```bash
# 查看状态
python tools/enablement_manager.py status

# Rollout
python tools/enablement_manager.py rollout --agent-id X --tier Y --reason "Z"

# Rollback
python tools/enablement_manager.py rollback --agent-id X --reason "Z"

# Quarantine
python tools/enablement_manager.py quarantine --agent-id X --reason "Z"

# Recover
python tools/enablement_manager.py recover --agent-id X --reason "Z"
```

---

## 更新记录

| 日期 | 变更 |
|-----|-----|
| 2026-03-17 | 初始版本 |
