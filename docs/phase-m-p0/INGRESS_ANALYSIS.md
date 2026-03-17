# Phase M-P0: Pilot 入口分析

**日期**: 2026-03-17

---

## 发现

### 1. agents_list 配置来源

**位置**: `~/.openclaw/openclaw.json` → `agents.list`

**当前配置**:
```json
{
  "agents": {
    "list": [
      {"id": "main", "default": true, ...},
      {"id": "testbot", ...},
      {"id": "skadi", ...},
      {"id": "yuno", ...},
      {"id": "audit", ...},
      {"id": "coder", ...},
      {"id": "ceo", ...}
    ]
  }
}
```

### 2. sessions_spawn allowed 来源

**位置**: `~/.openclaw/openclaw.json` → `agents.list[0].subagents.allowAgents`

**main agent 配置**:
```json
{
  "id": "main",
  "subagents": {
    "allowAgents": ["coder", "audit"]
  }
}
```

**这就是为什么**:
- `sessions_spawn runtime="subagent"` 报错 "allowed: coder, audit"
- 只有 `coder` 和 `audit` 在 main 的 `allowAgents` 列表中

### 3. ACP Runtime 状态

**位置**: `~/.openclaw/config.json` → `acp.allowedAgents`

**当前配置**:
```json
{
  "acp": {
    "allowedAgents": ["default", "healthcheck"]
  }
}
```

**问题**: ACP runtime backend (acpx plugin) 未安装/启用

---

## 结论

### 正式 pilot 主入口

**sessions_spawn runtime="subagent"** 是当前可用的入口（已配置 coder, audit）

**sessions_spawn runtime="acp"** 需要额外的 runtime backend 安装

### 修复方案

**选项 A**: 添加到 `agents.list`
1. 在 `~/.openclaw/openclaw.json` 中添加 `default` 和 `healthcheck` 到 `agents.list`
2. 配置 `workspace`, `agentDir`, `model` 等必要字段

**选项 B**: 添加到 `main.subagents.allowAgents`
1. 在 main agent 的 `subagents.allowAgents` 中添加 `default` 和 `healthcheck`
2. 但这些 agent 需要先在 `agents.list` 中配置

**推荐**: 选项 A（完整配置）

---

## 修复步骤

1. 备份 `~/.openclaw/openclaw.json`
2. 在 `agents.list` 中添加 `default` 和 `healthcheck`
3. 重新验证 `sessions_spawn runtime="subagent"`
4. 记录调用证据

---
**分析状态**: ✅ 完成
