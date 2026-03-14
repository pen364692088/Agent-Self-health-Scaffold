# Phase 2.9: Prompt Limited Pilot - Design Document

## Objective
为 materialized-state-driven prompt path 启动小范围真实试点，采用双门机制确保安全推进。

---

## Dual Gate Mechanism (核心变更)

### Gate 1: Shadow → Pilot

| 条件 | 要求 | 说明 |
|------|------|------|
| 最小有效样本数 | ≥ 20 | 有效样本定义见下文 |
| 最长观察期 | ≤ 7 天 | 防止无限期观察 |
| Stop Conditions | 全部通过 | 无违规 |
| Match Rate | ≥ 80% | 质量门槛 |
| Conflict Rate | ≤ 5% | 冲突门槛 |
| Fallback Rate | ≤ 10% | 稳定性门槛 |

### Gate 2: Pilot → Decision

| 条件 | 要求 | 说明 |
|------|------|------|
| 最小有效样本数 | ≥ 30 | 更多样本确保可靠性 |
| 最长观察期 | ≤ 14 天 | 防止无限期 pilot |
| Stop Conditions | 全部通过 | 无违规 |

### 可能的决策输出

| 决策 | 条件 | 说明 |
|------|------|------|
| `expand_prompt_pilot` | 所有指标达标 | 扩大试点范围 |
| `continue_pilot_and_patch_gaps` | 1-2 指标略低 | 继续观察并修复 |
| `escalate_to_phase_3` | 多项指标失败 | 升级到 Phase 3 |

---

## Effective Sample Definition (有效样本定义)

### 必须满足所有条件

1. **任务类型在白名单内**
   - `recovery_success`
   - `task_ready_to_close`
   - `gate_completed`

2. **实际执行路径**
   - 实际走到 prompt pilot shadow/pilot 路径
   - 不是配置错误或预检查失败

3. **产生完整指标**
   - 有 match_rate 记录
   - 有 conflict_count 记录
   - 有 provenance_completeness 记录

4. **质量要求**
   - `success = True`
   - `conflict_count = 0`
   - `provenance_completeness ≥ 0.5`

---

## Stop Conditions (扩展)

### 原有条件

| Condition | Threshold | 说明 |
|-----------|-----------|------|
| max_conflict_rate | 5% | 冲突率上限 |
| max_missing_rate | 5% | 缺失率上限 |
| min_match_rate | 80% | 匹配率下限 |
| max_token_overhead | 30% | Token 开销上限 |

### 新增条件

| Condition | Threshold | 说明 |
|-----------|-----------|------|
| max_fallback_rate | 10% | 回退率上限 |
| max_manual_override_rate | 5% | 人工覆盖率上限 |
| min_provenance_completeness | 95% | 来源完整性下限 |

### 监控指标

| Metric | 说明 |
|--------|------|
| `fallback_rate` | 回退到主链的比例 |
| `manual_override_rate` | 人工覆盖的比例 |
| `provenance_completeness` | 状态来源完整性 |
| `effective_sample_count` | 有效样本计数 |
| `user_visible_anomaly_count` | 用户可见异常数 |

---

## Pilot Scope Constraints (权限边界)

### ✅ 允许

- 辅助 main_chain 生成 prompt
- 生成 materialized-state-driven prompt path
- 影响上下文选择

### ❌ 禁止

- 直接决定 task close
- 直接决定 gate pass
- 替代 main_chain 成为 authority

### Authority Chain

```
Final Authority: main_chain
```

所有决策最终由 main_chain 确认。

---

## Configuration

### config/prompt_pilot.json

