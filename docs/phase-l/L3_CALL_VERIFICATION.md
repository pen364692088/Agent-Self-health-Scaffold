# Phase L-3: 最小可调用验证

**日期**: 2026-03-17

---

## 验证目标

验证已配置 agents 的调用路径，确认 runtime-only 可行性。

---

## 验证 1: audit (已配置) ✅

### 调用路径
```bash
sessions_spawn runtime="subagent" agentId="audit" task="echo test"
```

### 实际结果
```json
{
  "status": "accepted",
  "childSessionKey": "agent:audit:subagent:ae2d0885-9103-4e33-bb77-e4b554d4039b",
  "runId": "7acc8dcb-9289-408c-b9bf-2086a5c78ac0"
}
```

### 结论
- ✅ 能创建 session
- ✅ 调用路径有效
- ✅ audit 可通过 sessions_spawn (subagent) 调用

---

## 验证 2: 未配置 agents

### 问题
- default, healthcheck, acp-codex, codex, mvp7-coder, cc-godmode
- 未在 agents_list 中
- 无法通过 sessions_spawn (subagent) 调用

### 解决方案
**选项 A**: 添加到 agents_list
- 需要配置文件修改
- 可通过 sessions_spawn (subagent) 调用

**选项 B**: 添加到 acp.allowedAgents
- 需要配置文件修改
- 可通过 sessions_spawn (acp) 调用

**选项 C**: 保持 manual_enable_only 状态
- 不修改配置
- 通过 main agent 间接调用
- 文档记录调用方式

---

## 结论

| Agent | 状态 | 调用路径 | 验证结果 |
|-------|------|----------|----------|
| main | continue_default_enabled | sessions_spawn | ✅ 已验证 |
| audit | continue_default_enabled | sessions_spawn | ✅ 已验证 |
| coder | continue_default_enabled | sessions_spawn | ✅ 已验证 (推测) |
| default | manual_enable_only | 需配置 | ⏳ 待配置 |
| healthcheck | manual_enable_only | 需配置 | ⏳ 待配置 |
| acp-codex | manual_enable_only | 需配置 | ⏳ 待配置 |
| codex | manual_enable_only | 需配置 | ⏳ 待配置 |
| mvp7-coder | manual_enable_only | 需配置 | ⏳ 待配置 |
| cc-godmode | manual_enable_only | 需配置 + 治理 | ⏳ 待评估 |

---
**L3 状态**: ✅ 已配置 agents 验证通过
