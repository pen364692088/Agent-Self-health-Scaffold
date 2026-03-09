# Recovery Outcome Schema

## Purpose

定义"真实恢复效果"的评估标准，使 readiness 指标的业务价值可衡量。

---

## Outcome Dimensions

### 1. topic_resumed_correctly

**Question**: 恢复后是否正确识别并延续了之前的主题？

| Rating | Definition |
|--------|------------|
| `success` | 完全正确识别主题，无偏移 |
| `partial` | 主题识别大致正确，但有轻微偏移或混淆 |
| `fail` | 主题识别错误或完全丢失 |

**Evaluation Criteria**:
- 主任务目标是否清晰
- 上下文关联是否正确
- 是否发生主题漂移

---

### 2. next_action_resumed_correctly

**Question**: 恢复后是否正确识别了下一步应该执行的动作？

| Rating | Definition |
|--------|------------|
| `success` | 下一步动作明确且正确 |
| `partial` | 有动作方向但不够具体 |
| `fail` | 下一步动作缺失或错误 |

**Evaluation Criteria**:
- 是否有明确的 next_action 信号
- next_action 是否与当前任务阶段匹配
- 是否可以直接执行

---

### 3. tool_state_sufficient

**Question**: 恢复后是否保留了足够的工具状态信息？

| Rating | Definition |
|--------|------------|
| `success` | 工具状态完整，可无缝继续 |
| `partial` | 部分工具状态保留，需要补充 |
| `fail` | 工具状态丢失，需要重新开始 |

**Evaluation Criteria**:
- 已调用工具的结果是否保留
- 待调用工具的参数是否明确
- 工具依赖链是否清晰

---

### 4. constraint_fresh

**Question**: 恢复后是否保留了最新的约束条件？

| Rating | Definition |
|--------|------------|
| `success` | 所有最新约束都被保留 |
| `partial` | 部分约束保留，有遗漏风险 |
| `fail` | 约束条件丢失或过期 |

**Evaluation Criteria**:
- 用户最近的偏好/限制是否记录
- 任务约束是否更新
- 是否有冲突的旧约束

---

### 5. open_loop_continued

**Question**: 恢复后是否正确处理了未完成的循环？

| Rating | Definition |
|--------|------------|
| `success` | 所有 open loop 被正确识别和延续 |
| `partial` | 部分 open loop 被识别 |
| `fail` | open loop 丢失或被错误关闭 |

**Evaluation Criteria**:
- 是否有未完成的任务
- 是否有等待中的决策
- 是否有挂起的依赖

---

### 6. overall_recovery_success

**Question**: 综合评估恢复是否成功？

| Rating | Definition |
|--------|------------|
| `success` | 可以直接继续工作，无需额外上下文 |
| `partial` | 需要少量补充信息才能继续 |
| `fail` | 无法继续，需要重新开始 |

**Scoring Rule**:
```
success: >= 4 dimensions success
partial: 2-3 dimensions success
fail: <= 1 dimension success
```

---

## Schema Definition (JSON)

```json
{
  "sample_id": "string",
  "bucket": "string",
  "readiness_score": "float (0-1)",
  "v2_gates": {
    "topic_present": "boolean",
    "task_active": "boolean",
    "passed": "boolean",
    "failed_at": "string|null"
  },
  "v2_signals": {
    "next_action": "boolean",
    "decision_context": "boolean",
    "tool_state": "boolean",
    "open_loops": "boolean"
  },
  "outcome": {
    "topic_resumed_correctly": "success|partial|fail",
    "next_action_resumed_correctly": "success|partial|fail",
    "tool_state_sufficient": "success|partial|fail",
    "constraint_fresh": "success|partial|fail",
    "open_loop_continued": "success|partial|fail",
    "overall_recovery_success": "success|partial|fail"
  },
  "notes": "string (optional)",
  "human_reason": "string (from calibration)"
}
```

---

## Evaluation Protocol

### For Each Sample

1. **Read the capsule content** (from sample data)
2. **Simulate recovery**: What would the agent know after reading this capsule?
3. **Rate each dimension** based on the schema above
4. **Calculate overall** using the scoring rule

### Special Cases

**Information Insufficient (human_score = 0)**:
- Usually means the capsule is too sparse for ANY recovery
- Expected outcome: all dimensions = fail

**High Readiness but Low Agreement (FP cases)**:
- Need to answer: Is the evaluator over-optimistic, or is recovery actually possible?
- Check if missing signals are critical for this specific bucket

---

## Success Criteria for Phase B

1. ✅ Schema defined (this document)
2. ⏳ Samples labeled with outcomes
3. ⏳ Correlation analysis shows readiness ↔ outcome relationship
4. ⏳ Hotspot (long_technical) root cause identified

---

*Schema Version: 1.0*
*Created: 2026-03-09*
