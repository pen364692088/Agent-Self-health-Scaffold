# Phase M 最终报告

**日期**: 2026-03-17
**状态**: ❌ BLOCKED

---

## 执行摘要

Phase M 尝试让 default 和 healthcheck 进入受控 pilot，配置变更成功但调用验证失败。

---

## 执行分期

| 阶段 | 内容 | 状态 |
|------|------|------|
| M0 | 范围冻结 | ✅ |
| M1 | pilot 候选确认 | ✅ |
| M2 | pilot 启用与接入锁定 | ❌ BLOCKED |
| M3 | 单 Agent 运行观察 | ⏸️ 暂停 |
| M4 | 治理演练 | ⏸️ 暂停 |
| M5 | 晋级决策 | ⏸️ 暂停 |

---

## M2 阻塞详情

### 配置变更 ✅
- 备份: ✅
- 增量合并: ✅
- `acp.allowedAgents`: `[]` → `["default", "healthcheck"]`

### 调用验证 ❌

| 尝试 | 结果 | 错误 |
|------|------|------|
| runtime="acp" | ❌ | ACP runtime backend 未配置 |
| runtime="subagent" | ❌ | agentId not allowed (allowed: coder, audit) |

### 阻塞原因
1. **ACP Runtime 未安装**: 需要安装 `acpx` runtime plugin
2. **sessions_spawn allowed 限制**: default, healthcheck 不在 allowed 列表
3. **配置来源不明**: agents_list 配置机制需要进一步研究

---

## 真实调用证据

**无有效调用证据**。根据任务要求，不得宣称 Phase M 有效推进。

---

## 强制约束遵守确认

| 约束 | 遵守状态 |
|------|----------|
| 不修改 continue_default_enabled 的 3 个 agent | ✅ |
| 不新增正式状态词典 | ✅ |
| 不要求 Telegram token | ✅ |
| 不把"可调用"表述为"已稳定" | ✅ |
| 未拿到真实调用证据，不宣称有效推进 | ✅ |

---

## 建议

**保持 manual_enable_only 状态**，等待后续能力建设：
1. ACP Runtime 安装和配置
2. 或研究 sessions_spawn allowed 配置机制

---

## 文档

| 文档 | 路径 |
|------|------|
| 任务单 | docs/phase-m/TASK.md |
| M0 范围冻结 | docs/phase-m/M0_SCOPE.md |
| M1 候选确认 | docs/phase-m/M1_CANDIDATE_CONFIRM.md |
| M2 pilot 启用 | docs/phase-m/M2_PILOT_ENABLE.md (BLOCKED) |
| M3 运行观察 | docs/phase-m/M3_OBSERVATION.md (暂停) |
| M4 治理演练 | docs/phase-m/M4_GOVERNANCE.md (暂停) |
| M5 晋级决策 | docs/phase-m/M5_DECISION.md (暂停) |

---

**结论**: Phase M 因调用验证失败而阻塞。default 和 healthcheck 保持 manual_enable_only 状态。
