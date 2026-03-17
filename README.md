# Agent-Self-health-Scaffold v2

A constrained self-healing execution kernel scaffold for OpenClaw.

## Why this exists
The problem is not lack of monitoring. The problem is that after restart, corruption, or partial failure, the system often cannot continue the task automatically.

This project focuses on five primary execution-chain goals:
1. durable task truth via a ledger
2. restart-time automatic recovery
3. out-of-band restart execution
4. transcript rebuild from execution truth
5. durable parent/child subtask orchestration

## Current phase
**Phase L: ✅ CLOSED** | manual_enable_only Agents 补全与最小接入

### 最终状态

| 状态 | 数量 | Agents |
|------|------|--------|
| continue_default_enabled | 3 | main, audit, coder |
| manual_enable_only | 6 | default, healthcheck, acp-codex, codex, mvp7-coder, cc-godmode |

### manual_enable_only 接入结论

| Agent | 最小接入条件 | 调用样例 |
|-------|--------------|----------|
| default | acp.allowedAgents | `sessions_spawn runtime="acp" agentId="default"` |
| healthcheck | acp.allowedAgents | `sessions_spawn runtime="acp" agentId="healthcheck"` |
| acp-codex | acp.allowedAgents | `sessions_spawn runtime="acp" agentId="acp-codex"` |
| codex | acp.allowedAgents | `sessions_spawn runtime="acp" agentId="codex"` |
| mvp7-coder | acp.allowedAgents | `sessions_spawn runtime="acp" agentId="mvp7-coder"` |
| cc-godmode | acp.allowedAgents + 治理 | 强化审计，必须通过 main 发起 |

### 状态词典定义

| 状态 | 定义 |
|------|------|
| continue_default_enabled | 已配置、已验证、可用 |
| manual_enable_only | 有目录但未配置、需手动注册 |

### 关键文档
- `docs/phase-l/FINAL_REPORT.md` - Phase L 最终报告
- `docs/phase-l/L5_FINAL_DECISION.md` - 最终分流决策
- `docs/phase-l/L4_GOVERNANCE.md` - 治理与边界

### Phase History
| Phase | Status | Summary |
|-------|--------|---------|
| Phase I | ✅ CLOSED | 2 new agents enabled (scribe, merger) |
| Phase J | ✅ CLOSED | 5-Agent stability + auto-degradation verified |
| Phase K-T | ✅ CLOSED | Telegram agent inventory & classification |
| Phase K | ✅ CLOSED | Agent pilot enablement & classification (13 agents) |
| Phase L | ✅ CLOSED | manual_enable_only agents minimal access (6 agents) |

## Key Rule
Task truth is primary; transcript is derived.
