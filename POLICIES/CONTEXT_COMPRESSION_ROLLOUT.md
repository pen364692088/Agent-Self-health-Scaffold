# Context Compression Rollout Policy v2.2

**Version**: v2.2
**Status**: Phase S1 Active (Feature Frozen)
**Created**: 2026-03-06 11:46 CST

---

## Current Phase: S1 Shadow Validation

**定义**：证据采集阶段，不是开发阶段。

**核心规则**：S1 期间除 blocker 修复外，禁止功能变更。

**参见**：`POLICIES/S1_FEATURE_FREEZE.md`

---

## Gate System (Fixed)

### Gate 0: Minimal Closure ✅ PASSED
```yaml
condition: L1 可用 + capsule-only 可运行
status: passed
timestamp: 2026-03-06T11:35:00CST
```

### Gate 1: Capsule Shadow Ready ⏳ PENDING

**双条件**：

#### 条件 1: 分桶达标
```yaml
requirements:
  total_samples: >= 80
  
  bucket_minimums:
    old_topic_recall: >= 15
    multi_topic_switch: >= 12
    with_open_loops: >= 12
    post_tool_chat: >= 10
    user_correction: >= 10
    long_technical: >= 8
  
  # 不能用某一类简单样本把总量冲上去
  all_buckets_covered: true
```

#### 条件 2: 连续窗口达标
```yaml
requirements:
  recent_window_size: 30
  recent_window_metrics:
    capsule_only_old_topic_recovery: >= 0.70
    capsule_only_commitment_preservation: >= 0.85
    commitment_drift_rate: < 0.05
```

**原因**：累计指标可能被前面简单样本拉高，但近期真实复杂样本已经开始漂。

#### 条件 3: 全量指标达标
```yaml
metrics:
  capsule_only_old_topic_recovery: >= 0.70
  capsule_only_commitment_preservation: >= 0.85
  commitment_drift_rate: < 0.05
  priority_preservation_rate: >= 0.80
  compression_gain_ratio: >= 0.30
  source_mix_distribution: >= 0.90  # capsule > 90%
```

**当前状态**：
```yaml
phase: "S1 覆盖补齐已完成，进入证据提纯阶段"
total_samples: 105 / 80 ✅
bucket_coverage: "ALL COVERED" ✅
scorable_old_topic_samples: 23
old_topic_recovery_on_scorable_samples: 0.50
historical_replay: 0 ❌
gate_1_status: PENDING
```

**Gate 1 通过前提（更新）**：
1. historical_replay > 0（非象征性）
2. scorable_old_topic_samples >= 30
3. old_topic_recovery_on_scorable_samples >= 0.70

### Gate 2: Full Retrieval Ready ❌ BLOCKED
```yaml
condition: OpenViking 恢复 + S2 指标达标
status: blocked
blocker: OpenViking unavailable
```

---

## Monitoring Dashboard

### 总体指标
| 指标 | 阈值 | 当前 | 趋势 |
|------|------|------|------|
| capsule_only_old_topic_recovery | >= 0.70 | N/A | - |
| capsule_only_commitment_preservation | >= 0.85 | N/A | - |
| commitment_drift_rate | < 0.05 | N/A | - |

### 分桶指标（关键！）

**不要只看总样本，要看每个桶的表现**：

| 桶 | 样本数 | drift_rate | gain_ratio | priority_pres |
|---|--------|------------|------------|---------------|
| old_topic_recall | 0 | N/A | N/A | N/A |
| multi_topic_switch | 0 | N/A | N/A | N/A |
| with_open_loops | 0 | N/A | N/A | N/A |
| post_tool_chat | 0 | N/A | N/A | N/A |
| user_correction | 0 | N/A | N/A | N/A |
| long_technical | 0 | N/A | N/A | N/A |

**目的**：快速找到真正薄弱点。

### 连续窗口监控

```yaml
window_size: 30
current_window:
  samples: 12  # < 30, not enough
  metrics: "old_topic_recovery=0.50 (need >=0.70)"
  trend: "N/A"
```

---

## Risk: False Stability

**问题**：系统在普通对话里看起来稳定，一到复杂切话题/修约束/工具续聊就开始软漂。

**监控**：
- 按场景分桶的 drift 分布
- 哪个桶 drift 高
- 哪个桶 compression gain 低
- 哪个桶 priority preservation 差

---

## Light Enforced Rollout (分步)

**不要 Gate 1 一过就把所有聊天全切过去。**

### Step A: Capsule-only Light Enforced (低风险)
```yaml
scope:
  - 单主题连续聊天
  - 无复杂工具链
  - 无强承诺任务
  - 无技术调试上下文

exclusions:
  - 长任务协作
  - 多 agent 状态串联
  - 修 bug 对话
  - 用户要求"别忘了"
  - 技术对话（文件名/路径多）
```

### Step B: 扩大范围
```yaml
trigger: Step A 运行 7 天 + 指标稳定
scope: 一般日常会话
exclusions: 同上
```

---

## S1 Exit Criteria

```yaml
exit_conditions:
  all_required:
    - total_samples >= 80
    - all_buckets_minimum_reached: true
    - recent_window_samples >= 30
    - recent_window_metrics_passed: true
    - all_metrics_passed: true
    - no_blocker_issues: true
  
  gate_result: Gate_1_PASSED
  next_phase: Light_Enforced_Step_A
```

---

## Feature Freeze

**参见**：`POLICIES/S1_FEATURE_FREEZE.md`

**核心规则**：S1 期间除 blocker 修复外，禁止功能变更。

---

## File Locations

- Policy: `POLICIES/CONTEXT_COMPRESSION_ROLLOUT.md`
- Feature Freeze: `POLICIES/S1_FEATURE_FREEZE.md`
- Dashboard: `tools/s1-dashboard`
- Stress Tests: `tests/context/stress/test_s1_scenarios.py`

---

**Keywords**: `phase-s1` `feature-frozen` `bucket-coverage` `continuous-window` `controlled-rollout`
