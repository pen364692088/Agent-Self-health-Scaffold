# Phase K: 候选盘点清单

**版本**: 1.0
**日期**: 2026-03-17
**状态**: K1 进行中

---

## 1. 盘点范围

本次盘点覆盖三个 Agent 来源：

| # | 来源 | 类型 | 说明 |
|---|------|------|------|
| 1 | `~/.openclaw/openclaw.json` (channels.telegram.accounts) | 平台层 | Telegram bot 绑定的 agent |
| 2 | `~/.openclaw/agents/` 目录 | Runtime 实例 | OpenClaw 运行时 agent 实例 |
| 3 | `config/enablement_state.yaml` | 业务层 | Agent-Self-health-Scaffold 项目内 agent |

---

## 2. 来源 1：Telegram Accounts (平台层)

**配置文件**: `~/.openclaw/openclaw.json` → `channels.telegram.accounts`

| Agent | enabled | Bot Token | 风险等级 | 候选状态 |
|-------|---------|-----------|----------|----------|
| audit | True | ✅ | 低 | 已启用 |
| coder | True | ✅ | 中 | 已启用 |
| manager | True | ✅ | 低 | 已启用 |
| yuno | True | ✅ | 低 | 已启用 |
| testbot | True | ✅ | 低 | 已启用 |
| skadi | True | ✅ | 中 | 已启用 |
| ceo | True | ✅ | 中 | 已启用 |
| default | False | ❌ | 低 | **候选** |

**小计**: 7 已启用, 1 候选

---

## 3. 来源 2：Runtime Agent 实例

**目录**: `~/.openclaw/agents/`

| Agent | 目录存在 | 有 Profile | 有 SOUL.md | 风险等级 | 当前状态 | 候选判定 |
|-------|----------|------------|------------|----------|----------|----------|
| acp-codex | ✅ | ❌ | ❌ | 中 | 无 Telegram 绑定 | **候选** |
| audit | ✅ | ❌ | ❌ | 低 | 已启用 | 排除 |
| cc-godmode | ✅ | ❌ | ❌ | 高 | 无 Telegram 绑定 | **候选** |
| ceo | ✅ | ❌ | ❌ | 中 | 已启用 | 排除 |
| coder | ✅ | ❌ | ❌ | 中 | 已启用 | 排除 |
| codex | ✅ | ❌ | ❌ | 中 | 无 Telegram 绑定 | **候选** |
| default | ✅ | ❌ | ❌ | 低 | 已禁用 | **候选** |
| healthcheck | ✅ | ❌ | ❌ | 低 | 无 Telegram 绑定 | **候选** |
| implementer | ✅ | ❌ | ❌ | 低 | 业务层已启用 | 排除 |
| main | ✅ | ❌ | ❌ | 低 | 主 agent | 排除 |
| mc-gateway-* | ✅ | ❌ | ❌ | 低 | MCP 临时实例 | 排除 (临时) |
| mvp7-coder | ✅ | ❌ | ❌ | 中 | 无 Telegram 绑定 | **候选** |
| planner | ✅ | ❌ | ❌ | 低 | 业务层已启用 | 排除 |
| skadi | ✅ | ❌ | ❌ | 中 | 已启用 | 排除 |
| test | ✅ | ❌ | ❌ | 低 | 测试专用 | 排除 (测试) |
| testbot | ✅ | ❌ | ✅ | 低 | 已启用 | 排除 |
| verifier | ✅ | ❌ | ❌ | 低 | 业务层已启用 | 排除 |
| yuno | ✅ | ❌ | ❌ | 低 | 已启用 | 排除 |

**小计**: 
- 已启用/排除: 13
- 候选: 6

---

## 4. 来源 3：业务层 Agent (仓库)

**配置文件**: `config/enablement_state.yaml`

| Agent | 状态 | 风险等级 |
|-------|------|----------|
| implementer | default_enabled | 低 |
| planner | default_enabled | 低 |
| verifier | default_enabled | 低 |
| scribe | default_enabled | 低 |
| merger | default_enabled | 中 |
| test_agent | quarantine | N/A |

**小计**: 5 已启用, 1 quarantine

---

## 5. 候选池汇总

### 5.1 符合条件的候选 Agent

| Agent | 来源 | 风险等级 | 启用路径建议 |
|-------|------|----------|--------------|
| default | 平台层 | 低 | pilot_enabled → Telegram account |
| healthcheck | Runtime | 低 | pilot_enabled → Telegram account |
| acp-codex | Runtime | 中 | pilot_enabled → 验证 ACP 行为 |
| codex | Runtime | 中 | pilot_enabled → Telegram account |
| mvp7-coder | Runtime | 中 | pilot_enabled → 验证 MVP 行为 |
| cc-godmode | Runtime | 高 | pilot_enabled → 严格治理验证 |

### 5.2 排除对象

| Agent | 排除理由 |
|-------|----------|
| main | 主 agent，不可禁用 |
| mc-gateway-* | MCP 临时实例，生命周期短 |
| test | 测试专用 agent |
| test_agent | quarantine 状态 |
| implementer/planner/verifier | 业务层已 default_enabled |

---

## 6. 风险分层

| 风险等级 | 候选 Agent | 批次建议 |
|----------|------------|----------|
| 低 | default, healthcheck | Batch 1 |
| 中 | acp-codex, codex, mvp7-coder | Batch 2 |
| 高 | cc-godmode | Batch 3 (单独) |

---

## 7. Gate K-B 检查项

- [x] 候选清单完整
- [x] 风险分层明确
- [x] 排除对象说明清楚
- [x] 每个候选有唯一身份与当前状态

---

## 8. 下一步

1. **Gate K-B 验证** → 通过后进入 K2
2. **Batch 1 规划** → default + healthcheck (低风险)
3. **创建 batch plan** → `docs/PHASE_K_BATCH_PLAN.md`
