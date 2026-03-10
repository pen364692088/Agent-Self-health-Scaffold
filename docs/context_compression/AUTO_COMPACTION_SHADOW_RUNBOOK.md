# Auto-Compaction Shadow Runbook

**Version**: 1.0
**Purpose**: 异常分类、诊断流程、处置建议

---

## 异常分类速查

| Code | Type | Severity | Action |
|------|------|----------|--------|
| A01 | ratio_unavailable | Medium | Investigate |
| A02 | should_trigger_skip | High | Investigate |
| A03 | blocker_overfire | Medium | Tune |
| A04 | repeated_oscillation | High | Tune |
| A05 | insufficient_drop | High | Investigate |
| A06 | emergency_anomaly | Critical | Immediate |

---

## A01: Ratio Unavailable

### Definition
`context-budget-watcher` 无法获取当前 ratio，返回 `ratio_unavailable`。

### Symptoms
- SHADOW_TRACE 中 `action: none, reason: ratio_unavailable`
- 连续多次 ratio_unavailable

### Diagnostic Steps
```bash
# 1. 检查 session_status 是否正常
session_status

# 2. 检查 budget watcher 日志
~/.openclaw/workspace/tools/context-budget-watcher --json

# 3. 检查 OpenClaw gateway 状态
openclaw gateway status
```

### Root Causes
1. Session 刚启动，context 还未建立
2. OpenClaw 内部状态异常
3. 网络或服务中断

### Resolution
1. **Transient** (1-2 次): 正常，无需处理
2. **Repeated** (3+ 次连续): 检查 OpenClaw gateway 健康状态
3. **Persistent**: 记录到异常日志，人工介入

### Logging
```bash
echo "$(date -Iseconds) A01 ratio_unavailable count=N" >> artifacts/context_compression/shadow/anomaly_log.txt
```

---

## A02: Should Trigger But Skipped

### Definition
Ratio >= 0.80，且无 blocker、无 cooldown，但 action 仍为 `none`。

### Symptoms
- SHADOW_TRACE 中 `ratio >= 0.80` 但 `action: none`
- `reason` 不是 `below_threshold` 或 `blocker_hit`

### Diagnostic Steps
```bash
# 1. 检查 trigger-policy 判定
~/.openclaw/workspace/tools/trigger-policy --ratio <actual_ratio>

# 2. 检查是否有 blocker
~/.openclaw/workspace/tools/compaction-blockers --check

# 3. 检查 cooldown 状态
cat artifacts/context_compression/shadow/cooldown_state.json
```

### Root Causes
1. trigger-policy 逻辑缺陷
2. 隐式 blocker 未记录
3. cooldown 状态不一致

### Resolution
1. **Logic bug**: 修复 trigger-policy
2. **Missing blocker**: 添加到 blocker 定义
3. **State inconsistency**: 重置 cooldown 状态

### Severity
- **High**: 可能导致 context overflow

---

## A03: Blocker Overfire

### Definition
Blocker 命中率异常高（> 50% of eligible triggers）。

### Symptoms
- 大量 `action: none, reason: blocker_hit`
- 特定 blocker 频繁出现

### Diagnostic Steps
```bash
# 1. 统计 blocker 分布
jq '.blocker_id' artifacts/context_compression/SHADOW_TRACE.jsonl | sort | uniq -c

# 2. 检查具体 blocker 内容
~/.openclaw/workspace/tools/compaction-blockers --list

# 3. 验证 blocker 是否合理
# 例如：BLK-GIT-001 应该只在有未提交更改时触发
git status
```

### Root Causes
1. Blocker 条件过于宽泛
2. 用户工作模式导致（频繁 WIP）
3. Blocker 检测逻辑错误

### Resolution
1. **Too broad**: 收紧 blocker 条件
2. **User pattern**: 记录但不调整（用户行为）
3. **Bug**: 修复检测逻辑

### Tuning Guidance
```markdown
| Blocker | Current Threshold | Suggested |
|---------|------------------|-----------|
| BLK-GIT-001 | Any uncommitted | staged files only |
| BLK-LOOP-001 | Any unpersisted | critical loops only |
```

---

## A04: Repeated Oscillation

