# Phase M-P0: 验证结果

**日期**: 2026-03-17
**状态**: ✅ PASSED

---

## 配置变更

### 变更 1: 添加到 agents.list

**变更前**: `['main', 'testbot', 'skadi', 'yuno', 'audit', 'coder', 'ceo']`
**变更后**: `['main', 'testbot', 'skadi', 'yuno', 'audit', 'coder', 'ceo', 'default', 'healthcheck']`

### 变更 2: 更新 main.subagents.allowAgents

**变更前**: `['coder', 'audit']`
**变更后**: `['coder', 'audit', 'default', 'healthcheck']`

### 备份
- `~/.openclaw/openclaw.json.bak.20260317144700`

---

## 验证调用

### default agent

```bash
sessions_spawn runtime="subagent" agentId="default" task="echo test"
```

**结果**:
```json
{
  "status": "accepted",
  "childSessionKey": "agent:default:subagent:6895357d-8d9d-42d8-8f7e-d832b2ec9afa",
  "runId": "d3e8a68a-be98-4ed0-bd30-5b38cdf9aa44",
  "mode": "run",
  "modelApplied": true
}
```

**结论**: ✅ 成功

### healthcheck agent

```bash
sessions_spawn runtime="subagent" agentId="healthcheck" task="echo test"
```

**结果**:
```json
{
  "status": "accepted",
  "childSessionKey": "agent:healthcheck:subagent:9824ac16-0e54-41fc-8efa-15ddd8f48a8e",
  "runId": "ee5c3377-2277-4126-b1eb-4d0c77a3f6c1",
  "mode": "run",
  "modelApplied": true
}
```

**结论**: ✅ 成功

---

## agents_list 验证

**变更后**:
```json
{
  "agents": [
    {"id": "main", "name": "main", "configured": true},
    {"id": "audit", "name": "audit", "configured": true},
    {"id": "coder", "name": "coder", "configured": true},
    {"id": "default", "name": "default", "configured": true},
    {"id": "healthcheck", "name": "healthcheck", "configured": true}
  ]
}
```

---

## 真实调用证据

| Agent | 调用状态 | Session Key | Run ID |
|-------|----------|-------------|--------|
| default | ✅ accepted | `agent:default:subagent:6895357d-...` | `d3e8a68a-...` |
| healthcheck | ✅ accepted | `agent:healthcheck:subagent:9824ac16-...` | `ee5c3377-...` |

---

## 结论

**正式 pilot 主入口**: sessions_spawn runtime="subagent"

**修复步骤**:
1. ✅ 添加 default, healthcheck 到 agents.list
2. ✅ 添加 default, healthcheck 到 main.subagents.allowAgents
3. ✅ 验证调用成功

**结果**: 
- 已拿到真实成功调用证据
- default 和 healthcheck 可通过 pilot 入口调用
- **Phase M-P0 完成**

---
**M-P0 状态**: ✅ PASSED
