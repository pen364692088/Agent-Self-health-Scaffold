# Default Enablement Checklist

**Version**: 1.0
**Purpose**: Shadow → Production Enablement 操作清单

---

## 前置条件

### 1. Shadow 数据充足

- [ ] Shadow 运行至少 3 天（推荐 7 天）
- [ ] 总观察窗口 >= 100
- [ ] 触发候选窗口 >= 20
- [ ] 至少 1 次 normal compression 执行
- [ ] 无 P0/P1 异常未解决

### 2. Exit Criteria 通过

```bash
# 检查 exit criteria 状态
cat artifacts/context_compression/shadow/SHADOW_SAMPLE_SUMMARY.json | jq '.exit_criteria_progress'
```

| # | Criterion | Required |
|---|-----------|----------|
| 1 | Trigger frequency reasonable | ✅ Pass |
| 2 | No consecutive errors | ✅ Pass |
| 3 | No oscillation | ✅ Pass |
| 4 | Post-compact drop OK | ✅ Pass |
| 5 | Recovery quality OK | ✅ Pass |
| 6 | Emergency normal | ✅ Pass |
| 7 | Blockers explainable | ✅ Pass |

**Minimum**: 6/7 Pass (allow 1 pending)

### 3. 配置指纹确认

```bash
# 确认当前配置
cat artifacts/context_compression/shadow/SHADOW_CONFIG_FINGERPRINT.json
```

确认项：
- [ ] Thresholds 正确
- [ ] Cooldown 正确
- [ ] Blockers 列表完整
- [ ] Git commit 与当前一致

---

## 开启步骤

### Step 1: 备份当前状态

```bash
# 创建备份
mkdir -p artifacts/context_compression/enablement_backup
cp artifacts/context_compression/shadow_config.json artifacts/context_compression/enablement_backup/
cp artifacts/context_compression/SHADOW_TRACE.jsonl artifacts/context_compression/enablement_backup/
cp artifacts/context_compression/shadow/SHADOW_SAMPLE_SUMMARY.json artifacts/context_compression/enablement_backup/
```

### Step 2: 生成 Exit Report

```bash
# 使用模板生成报告
~/.openclaw/workspace/tools/shadow_watcher --exit-report

# 或手动填充模板
cp docs/context_compression/SHADOW_EXIT_REPORT_TEMPLATE.md artifacts/context_compression/SHADOW_EXIT_REPORT.md
# 编辑填充实际数据
```

### Step 3: 修改配置

```bash
# 方式 1: 修改 shadow_config.json
cat > artifacts/context_compression/shadow_config.json << 'EOF'
{
  "enabled": true,
  "mode": "production",
  "started_at": "$(date -Iseconds)",
  "version": "1.0",
  "previous_mode": "shadow",
  "shadow_ended_at": "<shadow_end_time>"
}
EOF

# 方式 2: 设置环境变量
export AUTO_COMPACTION_SHADOW_MODE=false
```

### Step 4: 验证配置生效

```bash
# 检查模式
~/.openclaw/workspace/tools/shadow_watcher --status

# 应该显示:
# Mode: PRODUCTION
# Enabled: true
```

### Step 5: 提交变更

```bash
git add artifacts/context_compression/
git commit -m "feat(context-compression): Enable production auto-compaction

- Shadow period: <start> to <end>
- Exit criteria: X/7 pass
- Exit report: artifacts/context_compression/SHADOW_EXIT_REPORT.md
- Recommendation: ENABLED
"
git push
```

---

## 验证命令

### 立即验证

```bash
# 1. 检查配置
cat artifacts/context_compression/shadow_config.json

# 2. 检查模式
~/.openclaw/workspace/tools/shadow_watcher --status

# 3. 手动触发测试
~/.openclaw/workspace/tools/auto-context-compact --dry-run

# 4. 检查 blockers
~/.openclaw/workspace/tools/compaction-blockers --check
```

### 持续监控 (首 24 小时)

```bash
# 每 4 小时执行
~/.openclaw/workspace/tools/shadow_watcher --metrics

# 检查异常日志
tail -f artifacts/context_compression/shadow/anomaly_log.txt

# 检查最新 trace
tail -5 artifacts/context_compression/SHADOW_TRACE.jsonl | jq
```

---

## 回滚步骤

### 触发条件

- 任何 P0 异常（A06: Emergency Anomaly）
- 连续 3 次压缩失败
- Post-compact ratio 持续不达标（> 2 次）
- Recovery quality 严重下降

### 回滚操作

```bash
# Step 1: 立即禁用
cat > artifacts/context_compression/shadow_config.json << 'EOF'
{
  "enabled": false,
  "mode": "disabled",
  "started_at": "$(date -Iseconds)",
  "version": "1.0",
  "previous_mode": "production",
  "rollback_reason": "<reason>"
}
EOF

# Step 2: 验证禁用
~/.openclaw/workspace/tools/shadow_watcher --status
# 应该显示: Mode: DISABLED

# Step 3: 恢复备份
cp artifacts/context_compression/enablement_backup/* artifacts/context_compression/

# Step 4: 记录回滚
echo "$(date -Iseconds) | ROLLBACK | <reason>" >> artifacts/context_compression/enablement_log.txt

# Step 5: 提交回滚
git add -A
git commit -m "rollback(context-compression): Disable auto-compaction

Reason: <reason>
Previous state: production
Action: Disabled
"
git push
```

---

## 观察窗口

### 首周观察 (Day 1-7)

| Day | Focus | Action |
|-----|-------|--------|
| 1 | 立即验证 | 确认配置生效，无异常 |
| 2 | 频率检查 | 触发次数是否合理 |
| 3 | 质量检查 | Post-compact ratio 达标率 |
| 4 | Blocker 检查 | Blocker 命中率正常 |
| 5 | Emergency 检查 | 无意外 emergency |
| 6 | Recovery 检查 | Session 状态完好 |
| 7 | 总结 | 决定继续/调整/回滚 |

### 每日检查命令

```bash
# 一键检查脚本
~/.openclaw/workspace/tools/shadow_watcher --metrics | tee artifacts/context_compression/daily_check_$(date +%Y%m%d).txt
```

---

## 决策矩阵

### 继续观察

- 所有指标正常
- 无 P0/P1 异常
- 建议：继续监控

### 调整参数

- 触发频率略高/低
- Blocker 命中率异常
- 建议：微调阈值，保持 enabled

### 回滚

- P0 异常
- 连续失败
- 建议：禁用，调查根因

---

## Checklist 完成签名

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Operator | | | |
| Reviewer | | | |

---

## Appendix

### A. 相关文档

- `SHADOW_EXIT_CRITERIA.md` — 退出标准定义
- `SHADOW_EXIT_REPORT_TEMPLATE.md` — 退出报告模板
- `AUTO_COMPACTION_SHADOW_RUNBOOK.md` — 异常处理手册
- `AUTO_COMPACTION_ROLLBACK.md` — 回滚详细步骤

### B. 配置参数速查

```json
{
  "trigger_ratio_normal": 0.80,
  "trigger_ratio_emergency": 0.90,
  "target_ratio_normal": "0.55-0.65",
  "target_ratio_emergency": "0.45-0.55",
  "cooldown_normal_min": 30,
  "cooldown_emergency_min": 15
}
```

### C. 快速命令

```bash
# 状态检查
~/.openclaw/workspace/tools/shadow_watcher --status

# 指标查看
~/.openclaw/workspace/tools/shadow_watcher --metrics

# 手动触发
~/.openclaw/workspace/tools/auto-context-compact --dry-run

# 回滚
./scripts/rollback_auto_compaction.sh
```
