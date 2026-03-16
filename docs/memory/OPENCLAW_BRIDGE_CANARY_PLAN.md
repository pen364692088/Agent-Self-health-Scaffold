# OpenClaw Bridge Canary Assist Plan

**Version**: 1.0.0
**Date**: 2026-03-16
**Status**: In Progress

---

## Objective

在不影响 Truth Source、不正式接管主流程的前提下，让 OpenClaw 以"建议参与"方式使用 Memory Kernel recall suggestions，验证其真实帮助率、噪音率和可依赖性。

---

## Core Principles

1. **Canary Assist Only** - 只允许 canary assist，不允许 full-on
2. **No Auto-Inject** - 不允许自动改主回复
3. **No State Writeback** - 不允许自动写回主状态/truth source
4. **Candidate Isolation** - 不允许 candidate 进入正式召回
5. **Fail-Open Required** - fail-open 必须继续生效
6. **No Process Debt** - 不允许新增 process debt

---

## Assist vs Shadow

| Aspect | Shadow (G1) | Assist (G2) |
|--------|-------------|-------------|
| Visibility | Log only | Available to main chain |
| Influence | None | Suggestion only |
| Adoption | N/A | Tracked |
| Write-back | No | No |
| Full-on | No | No |

---

## Assist Flow

```
User Query
    │
    ▼
OpenClaw Agent
    │
    ├──▶ Main Chain
    │        │
    │        ├──▶ Get Recall Suggestions (Canary Assist)
    │        │         │
    │        │         ▼
    │        │    BridgeCanary.assist()
    │        │         │
    │        │         ▼
    │        │    Suggestions Available (Not Injected)
    │        │
    │        ├──▶ Agent Decides to Use or Ignore
    │        │
    │        ▼
    │    Main Response
    │
    └──▶ Logging & Metrics
```

---

## Assist Interface

### Request

```python
@dataclass
class AssistRequest:
    query: str  # 用户查询
    context: Optional[str] = None  # 上下文
    task_type: Optional[str] = None  # 任务类型
    max_suggestions: int = 3  # 最大建议数
    include_reasoning: bool = False  # 是否包含推理
```

### Response

```python
@dataclass
class AssistResponse:
    success: bool  # 是否成功
    suggestions: List[AssistSuggestion]  # 建议列表
    adoption_token: str  # 采纳令牌（用于追踪）
    trace: Optional[AssistTrace]  # 追踪信息
    error: Optional[str]  # 错误信息
```

### Adoption Tracking

```python
@dataclass
class AdoptionReport:
    adoption_token: str  # 采纳令牌
    adopted: bool  # 是否采纳
    helpful: Optional[bool] = None  # 是否有帮助
    reason: Optional[str] = None  # 原因
```

---

## Metrics to Track

### Quality Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| adoption_rate | 建议采纳率 | Monitor |
| helpful_rate | 有帮助率 | ≥60% |
| noise_rate | 噪音率 | ≤20% |

### Safety Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| rollback_after_recall | 召回后被回滚的比例 | ≤5% |
| demote_after_recall | 召回后被降级的比例 | ≤10% |
| task_mismatch_rate | 任务类型误触发率 | ≤10% |

### Integration Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| prompt_bloat_rate | prompt 膨胀率 | ≤30% |
| timeout_count | 超时次数 | ≤5% |
| error_count | 错误次数 | ≤5% |
| fail_open_success | fail-open 成功率 | 100% |

---

## Validation Requirements

### Must Verify

1. ✅ OpenClaw 能稳定获取 suggestions
2. ✅ Suggestions 不自动注入主 prompt
3. ✅ Agent 可选择采纳或忽略
4. ✅ 采纳情况被正确追踪
5. ✅ Fail-open 继续生效

### Must Not Happen

1. ❌ Suggestions 自动改主回复
2. ❌ Suggestions 自动写回主状态
3. ❌ Candidate 进入正式召回
4. ❌ Fail-open 失效

---

## Test Scenarios

### Basic Scenarios

1. **Assist Success**: 正常建议流程
2. **No Results**: 无结果时的行为
3. **Adoption Tracking**: 采纳追踪
4. **Ignore Suggestions**: 忽略建议

### Edge Cases

1. **High Noise**: 高噪音场景
2. **Budget Exceeded**: 预算超出
3. **Task Mismatch**: 任务类型不匹配
4. **Multiple Requests**: 多次请求

### Safety Scenarios

1. **No Auto-Inject**: 不自动注入
2. **No State Writeback**: 不写回状态
3. **Candidate Isolation**: candidate 隔离

---

## Exit Criteria

### Pass (Enter G3)

- 所有测试通过
- 采纳率 ≥40%
- 有帮助率 ≥60%
- 噪音率 ≤20%
- Fail-open 100% 成功
- 无安全违规

### Pass with Fixes

- 核心功能通过
- 存在可修复的质量/边界问题
- 需先修问题再进入 G3

### Fail

- 严重质量问题
- 安全违规
- Fail-open 失效

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

**Created**: 2026-03-16T01:15:00Z
