# Memory Event Schema v1.1

## 事件类型

| 类型 | 触发 | 含义 |
|------|------|------|
| `use` | 使用记忆条目 | use_count += 1 |
| `correction` | 用户纠正 | correction_count += 1 |
| `conflict` | 规则导致错误输出 | conflict_penalty += 0.5 |
| `pin` | 手动标记高价值 | pinned = true |
| `forget` | 手动删除 | status = deleted |
| `reflection` | 自我反思 | 记录但不影响评分 |
| `deprecate` | 规则弃用 | status = deprecated |
| `supersede` | 规则替换 | status = superseded, superseded_by = new_id |

## 事件格式 (JSONL)

```json
{
  "schema_version": "1.1",
  "ts": "2026-03-03T10:45:00Z",
  "event": "correction",
  "memory_id": "mem_20260303_001",
  "scope": "projects/openemotion",
  "session_id": "abc123",
  "task_id": "mvp8_implementation",
  "evidence": "No, do X instead",
  "independent": true
}
```

## 有界函数定义

### recency (有界 [0, 1])

```python
HALF_LIFE_DAYS = 14

def recency_boost(days_ago: int) -> float:
    """
    指数衰减: recency = exp(-days / half_life)
    - days=0 → 1.0
    - days=14 → 0.368 (半衰)
    - days=30 → 0.117
    - days=90 → 0.001
    """
    return math.exp(-days_ago / HALF_LIFE_DAYS)
```

### conflict (可复现)

```yaml
conflict_definition:
  trigger: "规则/事实导致错误输出, 被用户纠正"
  event: conflict
  calculation: conflict_penalty = count(conflict_event) * 0.5
  
example:
  - event: conflict
    memory_id: mem_001
    evidence: "这条规则导致 API 调用失败"
    # conflict_penalty += 0.5
```

## 评分模型 (v1.1)

```python
def calculate_score(use_count, days_ago, importance, conflict_penalty):
    """
    所有因子都有界:
    - log(use_count+1) ∈ [0, ~7]
    - recency_boost ∈ [0, 1]
    - importance ∈ [0, 1]
    - conflict_penalty ≥ 0
    
    score ∈ [0, ~12]
    """
    score = (
        2.0 * log(use_count + 1) +
        1.5 * recency_boost(days_ago) +    # 有界 [0, 1.5]
        3.0 * min(max(importance, 0), 1) -  # 有界 [0, 3]
        2.0 * max(conflict_penalty, 0)
    )
    return round(score, 2)

# Tier 判定
if pinned: tier = "HOT"  # 用户手动标记
elif score >= 7: tier = "HOT"
elif score >= 3: tier = "WARM"
else: tier = "COLD"
```

## 规则状态 (v1.1 新增)

| 状态 | 含义 | 召回行为 |
|------|------|----------|
| `active` | 正常使用 | 正常召回 |
| `deprecated` | 已弃用 | 不召回, 除非用户明确问旧方案 |
| `superseded` | 已被替换 | 不召回, 指向新规则 |
| `deleted` | 已删除 | 永不召回 |

### 弃用/替换事件

```json
{
  "schema_version": "1.1",
  "event": "deprecate",
  "memory_id": "mem_001",
  "reason": "API 已废弃"
}
```

```json
{
  "schema_version": "1.1",
  "event": "supersede",
  "memory_id": "mem_001",
  "superseded_by": "mem_002",
  "reason": "更优方案"
}
```

## 幂等性保证

**sweeper 只从 events.log 派生状态, 不做非幂等更新:**

```python
# 错误: 非幂等
entry.use_count += 1

# 正确: 从事件派生
entry.use_count = count(events where type=use and entry_id=...)
entry.last_used = max(events.timestamp where entry_id=...)
```

## events.log 轮转

```bash
# 按月轮转
events.log → events-202603.log

# 解析时合并所有历史日志
cat events-*.log | sort | uniq
```

## 纠正独立性验证

```yaml
independent_correction:
  conditions:
    - different session_id
    - within 30 day window
    - same scope
  
  calculation: |
    sessions = set(e.session_id for e in corrections)
    independent_count = len(sessions)
```

## 晋升规则

```yaml
rule_promotion:
  trigger: correction_count >= 3
  constraints:
    - independent_sessions >= 3
    - within_30_day_window: true
    - scope_consistent: true
  action:
    type: RULE
    confidence: 0.85
    tier: WARM (initial)
    status: pending_review  # 需要人工确认
```

## Review Queue (人工审核)

```yaml
review_queue:
  trigger: "自动晋升条件满足"
  action: "标记为 pending_review, 等待用户确认"
  
  user_response:
    - "确认升级" → status: active
    - "不要升级" → status: blocked, 写 blocked 事件
```
