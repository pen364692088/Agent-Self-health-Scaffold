# M5a: Controlled Recall v1

**Status**: In Progress
**Branch**: feature/memory-kernel-m5a
**Started**: 2026-03-15T23:48:00Z

---

## Objective

默认只从 approved 召回，candidate 仅 shadow/debug 可见。支持 top-k 小流量召回，输出 recall trace。Truth 记录只允许精确引用，不允许摘要冒充原文。recall 失败时主链 fail-open。

---

## Core Principles

1. **Default from approved only** - 默认只从 approved 记忆召回
2. **Candidate shadow visibility** - 候选仅在 shadow/debug 模式可见
3. **Top-k small traffic** - 小流量召回，避免过载
4. **Trace output** - 输出召回追踪信息
5. **Truth exact quote** - Truth 记录只允许精确引用
6. **Fail-open** - 召回失败时主链继续执行

---

## Deliverables

| File | Description |
|------|-------------|
| core/memory/memory_recall.py | 召回引擎 |
| core/memory/recall_trace.py | 召回追踪 |
| docs/memory/RECALL_POLICY.md | 召回策略文档 |
| tests/memory/test_memory_recall.py | 召回测试 |
| tests/memory/test_memory_recall_trace.py | 追踪测试 |

---

## Recall Flow

```
Query → RecallEngine → Filter(approved only) → Top-K → Trace Output
                ↓
            Fail-Open → Continue on error
```

---

## Recall Modes

| Mode | Description | Candidate Visibility |
|------|-------------|---------------------|
| production | 生产模式 | Hidden |
| shadow | 影子模式 | Visible (tagged) |
| debug | 调试模式 | Visible |

---

## Truth Record Handling

Truth 层记录的特殊处理：
- 只允许精确引用（verbatim quote）
- 不允许摘要或改写
- 必须包含原文引用

```python
@dataclass
class TruthQuote:
    record_id: str
    exact_quote: str  # 精确引用原文
    source_ref: SourceRef
```

---

## Fail-Open Behavior

当召回失败时：
1. 记录错误日志
2. 输出 trace 信息
3. 返回空结果
4. 主链继续执行（不抛异常）

---

## Trace Information

```python
@dataclass
class RecallTrace:
    query: str
    mode: str
    total_scanned: int
    filtered_count: int
    top_k: int
    returned_count: int
    timing_ms: float
    errors: List[str]
    stages: List[TraceStage]
```

---

## Test Requirements

- test_recall_basic
- test_recall_from_approved_only
- test_recall_candidate_shadow_mode
- test_recall_candidate_debug_mode
- test_recall_top_k_limit
- test_recall_trace_output
- test_recall_fail_open
- test_truth_exact_quote
- test_truth_no_summary

---

## Acceptance Criteria

1. 所有测试通过
2. 默认只从 approved 召回
3. candidate 仅 shadow/debug 可见
4. Trace 输出完整
5. Truth 精确引用
6. Fail-open 生效

---

## Constraints

- 不接 OpenClaw bridge
- 不引入新 process debt
- 独立分支/提交/测试/验收

---

**Updated**: 2026-03-15T23:48:00Z
