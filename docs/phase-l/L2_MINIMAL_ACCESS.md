# Phase L-2: 最小接入补全

**日期**: 2026-03-17

---

## 调用路径分析

### 路径 1: sessions_spawn (runtime="acp")

**前提**: agent 需在 `acp.allowedAgents` 列表中

```bash
sessions_spawn runtime="acp" agentId="<agent>" thread=true
```

### 路径 2: sessions_spawn (runtime="subagent")

**前提**: agent 需在 agents_list 中

```bash
sessions_spawn runtime="subagent" agentId="<agent>"
```

### 路径 3: sessions_send (直接调用)

**前提**: agent 需有活动的 session

```bash
sessions_send sessionKey="<agent>:<sessionId>" message="..."
```

---

## 当前状态

### agents_list (已配置)

| Agent | 在 agents_list | 状态 |
|-------|---------------|------|
| main | ✅ | continue_default_enabled |
| audit | ✅ | continue_default_enabled |
| coder | ✅ | continue_default_enabled |
| default | ❌ | manual_enable_only |
| healthcheck | ❌ | manual_enable_only |
| acp-codex | ❌ | manual_enable_only |
| codex | ❌ | manual_enable_only |
| mvp7-coder | ❌ | manual_enable_only |
| cc-godmode | ❌ | manual_enable_only |

### acp.allowedAgents

| Agent | 在 allowedAgents | 备注 |
|-------|------------------|------|
| main | ❌ | 不在 ACP 列表 |
| audit | ❌ | 不在 ACP 列表 |
| coder | ❌ | 不在 ACP 列表 |
| default | ❌ | 需添加 |
| healthcheck | ❌ | 需添加 |
| acp-codex | ❌ | 需添加 |
| codex | ❌ | 需添加 |
| mvp7-coder | ❌ | 需添加 |
| cc-godmode | ❌ | 需添加 (单独评估) |

---

## 接入路径选择

### 已配置 Agents (main, audit, coder)
- **可用路径**: sessions_spawn (runtime="subagent")
- **状态**: continue_default_enabled
- **无需操作**: 已可用

### 未配置 Agents (5 + 1)

| Agent | 推荐路径 | 前提条件 |
|-------|----------|----------|
| default | acp.allowedAgents | 添加到配置 |
| healthcheck | acp.allowedAgents | 添加到配置 |
| acp-codex | acp.allowedAgents | 添加到配置 |
| codex | acp.allowedAgents | 添加到配置 |
| mvp7-coder | acp.allowedAgents | 添加到配置 |
| cc-godmode | acp.allowedAgents | 添加到配置 + 治理边界 |

---

## 最小接入补全动作

### 批量处理 (5 agents)
1. 添加到 `acp.allowedAgents`
2. 验证调用路径
3. 记录调用样例

### 单独处理 (cc-godmode)
1. 评估治理边界
2. 定义使用场景
3. 添加到 `acp.allowedAgents` (带条件)
4. 验证调用路径

---
**L2 状态**: ⏳ 待执行接入配置
