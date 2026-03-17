# SESSION-STATE.md

## 当前目标
**Phase M - selected manual_enable_only Agents 受控 pilot**

## 阶段

### M0 范围冻结 ✅
- 确认 Batch M1: default + healthcheck

### M1 pilot 候选确认 ✅
- 风险评估通过
- 目录结构完整

### M2 pilot 启用与接入锁定 ❌ BLOCKED
- 配置变更: ✅ acp.allowedAgents 已添加
- 调用验证: ❌ 全部失败
  - runtime="acp": ACP runtime 未配置
  - runtime="subagent": agentId not allowed

### M3-M5 ⏸️ 暂停
- 等待 M2 阻塞解决

## 阻塞原因

1. **ACP Runtime 未安装**: 需要 acpx runtime plugin
2. **sessions_spawn allowed 限制**: 仅允许 coder, audit

## 当前状态

| 状态 | 数量 | Agents |
|------|------|--------|
| continue_default_enabled | 3 | main, audit, coder |
| manual_enable_only | 6 | default, healthcheck, acp-codex, codex, mvp7-coder, cc-godmode |

## 分支
main

## Blocker
调用验证失败，无法推进到观察期

## 下一步
- 选项 A: 安装 ACP Runtime
- 选项 B: 研究 sessions_spawn allowed 配置
- 选项 C: 保持 manual_enable_only，等待后续能力建设

---

## 更新时间
2026-03-17T19:35:00Z