```json
{
  "pilot_enabled": false,
  "pilot_mode": "shadow",
  "allowed_events": ["recovery_success", "task_ready_to_close", "gate_completed"],
  "blocked_events": ["subagent_spawn", "external_api_call", "user_message"],
  "authority_chain": {"prompt": "main_chain", "recovery": "main_chain"},
  "fallback_on_error": true,
  
  "dual_gate": {
    "shadow_to_pilot": {
      "min_samples": 20,
      "max_days": 7
    },
    "pilot_to_decision": {
      "min_samples": 30,
      "max_days": 14
    }
  },
  
  "stop_conditions": {
    "max_conflict_rate": 0.05,
    "max_missing_rate": 0.05,
    "min_match_rate": 0.80,
    "max_token_overhead": 0.30,
    "max_fallback_rate": 0.10,
    "max_manual_override_rate": 0.05,
    "min_provenance_completeness": 0.95
  },
  
  "pilot_scope": {
    "can_influence_prompt_assembly": true,
    "can_influence_context_selection": true,
    "cannot_decide_task_close": true,
    "cannot_decide_gate_pass": true,
    "final_authority": "main_chain"
  }
}
```

---

## Tools

### prompt-pilot-control

```bash
# 查看状态
tools/prompt-pilot-control --status

# 检查 Gate
tools/prompt-pilot-control --check-gate

# 启用 shadow
tools/prompt-pilot-control --enable --mode shadow

# 切换到 pilot (需要通过 Gate)
tools/prompt-pilot-control --set-mode pilot

# 禁用
tools/prompt-pilot-control --disable --reason "..."
```

### prompt-pilot-preflight

```bash
# 启动前检查
tools/prompt-pilot-preflight
```

检查项：
1. Shadow systems 可用性
2. State files 存在性
3. Configuration 完整性
4. Rollback switch 可用性
5. Metrics path 可写性
6. Sample availability (样本流量)
7. Pilot scope constraints
8. Functional test

---

## Operations Runbook

### 启动流程

```bash
# Step 1: Preflight
tools/prompt-pilot-preflight

# Step 2: Enable shadow
tools/prompt-pilot-control --enable --mode shadow

# Step 3: Monitor and collect samples
# (自动进行，定期检查)

# Step 4: Check gate
tools/prompt-pilot-control --check-gate

# Step 5: If eligible, switch to pilot
tools/prompt-pilot-control --set-mode pilot

# Step 6: Continue monitoring
tools/prompt-pilot-control --status
```

### 禁止事项

- ❌ 直接进入 Phase 3
- ❌ 开启 recovery live
- ❌ 把时间长度当成唯一 gate
- ❌ 在样本不足时强行切 pilot
- ❌ 让 pilot 直接决定任务关闭或 gate 通过

---

## Status Output

### Fields Displayed

```
=== Prompt Pilot Status ===

Status: ENABLED
Mode: shadow
Authority: main_chain
Started: 2026-03-14T10:00:00 (2 days ago)

Allowed Events: recovery_success, task_ready_to_close, gate_completed
Blocked Events: subagent_spawn, external_api_call, user_message

--- Gate Status ---
Effective Samples: 15 / 20 required
Days Elapsed: 2 / 7 max

--- Core Metrics ---
Total Calls: 18
Effective Samples: 15
Successful: 18
Fallbacks: 0
Errors: 0
Manual Overrides: 0
User Visible Anomalies: 0

--- Quality Metrics ---
Avg Match Rate: 92.0%
Avg Conflict Rate: 0.0%
Avg Missing Rate: 0.0%
Avg Token Overhead: 5.0%
Avg Fallback Rate: 0.0%
Avg Manual Override Rate: 0.0%
Avg Provenance Completeness: 100.0%

✅ No stop condition violations

--- Recommendation ---
Status: SHADOW - collecting samples
Action: Continue shadow until 20 samples collected
```

---

## Constraints Verification

| Constraint | Status | Evidence |
|------------|--------|----------|
| No handoff/capsule input | ✅ | Not in scope |
| No second live state | ✅ | Main chain is authority |
| No materialized_state authority | ✅ | Fallback to main_chain |
| No recovery live | ✅ | Recovery stays shadow |
| Explicit rollback switch | ✅ | pilot_enabled flag |
| Stop conditions defined | ✅ | 7 conditions configured |
| Dual gate mechanism | ✅ | Sample + time gates |
| Pilot scope limited | ✅ | Cannot decide task/gate |
