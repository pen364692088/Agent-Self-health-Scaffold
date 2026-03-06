# S1 Sample Counting Rules

**Version**: v1.0
**Effective**: 2026-03-06 11:58 CST
**Status**: ACTIVE

---

## 1. 多标签样本规则

### 定义

**多标签样本**：一个样本可能同时满足多个桶的条件。

示例：
- 一个会话可能同时属于：`old_topic_recall` + `with_open_loops` + `user_correction`
- 用户在旧话题切回时还修改了约束，并且有未完成承诺

### 规则

#### 规则 1：允许多标签
一个样本可以被计入多个桶。

#### 规则 2：分开统计
```yaml
statistics:
  total_unique_samples: 唯一样本数
  bucket_hit_counts: 每个桶的命中数（可重叠）
  
  gate_1_requirements:
    total_unique_samples: >= 80
    each_bucket_hit_count: >= bucket_minimum
```

#### 规则 3：防止"复杂样本冲高覆盖率"
```yaml
coverage_check:
  method: unique_samples_per_bucket
  not: total_hits_across_buckets
  
  # 不能这样算：
  # 1 个复杂样本命中 6 个桶 → 6/6 桶达标 ❌
  
  # 必须这样算：
  # 每个桶至少有 N 个独立样本命中 ✅
```

### Recent Window 统计

```yaml
recent_window:
  size: 30
  counting_method: unique_samples
  
  # 允许多标签
  # 但每个样本只计入窗口一次
  
  example:
    sample_A: [old_topic_recall, with_open_loops]  # 计入窗口 1 次
    sample_B: [user_correction]                     # 计入窗口 1 次
    total_window_samples: 2  # 不是 3
```

---

## 2. Blocker 白名单

### 定义

**Blocker** = 必须立即修复的问题，可以打破 Feature Freeze。

### 白名单（只有这 3 类）

```yaml
blocker_types:
  - type: sampling_blocked
    description: 导致 S1 无法继续采样
    examples:
      - capsule 无法创建
      - context-retrieve 无法启动
      - 数据收集工具崩溃
    
  - type: metrics_invalid
    description: 导致指标计算失真
    examples:
      - 指标公式错误
      - 数据丢失
      - 统计脚本 bug
    
  - type: protection_failed
    description: 导致 resident/open_loops/commitments 保护失效
    examples:
      - Never-Compress Slots 被错误覆盖
      - 低 confidence 数据污染 resident
      - commitment 丢失
```

### 非 Blocker（不允许修复）

```yaml
not_blockers:
  - 指标展示优化
  - prompt 小优化
  - 召回排序调整
  - 性能优化
  - L2 参数修复（S1 不依赖）
  - 文档改进
  - UI/UX 改进
```

### 修复流程

```yaml
fix_process:
  step_1: 确认属于白名单
  step_2: 记录到 KNOWN_ISSUES.md
  step_3: 标记为 blocker
  step_4: 修复
  step_5: 验证不影响已收集数据
  step_6: 更新 baseline manifest
```

---

## 3. 实验面冻结

### 冻结范围（不只是代码）

```yaml
frozen_components:
  code:
    - tools/context-budget-check
    - tools/capsule-builder
    - tools/context-compress
    - tools/context-retrieve
    - tools/prompt-assemble
    - tools/context-shadow-report
  
  schemas:
    - schemas/active_state.v1.schema.json
    - schemas/session_capsule.v1.schema.json
    - schemas/compression_event.v1.schema.json
    - schemas/budget_snapshot.v1.schema.json
  
  policies:
    - POLICIES/CONTEXT_COMPRESSION.md
    - POLICIES/CONTEXT_COMPRESSION_ROLLOUT.md
    - POLICIES/S1_FEATURE_FREEZE.md
  
  metrics:
    - tools/s1-dashboard (指标计算逻辑)
    - bucket tagging 规则
    - confidence threshold (0.60)
  
  templates:
    - prompt assemble 模板
    - capsule 输出格式
  
  scoring:
    - old_topic_recovery_rate 公式
    - commitment_preservation_rate 公式
    - commitment_drift_rate 公式
    - priority_preservation_rate 公式
    - compression_gain_ratio 公式
```

---

## 4. 自由样本规则

### 背景

分桶最小样本数总和 = 67
总样本要求 = 80
**自由空间 = 13**

### 规则

```yaml
free_sample_rules:
  priority_1: 补到当前最弱桶
  rule: 不允许连续 10 个以上样本都来自非薄弱桶
  
  weakest_bucket_first: true
  
  example:
    current_state:
      old_topic_recall: 5/15  # 最弱
      multi_topic_switch: 10/12
      with_open_loops: 8/12
    
    next_10_samples:
      - 至少 5 个应该补到 old_topic_recall
      - 不能全部来自 multi_topic_switch
```

### 监控

```bash
# 每次采样后检查
s1-dashboard --bucket-weakness
```

---

## 5. S1 Baseline Manifest

**位置**: `artifacts/context_compression/S1_BASELINE_MANIFEST.json`

```json
{
  "version": "1.0",
  "created": "2026-03-06T11:58:00CST",
  "phase": "S1",
  
  "git": {
    "commit_hash": "<to_be_filled>",
    "branch": "main",
    "status": "clean"
  },
  
  "schema_versions": {
    "active_state": "v1",
    "session_capsule": "v1",
    "compression_event": "v1",
    "budget_snapshot": "v1"
  },
  
  "scoring_versions": {
    "old_topic_recovery_rate": "v1.0",
    "commitment_preservation_rate": "v1.0",
    "commitment_drift_rate": "v1.0",
    "priority_preservation_rate": "v1.0",
    "compression_gain_ratio": "v1.0"
  },
  
  "prompt_template_version": "v1.0",
  "bucket_policy_version": "v1.0",
  "dashboard_version": "v2.0",
  
  "confidence_threshold": 0.60,
  "never_compress_slots": [
    "task_goal",
    "open_loops",
    "recent_commitments",
    "tool_execution_state",
    "recent_errors",
    "user_corrected_constraints",
    "response_contract"
  ],
  
  "frozen_at": "2026-03-06T11:58:00CST",
  "frozen_by": "S1 Feature Freeze Policy"
}
```

---

## 6. 版本一致性检查

### 每次采样前

```bash
# 检查是否与 baseline 一致
s1-dashboard --check-baseline
```

### 如果检测到变更

```yaml
on_change_detected:
  action: alert
  require: 手动确认是否应该继续采样
  
  if_authorized:
    - 更新 baseline manifest
    - 记录变更原因
    - 标记样本为 "post-change"
```

---

**Keywords**: `sample-counting` `multi-label` `blocker-whitelist` `experimental-freeze` `baseline-manifest`
