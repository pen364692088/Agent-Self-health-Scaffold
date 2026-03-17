# Phase K-T: 候选盘点清单

**版本**: 2.0
**日期**: 2026-03-17
**状态**: K1 完成 → K3 观察

---

## 1. 候选范围

**聚焦**: 已有 Telegram bot token 且已启用的 agent

---

## 2. 候选 Agent (已在 pilot 运行)

| Agent | Bot ID | 风险等级 | 状态 | Workspace |
|-------|--------|----------|------|-----------|
| audit | 8388882962 | 低 | pilot_enabled | workspace-audit |
| coder | 8270180209 | 中 | pilot_enabled | workspace-coder |
| manager | 8538576613 | 低 | pilot_enabled | (主 agent) |
| yuno | 8593157471 | 低 | pilot_enabled | workspace-yuno |
| testbot | 8521409435 | 低 | pilot_enabled | workspace-testbot |
| skadi | 8392187738 | 中 | pilot_enabled | workspace-skadi |
| ceo | 8730912384 | 中 | pilot_enabled | workspace-ceo |

**总计**: 7 个 agent

---

## 3. 风险分层

| 风险等级 | Agent | 数量 |
|----------|-------|------|
| 低 | audit, manager, yuno, testbot | 4 |
| 中 | coder, skadi, ceo | 3 |

---

## 4. Phase K 进度

| 阶段 | 状态 |
|------|------|
| K0 真源固化 | ✅ 完成 |
| K1 候选盘点 | ✅ 完成 |
| K2 Batch 规划 | ✅ 跳过 (已启用) |
| K3 运行观察 | ⏳ 待执行 |
| K4 治理验证 | ⏳ 待执行 |
| K5 晋级决策 | ⏳ 待执行 |

---

## 5. 下一步

进入 K3：收集每个 agent 的运行指标