### Definition
Ratio 在阈值附近反复波动，导致频繁触发/跳过。

### Symptoms
- 短时间内多次 ratio 在 0.78-0.82 之间
- trigger / skip / trigger / skip 模式

### Diagnostic Steps
```bash
# 1. 查看 ratio 变化趋势
jq -r '[.timestamp, .ratio] | @tsv' artifacts/context_compression/SHADOW_TRACE.jsonl | head -20

# 2. 检查触发间隔
~/.openclaw/workspace/tools/shadow_watcher --metrics | grep -A5 "oscillation"
```

### Root Causes
1. Threshold 边界过于敏感
2. Context 自然波动
3. 缺少 hysteresis

### Resolution
1. **Add hysteresis**: 引入滞后区间
   - Trigger: ratio >= 0.80
   - Reset: ratio <= 0.65
2. **Widen threshold**: 调整触发阈值
3. **Increase cooldown**: 延长最小间隔

### Configuration Change
```json
{
  "trigger_ratio": 0.80,
  "reset_ratio": 0.65,
  "hysteresis_enabled": true
}
```

**Note**: Shadow 期不建议修改，记录即可

---

## A05: Insufficient Drop

### Definition
压缩后 ratio 未降到目标区间（0.55-0.65）。

### Symptoms
- Post-compact ratio > 0.65
- 多次压缩后仍不达标

### Diagnostic Steps
```bash
# 1. 检查压缩前后对比
jq 'select(.action == "compact") | {before: .ratio_before, after: .ratio_after}' artifacts/context_compression/SHADOW_TRACE.jsonl

# 2. 检查 capsule 质量
cat artifacts/context_compression/latest_capsule.json | jq '.quality_score'

# 3. 检查压缩策略
cat artifacts/context_compression/compression_strategy.json
```

### Root Causes
1. Capsule 提取质量低
2. Compress 策略过于保守
3. Context 结构问题（大量不可压缩内容）

### Resolution
1. **Capsule quality**: 改进 capsule-builder
2. **Strategy**: 调整压缩强度
3. **Structure**: 分析 context 内容分布

### Severity
- **High**: 影响压缩有效性

---

## A06: Emergency Anomaly

### Definition
非预期 emergency 触发（ratio < 0.90 时触发 emergency）。

### Symptoms
- `action: compact_emergency` 但 ratio < 0.90
- 紧急压缩未按预期触发

### Diagnostic Steps
```bash
# 1. 立即检查 trace
jq 'select(.action == "compact_emergency")' artifacts/context_compression/SHADOW_TRACE.jsonl

# 2. 检查 emergency 判定逻辑
~/.openclaw/workspace/tools/trigger-policy --ratio <actual> --emergency-check

# 3. 检查是否有其他触发条件
cat artifacts/context_compression/emergency_config.json
```

### Root Causes
1. Emergency threshold 错误
2. 级联触发（其他条件触发 emergency）
3. 代码 bug

### Resolution
1. **Immediate**: 记录并监控
2. **Investigate**: 检查 emergency 判定逻辑
3. **Fix**: 修复阈值或逻辑

### Severity
- **Critical**: 可能导致非预期行为

---

## 处置优先级

| Priority | Code | Action Time |
|----------|------|-------------|
| P0 | A06 | Immediate |
| P1 | A02, A05 | Within 1 hour |
| P2 | A04 | Within 1 day |
| P3 | A01, A03 | Within 1 week |

---

## 日志记录格式

```bash
# 记录异常
log_anomaly() {
    local code=$1
    local details=$2
    echo "$(date -Iseconds) | $code | $details" >> artifacts/context_compression/shadow/anomaly_log.txt
}

# 使用示例
log_anomaly A01 "ratio_unavailable count=5 consecutive"
log_anomaly A02 "ratio=0.85 but skipped, no blocker, no cooldown"
```

---

## Escalation Path

1. **P3/P2**: 记录到 anomaly_log.txt，Shadow 期结束后统一处理
2. **P1**: 记录 + 通知，视情况决定是否中断 Shadow
3. **P0**: 立即通知，考虑禁用 Shadow 模式

---

## Contact

- Primary: [Agent/System Owner]
- Secondary: [Backup Contact]
- Channel: [Notification Channel]
