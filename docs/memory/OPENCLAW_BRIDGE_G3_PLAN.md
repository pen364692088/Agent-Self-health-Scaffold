# OpenClaw Bridge G3 Plan: Limited Mainline Assist

**Version**: 1.0.0
**Date**: 2026-03-16
**Status**: In Progress

---

## Objective

让 OpenClaw 在有限主链范围内参考使用 Memory Kernel suggestion，但仍不成为主链强依赖，不写回 truth source，不自动改主回复。

---

## Core Principles

1. **Limited Scope** - 仅限指定任务类型
2. **Limited Entry** - 仅限单主链入口/小范围 canary
3. **Suggestion Block** - suggestion 仍为建议块，不自动注入改写
4. **Candidate Isolation** - candidate 不进入正式召回
5. **Fail-Open Required** - fail-open 必须继续有效
6. **No Process Debt** - 不允许新增 process debt

---

## G1 → G2 → G3 Progression

| Aspect | G1 Shadow | G2 Canary Assist | G3 Limited Mainline |
|--------|-----------|------------------|---------------------|
| Visibility | Log only | Available | Integrated (limited) |
| Influence | None | Suggestion | Suggestion (mainline) |
| Scope | All queries | Canary only | Limited task types |
| Adoption | N/A | Tracked | Tracked + Measured |
| Main Chain | No impact | Optional use | Available (limited) |

---

## Limited Mainline Configuration

### Allowed Task Types

| Task Type | Allowed | Budget |
|-----------|---------|--------|
| coding | Yes | 800 tokens |
| decision | Yes | 600 tokens |
| question | Yes | 400 tokens |
| analysis | No | 0 tokens |
| creative | No | 0 tokens |

### Entry Points

| Entry | Allowed | Description |
|-------|---------|-------------|
| main_chain_query | Yes | 主链查询入口 |
| subagent_query | No | 子代理查询 |
| batch_query | No | 批量查询 |

### Rate Limits

| Limit | Value |
|-------|-------|
| Max requests per session | 10 |
| Max tokens per session | 5000 |
| Cooldown between requests | 0 ms |

---

## Mainline Assist Flow

```
User Query
    │
    ▼
OpenClaw Main Chain
    │
    ├──▶ Check Task Type
    │        │
    │        ├──▶ Allowed → Continue
    │        └──▶ Not Allowed → Skip Assist
    │
    ├──▶ BridgeMainlineLimited.assist()
    │        │
    │        ├──▶ Get Suggestions
    │        │
    │        ├──▶ Format as Suggestion Block
    │        │
    │        └──▶ Return to Main Chain
    │
    ├──▶ Main Chain Processes
    │        │
    │        ├──▶ Uses Suggestions (Optional)
    │        │
    │        └──▶ Formulates Response
    │
    ▼
Main Response
```

---

## Mainline Assist Interface

### Request

```python
@dataclass
class MainlineAssistRequest:
    query: str  # 用户查询
    session_id: str  # 会话 ID（用于限流）
    task_type: str  # 任务类型
    max_suggestions: int = 3  # 最大建议数
    format: str = "block"  # 输出格式: block, list, markdown
```

### Response

```python
@dataclass
class MainlineAssistResponse:
    success: bool  # 是否成功
    allowed: bool  # 是否允许 assist
    suggestion_block: Optional[str]  # 格式化的建议块
    suggestions: List[MainlineSuggestion]  # 原始建议列表
    metrics: MainlineMetrics  # 指标
    error: Optional[str]  # 错误信息
```

### Suggestion Block Format

```markdown
---
📚 Memory Suggestions (Limited Mainline)

1. [API Versioning Rule] (Knowledge | Global)
   All API endpoints must be versioned with /vN prefix
   Relevance: 0.90

2. [Configuration Path] (Truth | Global)
   All configuration files are located in ~/.openclaw/ directory
   Relevance: 0.95

---
Note: These are suggestions from the memory kernel. Use at your discretion.
```

---

## Metrics to Track

### Quality Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| adoption_rate | 采纳率 | ≥40% |
| quality_improvement_rate | 质量提升率 | ≥10% |
| noise_rate | 噪音率 | ≤15% |

### Safety Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| rollback_after_recall | 召回后回滚比例 | ≤5% |
| demote_after_recall | 召回后降级比例 | ≤10% |
| fail_open_success | fail-open 成功率 | 100% |

### Integration Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| main_chain_success_rate | 主链成功率变化 | No decrease |
| prompt_bloat_rate | prompt 膨胀率 | ≤25% |
| rate_limit_hits | 限流触发次数 | Monitor |

---

## Exit Criteria

### Pass (Continue Expansion)

- 所有测试通过
- 采纳率 ≥40%
- 质量提升率 ≥10%
- 主链成功率不下降
- Fail-open 100% 成功
- 无安全违规

### Pass with Fixes

- 核心功能通过
- 存在可修复的问题
- 需先修问题再扩大

### Fail

- 严重质量问题
- 主链成功率下降
- 安全违规
- Fail-open 失效

---

## Timeline

| Step | Duration |
|------|----------|
| Implementation | ~40 min |
| Testing | ~20 min |
| Validation | ~20 min |
| Documentation | ~10 min |
| **Total** | ~90 min |

---

**Created**: 2026-03-16T01:32:00Z
