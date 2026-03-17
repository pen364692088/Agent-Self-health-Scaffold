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
**Phase M: ❌ BLOCKED** | Batch M1 调用验证失败

### M2 阻塞详情
| 尝试 | 结果 | 原因 |
|------|------|------|
| acp.allowedAgents 配置 | ✅ | 已添加 default, healthcheck |
| runtime="acp" 验证 | ❌ | ACP runtime 未配置 |
| runtime="subagent" 验证 | ❌ | agentId not allowed |

### 阻塞原因
1. ACP Runtime (acpx plugin) 未安装
2. sessions_spawn allowed 列表仅允许 coder, audit

### 最终状态

| 状态 | 数量 | Agents |
|------|------|--------|
| continue_default_enabled | 3 | main, audit, coder |
| manual_enable_only | 6 | default, healthcheck, acp-codex, codex, mvp7-coder, cc-godmode |

### 状态词典定义

| 状态 | 定义 |
|------|------|
| continue_default_enabled | 已配置、已验证、可用 |
| manual_enable_only | 有目录但未配置、需手动注册 |

### 关键文档
- `docs/phase-m/FINAL_REPORT.md` - Phase M 阻塞报告
- `docs/phase-m/M2_PILOT_ENABLE.md` - 调用验证失败详情

### Phase History
| Phase | Status | Summary |
|-------|--------|---------|
| Phase I | ✅ CLOSED | 2 new agents enabled (scribe, merger) |
| Phase J | ✅ CLOSED | 5-Agent stability + auto-degradation verified |
| Phase K-T | ✅ CLOSED | Telegram agent inventory & classification |
| Phase K | ✅ CLOSED | Agent pilot enablement & classification (13 agents) |
| Phase L | ✅ CLOSED | manual_enable_only agents minimal access (6 agents) |
| Phase M | ❌ BLOCKED | Batch M1 调用验证失败 |

## Key Rule
Task truth is primary; transcript is derived.
