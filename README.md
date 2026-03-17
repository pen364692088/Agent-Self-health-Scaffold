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
**Phase K: IN PROGRESS** | K1 候选盘点完成，等待 bot token

### Status Summary
- **5 Agents** running stable with `default_enabled` (业务层):
  - implementer (执行型)
  - planner (规划型)
  - verifier (验证型)
  - scribe (记录型)
  - merger (合并型，中风险)
- **6 Candidates** pending pilot enablement:
  - 低风险: default, healthcheck
  - 中风险: acp-codex, codex, mvp7-coder
  - 高风险: cc-godmode
- **Auto-degradation chain** verified and closed-loop

### Phase K-T (Telegram Inventory)
- 7 Telegram agents 盘点完成
- default_enabled: manager, yuno, testbot, ceo
- manual_enable_only: audit, coder, skadi

### Phase History
| Phase | Status | Summary |
|-------|--------|---------|
| Phase I | ✅ CLOSED | 2 new agents enabled (scribe, merger) |
| Phase J | ✅ CLOSED | 5-Agent stability + auto-degradation verified |
| Phase K-T | ✅ CLOSED | Telegram agent inventory & classification |
| Phase K | ⏳ IN PROGRESS | 6 candidates identified, Batch 1 pending |

## Key Files
- `config/enablement_state.yaml` - Agent enablement configuration
- `SESSION-STATE.md` - Current session state and progress
- `docs/PHASE_K_FINAL_REPORT.md` - Phase K closure report

## Key Rule
Task truth is primary; transcript is derived.
