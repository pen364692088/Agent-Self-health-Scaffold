# M5b: Limited Canary Recall Expansion

**Status**: In Progress
**Branch**: feature/memory-kernel-m5b
**Started**: 2026-03-16T00:29:00Z

---

## Objective

受限 canary 召回增强，按任务类型触发 recall，默认只召回 approved，增加 prompt budget 控制，输出 canary recall 质量报告。

---

## Core Principles

1. **Canary Only** - 只允许 canary 模式
2. **Approved Only** - 默认只召回 approved
3. **Budget Control** - prompt budget 控制
4. **Quality Report** - 输出质量报告
5. **A/B Testing** - 有/无 recall 对照实验

---

## Deliverables

| File | Description |
|------|-------------|
| core/memory/memory_recall_policy.py | 召回策略 |
| core/memory/memory_budget.py | 预算控制 |
| artifacts/memory/CANARY_RECALL_REPORT.md | canary 报告 |
| tests/memory/test_memory_recall_policy.py | 策略测试 |
| tests/memory/test_memory_budget.py | 预算测试 |

---

## Task Types

| Task Type | Recall Trigger | Budget |
|-----------|---------------|--------|
| question | Yes | 500 tokens |
| coding | Yes | 1000 tokens |
| decision | Yes | 800 tokens |
| creative | No | 0 tokens |
| analysis | Yes | 600 tokens |

---

## Budget Control

### Token Budget

```python
@dataclass
class PromptBudget:
    max_tokens: int = 1000
    max_records: int = 10
    max_content_length: int = 500
```

### Budget Enforcement

1. 记录数量限制
2. 内容长度限制
3. 总 token 估算
4. 超出时截断

---

## Canary Quality Metrics

| Metric | Description |
|--------|-------------|
| precision | 召回精度 |
| recall | 召回率 |
| latency | 召回延迟 |
| budget_used | 预算使用 |
| relevance | 相关性评分 |

---

## A/B Testing

### Control Group (No Recall)
- 不触发召回
- 仅使用上下文

### Treatment Group (With Recall)
- 触发召回
- 使用召回内容

### Comparison
- 输出质量
- 相关性
- 完整性

---

## Test Requirements

- test_recall_policy_by_task_type
- test_recall_policy_approved_only
- test_budget_enforcement
- test_budget_truncation
- test_canary_quality_metrics
- test_ab_comparison

---

## Acceptance Criteria

1. 所有测试通过
2. 只 canary 模式
3. candidate 不进入正式召回
4. budget 控制生效
5. 质量报告完整

---

## Constraints

- 不允许 candidate 进入正式召回
- 不允许 full-on
- 不允许接 OpenClaw 主流程
- 不允许与 bridge 或其他功能混提
- 无 process debt

---

**Updated**: 2026-03-16T00:29:00Z
