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
**Phase K: ✅ CLOSED** | Agent Pilot 晋级标准化完成

### 最终决策 (正式状态词典)

| 状态 | 数量 | Agents |
|------|------|--------|
| continue_default_enabled | 3 | main, audit, coder |
| manual_enable_only | 6 | default, healthcheck, acp-codex, codex, mvp7-coder, cc-godmode |
| manual_enable_only (需补全) | 4 | implementer, planner, verifier, test |

### 状态词典定义

| 状态 | 定义 |
|------|------|
| continue_default_enabled | 已配置、已验证、可用 |
| manual_enable_only | 有目录但未配置、需手动注册 |

### 关键文档
- `docs/phase-k/FINAL_REPORT.md` - 最终报告
- `docs/phase-k/DECISION_MAPPING.md` - 决策词典映射
- `docs/phase-k/AGENT_CARDS.md` - Agent 卡片与再评估条件

### Phase History
| Phase | Status | Summary |
|-------|--------|---------|
| Phase I | ✅ CLOSED | 2 new agents enabled (scribe, merger) |
| Phase J | ✅ CLOSED | 5-Agent stability + auto-degradation verified |
| Phase K-T | ✅ CLOSED | Telegram agent inventory & classification |
| Phase K | ✅ CLOSED | Agent pilot enablement & classification (13 agents) |

## Key Rule
Task truth is primary; transcript is derived.
