# Phase 2.9: Prompt Limited Pilot - Design Document

## Objective
为 materialized-state-driven prompt path 启动小范围真实试点，同时保持 recovery 主链不变。

---

## Pilot Scope

### 允许的任务类型

| 任务类型 | 风险等级 | 理由 |
|----------|----------|------|
| `session_recovery` | 低 | 只读操作，无副作用 |
| `task_close` | 低 | 清理操作，可验证 |
| `gate_completed` | 低 | 状态记录，可审计 |

### 禁止的任务类型

| 任务类型 | 理由 |
|----------|------|
| `user_interaction` | 直接影响用户体验 |
| `subagent_spawn` | 涉及资源创建 |
| `external_api` | 不可控外部依赖 |
| `recovery_live` | 用户明确禁止 |

---

## Rollout Flags

### 配置文件: `config/prompt_pilot.json`

```json
{
  "pilot_enabled": false,
  "pilot_mode": "shadow",
  "allowed_events": [
    "recovery_success",
    "task_ready_to_close",
    "gate_completed"
  ],
  "blocked_events": [
    "subagent_spawn",
    "external_api_call",
    "user_message"
  ],
  "authority_chain": {
    "prompt": "main_chain",
    "recovery": "main_chain"
  },
  "fallback_on_error": true,
  "stop_conditions": {
    "max_conflict_rate": 0.05,
    "max_missing_rate": 0.05,
    "min_match_rate": 0.80,
    "max_token_overhead": 0.30
  },
  "rollback_trigger": {
    "manual": true,
    "auto_on_violation": true,
    "auto_on_error_spike": true
  }
}
```

### Flag 说明

| Flag | 默认值 | 说明 |
|------|--------|------|
| `pilot_enabled` | false | 必须手动启用 |
| `pilot_mode` | "shadow" | shadow / pilot / live |
| `authority_chain` | main_chain | 始终以主链为权威 |
| `fallback_on_error` | true | 错误时自动回退主链 |

---

## Monitoring Metrics

### 核心指标

| Metric | Collection | Alert Threshold |
|--------|------------|-----------------|
| `prompt_match_rate` | 每次调用 | < 80% |
| `prompt_conflict_rate` | 每次调用 | > 5% |
| `prompt_missing_rate` | 每次调用 | > 5% |
| `prompt_token_overhead` | 每次调用 | > 30% |
| `prompt_fallback_count` | 每次调用 | 持续增长 |
| `prompt_error_count` | 每次调用 | > 0 |

### 收集方式

```python
# 每次调用记录
{
  "timestamp": "2026-03-14T10:00:00",
  "event_type": "prompt_pilot_call",
  "session_id": "...",
  "task_type": "recovery_success",
  "match_rate": 0.92,
  "conflict_count": 0,
  "missing_count": 0,
  "token_overhead": 0.05,
  "fallback": false,
  "error": null
}
```

---

## Rollback Mechanism

### 1. Manual Rollback

```bash
# 立即禁用 pilot
tools/prompt-pilot-control --disable

# 或修改配置
jq '.pilot_enabled = false' config/prompt_pilot.json > config/prompt_pilot.json.tmp
mv config/prompt_pilot.json.tmp config/prompt_pilot.json
```

### 2. Auto Rollback Triggers

| Trigger | Action | Threshold |
|---------|--------|-----------|
| Conflict rate spike | Disable pilot | > 5% for 5 min |
| Match rate drop | Disable pilot | < 80% for 5 min |
| Error count spike | Disable pilot | > 3 errors in 5 min |
| Token overhead spike | Alert only | > 30% |

### 3. Rollback Procedure

```
1. Set pilot_enabled = false
2. All subsequent calls use main_chain
3. Log rollback event with reason
4. Notify operator (if configured)
5. Wait for investigation
```

---

## Stop Conditions

### 立即停止

- Conflict rate > 5% 持续 5 分钟
- Match rate < 80% 持续 5 分钟
- 任何 unhandled error
- 用户手动触发

### 试点结束

- 达到预设样本量 (建议 100+ 调用)
- 达到预设时间 (建议 7 天)
- 用户决策

---

## Operations Runbook

### 日常检查 (Daily)

```bash
# 检查 pilot 状态
tools/prompt-pilot-status

# 检查指标
tools/prompt-pilot-metrics --last 24h

# 检查错误
tools/prompt-pilot-errors --last 24h
```

### 启动 Pilot

```bash
# 1. 检查前置条件
tools/prompt-pilot-preflight

# 2. 启用 pilot (shadow mode first)
tools/prompt-pilot-control --enable --mode shadow

# 3. 监控 1-2 天
tools/prompt-pilot-watch

# 4. 切换到 pilot mode
tools/prompt-pilot-control --mode pilot

# 5. 持续监控
tools/prompt-pilot-metrics --live
```

### 禁用 Pilot

```bash
# 立即禁用
tools/prompt-pilot-control --disable

# 带原因禁用
tools/prompt-pilot-control --disable --reason "conflict rate exceeded"
```

### 故障排查

```bash
# 查看 fallback 日志
tools/prompt-pilot-fallbacks --last 1h

# 查看冲突详情
tools/prompt-pilot-conflicts --last 1h

# 查看错误详情
tools/prompt-pilot-errors --last 1h

# 对比 shadow vs main
tools/prompt-pilot-compare --last 1h
```

---

## Success Criteria

### 试点成功的条件

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Match Rate | ≥ 85% | prompt_match_rate |
| Conflict Rate | ≤ 3% | prompt_conflict_rate |
| Fallback Rate | ≤ 5% | prompt_fallback_count / total |
| Error Rate | 0% | prompt_error_count / total |
| Token Overhead | ≤ 20% | prompt_token_overhead |

### Post-Pilot Decision

| Outcome | Decision |
|---------|----------|
| All criteria met | Expand pilot scope |
| 1-2 criteria missed | Patch gaps, continue pilot |
| Multiple criteria failed | Revert to shadow, investigate |

---

## Timeline

| Week | Phase | Mode | Scope |
|------|-------|------|-------|
| 1 | Observation | shadow | Log only, no use |
| 2 | Limited Pilot | pilot | recovery_success only |
| 3 | Expanded Pilot | pilot | + task_close, gate_completed |
| 4 | Evaluation | - | Post-pilot decision |

---

## Constraints Verification

| Constraint | Status | Evidence |
|------------|--------|----------|
| No handoff/capsule input | ✅ | Not in scope |
| No second live state | ✅ | Main chain is authority |
| No materialized_state authority | ✅ | Fallback to main_chain |
| No recovery live | ✅ | Recovery stays shadow |
| Explicit rollback | ✅ | pilot_enabled flag |
| Stop condition | ✅ | Threshold triggers |
