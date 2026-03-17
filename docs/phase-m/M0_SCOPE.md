# Phase M-0: 范围冻结

**日期**: 2026-03-17

---

## 正式状态词典 (冻结)

| 状态 | 定义 |
|------|------|
| continue_default_enabled | 已配置、已验证、可用 |
| manual_enable_only | 有目录但未配置、需手动注册 |

**约束**: 不新增状态词典

---

## Batch 划分

### Batch M1 (低风险)
| Agent | 风险等级 | 理由 |
|-------|----------|------|
| default | 低 | 通用备选，无特殊权限 |
| healthcheck | 低 | 健康检查专用，只读操作 |

### Batch M2 (中风险)
| Agent | 风险等级 | 理由 |
|-------|----------|------|
| acp-codex | 中 | ACP harness，代码执行 |
| codex | 中 | OpenAI Codex，代码执行 |
| mvp7-coder | 中 | 编码专用，代码执行 |

### Batch M3 (高风险)
| Agent | 风险等级 | 理由 |
|-------|----------|------|
| cc-godmode | 高 | 高权限治理，敏感操作 |

---

## 本 Phase 范围

**仅处理 Batch M1**: default + healthcheck

### 不在范围内
- continue_default_enabled agents (main, audit, coder)
- Batch M2 agents (acp-codex, codex, mvp7-coder)
- Batch M3 agent (cc-godmode)

---

## 目标状态

Batch M1 agents 进入 **pilot_enabled** (内部状态，非正式状态词典)

**pilot_enabled 定义**:
- 已添加到 acp.allowedAgents
- 已完成最小调用验证
- 进入观察期
- 有独立观察记录

**重要**: pilot_enabled 是内部工作状态，不是正式状态词典的一部分。正式状态仍为 manual_enable_only。

---

## 观察期定义

| 项目 | 要求 |
|------|------|
| 时长 | 最少 7 天 |
| 调用次数 | 最少 3 次 |
| 错误率 | < 10% |
| 治理演练 | 通过 |

---
**M0 状态**: ✅ 范围冻结完成
