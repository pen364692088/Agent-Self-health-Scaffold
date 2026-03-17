# Phase M-2: pilot 启用与接入锁定

**日期**: 2026-03-17

---

## 启用条件

### 前提条件
1. 目录结构完整 ✅
2. 风险评估通过 ✅
3. 有明确调用路径 ✅

### 配置变更需求

**当前状态**:
- default: 未在 agents_list
- healthcheck: 未在 agents_list

**目标状态**:
- 添加到 `acp.allowedAgents`

---

## 配置变更步骤

### 步骤 1: 添加到 acp.allowedAgents

编辑 `~/.openclaw/config.json`:

```json
{
  "acp": {
    "allowedAgents": ["default", "healthcheck"]
  }
}
```

### 步骤 2: 重启 gateway (可选)

```bash
openclaw gateway restart
```

### 步骤 3: 验证配置

```bash
# 验证 acp.allowedAgents
cat ~/.openclaw/config.json | jq '.acp.allowedAgents'
```

---

## 接入锁定

### 调用路径
```bash
sessions_spawn runtime="acp" agentId="default" thread=true
sessions_spawn runtime="acp" agentId="healthcheck" thread=true
```

### 锁定条件
- 配置已添加
- 调用路径明确
- 验证通过

---

## 当前状态

| Agent | 配置状态 | 接入状态 |
|-------|----------|----------|
| default | ⏳ 待添加 | ⏳ 待验证 |
| healthcheck | ⏳ 待添加 | ⏳ 待验证 |

---

## 下一步

1. 用户确认是否执行配置变更
2. 执行配置变更
3. 验证调用
4. 进入观察期

---
**M2 状态**: ⏳ 等待用户确认配置变更
