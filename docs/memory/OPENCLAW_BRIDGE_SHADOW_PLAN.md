# OpenClaw Bridge Shadow Plan

**Version**: 1.0.0
**Date**: 2026-03-16
**Status**: In Progress

---

## Objective

验证 OpenClaw 能否以只读 shadow 方式调用 Memory Kernel，在不影响主链决策、不污染主状态的前提下，评估 recall suggestion 的稳定性与价值。

---

## Core Principles

1. **Read-Only** - 只读，不正式注入主流程
2. **No Pollution** - 不改主回复/主状态/truth source
3. **Candidate Isolation** - 不允许 candidate 进入正式召回
4. **Single Path** - 单 canary agent / 单 workspace / 单入口链路
5. **Fail-Open** - bridge 失败必须 fail-open，不影响主链

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Agent                        │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ Main Chain       │  │ Shadow Chain     │             │
│  │ (Unaffected)     │  │ (Read-Only)      │             │
│  └──────────────────┘  └──────────────────┘             │
│           │                     │                        │
│           │                     ▼                        │
│           │         ┌──────────────────┐                 │
│           │         │ OpenClaw Bridge  │                 │
│           │         │ (Shadow Mode)    │                 │
│           │         └──────────────────┘                 │
│           │                     │                        │
└───────────┼─────────────────────┼────────────────────────┘
            │                     │
            ▼                     ▼
     ┌──────────────┐    ┌──────────────────┐
     │ Main State   │    │ Memory Kernel    │
     │ (Unchanged)  │    │ (Read-Only)      │
     └──────────────┘    └──────────────────┘
```

---

## Bridge Flow

```
User Query
    │
    ▼
OpenClaw Agent
    │
    ├──▶ Main Chain (Unaffected)
    │        │
    │        ▼
    │    Main Response
    │
    └──▶ Shadow Chain (Parallel)
             │
             ▼
         OpenClaw Bridge
             │
             ├──▶ Detect Task Type
             │
             ├──▶ Check Recall Policy
             │
             ├──▶ Apply Budget
             │
             ├──▶ Query Memory Kernel
             │
             ▼
         Recall Suggestions (Shadow)
             │
             ▼
         Log & Metrics (No Injection)
```

---

## Bridge Interface

### Input

```python
@dataclass
class BridgeRequest:
    query: str  # 用户查询
    context: Optional[str] = None  # 上下文
    task_type: Optional[str] = None  # 任务类型（可选）
    max_suggestions: int = 5  # 最大建议数
    timeout_ms: int = 1000  # 超时时间
```

### Output

```python
@dataclass
class BridgeResponse:
    success: bool  # 是否成功
    suggestions: List[RecallSuggestion]  # 召回建议
    trace: Optional[BridgeTrace]  # 追踪信息
    error: Optional[str]  # 错误信息
```

### Recall Suggestion

```python
@dataclass
class RecallSuggestion:
    record_id: str  # 记录 ID
    title: str  # 标题
    content_preview: str  # 内容预览
    relevance_score: float  # 相关性分数
    source: str  # 来源
    scope: str  # 作用域
    tkr_layer: str  # 层级
```

---

## Fail-Open Behavior

### Conditions

| Condition | Behavior |
|-----------|----------|
| Timeout | Return empty suggestions, continue |
| Memory Kernel Error | Log error, return empty |
| No Results | Return empty suggestions |
| Budget Exceeded | Truncate suggestions |
| Invalid Request | Return error, continue |

### Implementation

```python
try:
    response = bridge.recall(request)
except Exception as e:
    # Fail-open: log and continue
    log_error(e)
    response = BridgeResponse(
        success=False,
        suggestions=[],
        error=str(e),
    )

# Main chain continues regardless
main_response = main_chain.process(query)
```

---

## Validation Metrics

### Suggestion Quality

| Metric | Description | Target |
|--------|-------------|--------|
| adoption_rate | 建议采用率 | Monitor |
| helpful_rate | 帮助率 | ≥60% |
| noise_rate | 噪音率 | ≤20% |

### Safety Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| rollback_after_recall | 召回后被回滚的比例 | ≤5% |
| demote_after_recall | 召回后被降级的比例 | ≤10% |
| budget_stability | 预算稳定性 | Stable |
| task_mismatch_rate | 任务类型误触发率 | ≤10% |

### Integration Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| timeout_rate | 超时率 | ≤5% |
| error_rate | 错误率 | ≤5% |
| fail_open_success | fail-open 成功率 | 100% |

---

## Test Scenarios

### Basic Scenarios

1. **Normal Recall**: 正常召回流程
2. **No Results**: 无结果时的行为
3. **Timeout**: 超时时的行为
4. **Error**: 错误时的行为

### Edge Cases

1. **Budget Exceeded**: 预算超出时的截断
2. **Task Mismatch**: 任务类型不匹配时的行为
3. **Concurrent Requests**: 并发请求时的行为
4. **Empty Query**: 空查询时的行为

### Safety Scenarios

1. **Candidate Not Leaked**: candidate 不泄露
2. **Main State Unchanged**: 主状态不变
3. **Truth Source Unchanged**: truth source 不变

---

## Constraints

### Hard Constraints

| Constraint | Enforcement |
|------------|-------------|
| Read-only | No write operations |
| No injection | Suggestions not in main prompt |
| Candidate isolation | Only approved records |
| Fail-open | Exception handling |
| Single path | One bridge instance |

### Soft Constraints

| Constraint | Target |
|------------|--------|
| Latency | <100ms |
| Memory | <50MB |
| CPU | <10% |

---

## Exit Criteria

### Pass

- 所有测试通过
- Fail-open 100% 成功
- 噪音率 ≤20%
- 无 candidate 泄露
- 无主状态污染

### Pass with Fixes

- 核心功能通过
- 存在可修复的边界问题
- 需要先修边界再扩大 canary

### Fail

- 存在严重问题
- 候选泄露或主状态污染
- fail-open 失效

---

## Timeline

| Step | Duration |
|------|----------|
| Implementation | ~30 min |
| Testing | ~15 min |
| Validation | ~15 min |
| Documentation | ~10 min |
| **Total** | ~70 min |

---

**Created**: 2026-03-16T01:00:00Z
