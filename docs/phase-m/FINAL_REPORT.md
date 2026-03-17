# Phase M 最终报告

**日期**: 2026-03-17
**状态**: ⏳ IN PROGRESS

---

## 执行摘要

Phase M 正在进行中，目标是让 default 和 healthcheck 进入受控 pilot。

---

## 执行分期

| 阶段 | 内容 | 状态 |
|------|------|------|
| M0 | 范围冻结 | ✅ |
| M1 | pilot 候选确认 | ✅ |
| M2 | pilot 启用与接入锁定 | ⏳ 等待用户确认 |
| M3 | 单 Agent 运行观察 | ⏳ 待观察期 |
| M4 | 治理演练 | ⏳ 待观察期后 |
| M5 | 晋级决策 | ⏳ 待全部条件满足 |

---

## Batch M1 候选

| Agent | 风险等级 | 状态 | 推荐进入 pilot |
|-------|----------|------|----------------|
| default | 低 | 目录完整 | ✅ |
| healthcheck | 低 | 目录完整 | ✅ |

---

## 配置变更需求

### 需要用户确认
编辑 `~/.openclaw/config.json`:

```json
{
  "acp": {
    "allowedAgents": ["default", "healthcheck"]
  }
}
```

### 变更后验证
```bash
sessions_spawn runtime="acp" agentId="default" task="echo test"
sessions_spawn runtime="acp" agentId="healthcheck" task="echo test"
```

---

## 强制约束遵守确认

| 约束 | 遵守状态 |
|------|----------|
| 不修改 continue_default_enabled 的 3 个 agent | ✅ |
| 不新增正式状态词典 | ✅ |
| 不要求 Telegram token | ✅ |
| 不把"可调用"表述为"已稳定" | ✅ |
| Batch M1: default + healthcheck | ✅ |
| Batch M2: acp-codex, codex, mvp7-coder (不在本 Phase) | ✅ |
| Batch M3: cc-godmode (不在本 Phase) | ✅ |

---

## 下一步行动

1. **用户确认**: 是否执行配置变更
2. **配置变更**: 添加到 acp.allowedAgents
3. **验证调用**: 确认调用路径有效
4. **观察期**: 开始 7 天观察期
5. **治理演练**: 观察期后执行
6. **晋级决策**: 条件满足后决策

---

## 文档

| 文档 | 路径 |
|------|------|
| 任务单 | docs/phase-m/TASK.md |
| M0 范围冻结 | docs/phase-m/M0_SCOPE.md |
| M1 候选确认 | docs/phase-m/M1_CANDIDATE_CONFIRM.md |
| M2 pilot 启用 | docs/phase-m/M2_PILOT_ENABLE.md |
| M3 运行观察 | docs/phase-m/M3_OBSERVATION.md |
| M4 治理演练 | docs/phase-m/M4_GOVERNANCE.md |
| M5 晋级决策 | docs/phase-m/M5_DECISION.md |

---

**结论**: Phase M 已完成 M0-M1，等待用户确认配置变更后继续。
