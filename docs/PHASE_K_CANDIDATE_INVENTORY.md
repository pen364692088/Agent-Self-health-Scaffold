# Phase K: 候选盘点清单

**版本**: 1.0
**日期**: 2026-03-17
**状态**: K1 进行中

---

## 1. 候选范围

**业务层候选**: 存在于 `~/.openclaw/agents/` 但未绑定 Telegram bot 的 agent

**排除**:
- 已有 Telegram bot 且已启用的 agent (已在 Phase K-T 处理)
- 测试专用 agent
- MCP 临时实例

---

## 2. 候选 Agent 清单

| Agent | 目录存在 | 风险等级 | 当前状态 | 启用需求 |
|-------|----------|----------|----------|----------|
| default | ✅ | 低 | disabled | 创建 Telegram bot |
| healthcheck | ✅ | 低 | 无 bot 绑定 | 创建 Telegram bot |
| acp-codex | ✅ | 中 | 无 bot 绑定 | 创建 Telegram bot |
| codex | ✅ | 中 | 无 bot 绑定 | 创建 Telegram bot |
| mvp7-coder | ✅ | 中 | 无 bot 绑定 | 创建 Telegram bot |
| cc-godmode | ✅ | 高 | 无 bot 绑定 | 创建 Telegram bot |

**总计**: 6 个候选

---

## 3. 风险分层

| 风险等级 | 候选 Agent | 批次 |
|----------|------------|------|
| 低 | default, healthcheck | Batch 1 |
| 中 | acp-codex, codex, mvp7-coder | Batch 2 |
| 高 | cc-godmode | Batch 3 |

---

## 4. 启用路径

每个候选必须经过：

```
candidate → pilot_enabled → per-agent observation → governance drill → decision
```

**禁止**:
- 跳过 pilot 直接启用
- 用总平均掩盖个体问题
- 跳过治理验证

---

## 5. Gate K-B 检查项

- [x] 候选清单完整 (6 个)
- [x] 风险分层明确
- [x] 排除对象说明清楚
- [x] 每个候选有唯一身份

---

## 6. 下一步

**Blocker**: 所有候选均无 Telegram bot token

需要用户提供:
1. 通过 @BotFather 创建 bot
2. 提供 bot token

或者：仅做 runtime 启用（不绑定 Telegram）
