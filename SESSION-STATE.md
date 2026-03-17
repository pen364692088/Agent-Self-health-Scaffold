# SESSION-STATE.md

## 当前目标
**Phase K - Agent Pilot 晋级标准化**

## 阶段

### K0 真源固化 ✅
- 确认 `~/.openclaw/agents/<agentId>/sessions/` 为标准路径

### K1 候选盘点 ✅
- 盘点 13 个 agent 目录

### K2 晋级流程 ✅
- K2-R: Runtime-only 注册完成
- K2-O: Per-agent observation 完成
- K2-G: Governance drill 完成
- K2-D: Final decision 完成

### K-F: Closure Consistency ✅
- 文档口径归一验证通过
- 公开真源同步完成

## 最终决策 (正式状态词典)

| 状态 | 数量 | Agents |
|------|------|--------|
| continue_default_enabled | 3 | main, audit, coder |
| manual_enable_only | 6 | default, healthcheck, acp-codex, codex, mvp7-coder, cc-godmode |
| manual_enable_only (需补全) | 4 | implementer, planner, verifier, test |

## 状态词典定义

| 状态 | 定义 |
|------|------|
| continue_default_enabled | 已配置、已验证、可用 |
| manual_enable_only | 有目录但未配置、需手动注册 |

## 分支
main

## Blocker
无

## 下一步
Phase L 或其他优先任务

---

## 更新时间
2026-03-17T15:50:00Z
