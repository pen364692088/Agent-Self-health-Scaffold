# Gate K-F: Closure Consistency

**目的**: 验证 Phase K 关闭前所有文档口径一致

## 检查项

### K-F.1: 状态词典一致性
- [ ] SESSION-STATE.md 使用正式状态词典
- [ ] FINAL_REPORT.md 使用正式状态词典
- [ ] POLICIES/runtime-agents.md 使用正式状态词典
- [ ] README.md 口径与上述一致

### K-F.2: Agent 分组一致性
- [ ] Tier 1 = continue_default_enabled = 3 agents (main, audit, coder)
- [ ] Tier 2 = manual_enable_only = 6 agents (default, healthcheck, acp-codex, codex, mvp7-coder, cc-godmode)
- [ ] Tier 3 = manual_enable_only + prerequisite = 4 agents (implementer, planner, verifier, test)

### K-F.3: 卡点描述一致性
- [ ] 每个 manual_enable_only agent 有明确卡点
- [ ] 每个 manual_enable_only agent 有明确再评估条件
- [ ] cc-godmode 有额外风险说明

### K-F.4: 文档存在性
- [ ] SESSION-STATE.md 存在且最新
- [ ] FINAL_REPORT.md 存在且最新
- [ ] DECISION_MAPPING.md 存在
- [ ] AGENT_CARDS.md 存在
- [ ] PILOT_TRACKING.md 存在

### K-F.5: 状态文件更新时间
- [ ] 所有文档更新时间在本次会话内
- [ ] 无过期或冲突的状态声明

## 验证命令
```bash
# 检查文档存在
ls -la ~/.openclaw/workspace/SESSION-STATE.md
ls -la ~/.openclaw/workspace/docs/phase-k/

# 检查状态词典使用
grep -c "continue_default_enabled\|manual_enable_only" ~/.openclaw/workspace/SESSION-STATE.md
grep -c "continue_default_enabled\|manual_enable_only" ~/.openclaw/workspace/docs/phase-k/FINAL_REPORT.md
```

## 通过标准
- 所有检查项 ✅
- 无冲突状态声明
- 文档更新时间一致

## 当前状态
✅ PASSED - 2026-03-17T15:23:00Z
