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
**Phase M: ⏳ IN PROGRESS** | selected manual_enable_only Agents 受控 pilot

### Batch M1 (低风险)
| Agent | pilot 状态 | 正式状态 |
|-------|-----------|----------|
| default | pilot_pending | manual_enable_only |
| healthcheck | pilot_pending | manual_enable_only |

### 配置变更需求
等待用户确认后添加到 `acp.allowedAgents`:
```json
{
  "acp": {
    "allowedAgents": ["default", "healthcheck"]
  }
}
```

### 执行分期
| 阶段 | 内容 | 状态 |
|------|------|------|
| M0 | 范围冻结 | ✅ |
| M1 | pilot 候选确认 | ✅ |
| M2 | pilot 启用 | ⏳ 等待确认 |
| M3 | 运行观察 | ⏳ |
| M4 | 治理演练 | ⏳ |
| M5 | 晋级决策 | ⏳ |

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
- `docs/phase-m/FINAL_REPORT.md` - Phase M 最终报告
- `docs/phase-m/M2_PILOT_ENABLE.md` - pilot 启用配置

### Phase History
| Phase | Status | Summary |
|-------|--------|---------|
| Phase I | ✅ CLOSED | 2 new agents enabled (scribe, merger) |
| Phase J | ✅ CLOSED | 5-Agent stability + auto-degradation verified |
| Phase K-T | ✅ CLOSED | Telegram agent inventory & classification |
| Phase K | ✅ CLOSED | Agent pilot enablement & classification (13 agents) |
| Phase L | ✅ CLOSED | manual_enable_only agents minimal access (6 agents) |
| Phase M | ⏳ IN PROGRESS | Batch M1 pilot (default, healthcheck) |

## Key Rule
Task truth is primary; transcript is derived.
