# Resume-Readiness Rubric V2

**Version**: 2.0
**Date**: 2026-03-09
**Purpose**: Score capsule by "续做能力" (continuation capability), NOT "摘要质量" (summary quality)

---

## Core Principle

**Readiness = Can I continue this work without asking clarifying questions?**

- ❌ Not: "Does this look like a good summary?"
- ✅ Yes: "Do I have enough to pick up and continue?"

---

## Mandatory Signals (Gate Conditions)

### Gate 1: Topic Present

**Question**: What are we working on?

**Pass**: Clear topic/anchor present
```
✅ "修复 resume-readiness evaluator"
✅ "Gate 1.5 校准任务"
✅ "Context Compression Pipeline V2"
```

**Fail**: No topic or generic content
```
❌ "讨论了一些事情"
❌ "继续工作"
❌ Empty or only session startup messages
```

**Scoring**: If Gate 1 FAILS → readiness = 0, STOP

---

### Gate 2: Task Status Known

**Question**: Is the task still active?

**Pass**: Active work in progress
```
✅ "Phase 1 进行中"
✅ "正在修复..."
✅ "下一步：标注错误分类"
```

**Fail**: Task completed or no status
```
❌ "✅ Task Completed"
❌ "Done"
❌ No status indicator at all
```

**Scoring**: If Gate 2 FAILS → readiness = 0, STOP

---

## Enhancement Signals (Score Boosters)

Only evaluate if Gate 1 AND Gate 2 pass.

### Signal A: Next Action Explicit (+0.30)

**Question**: What exactly should I do next?

**Strong**:
- Specific action: "运行 calibration 脚本"
- Specific file: "编辑 tools/resume_readiness_calibration.py"
- Specific step: "Phase 1: 标注错误分类"

**Weak** (no boost):
- "继续" (generic)
- "需要看一下" (vague)

---

### Signal B: Context Preserved (+0.20)

**Question**: Why does this matter? What decisions led here?

**Strong**:
- Decision history: "选择了方案 A 因为..."
- Constraint noted: "不能用 OpenAI API"
- Trade-off recorded: "优先稳定性而非性能"

**Weak** (partial boost):
- Only file names without context
- Only error messages without resolution

---

### Signal C: Tool State Intact (+0.15)

**Question**: What tools/files were being used?

**Strong**:
- File paths with status: "已创建 tools/capsule-builder-v2.py"
- Tool outputs preserved
- Command history available

**Weak** (no boost):
- Tool names only, no state
- No file context

---

### Signal D: Open Loops Tracked (+0.15)

**Question**: What's pending? What constraints apply?

**Strong**:
- Explicit TODO list
- Constraints documented
- Known blockers noted

**Weak** (no boost):
- Vague "还有一些事情"
- No specific items

---

## Scoring Formula (V2)

```python
def compute_readiness_v2(capsule):
    # Gates (mandatory)
    if not has_topic(capsule):
        return 0.0
    
    if is_task_completed(capsule):
        return 0.0
    
    # Base score for passing gates
    score = 0.20
    
    # Enhancement signals
    score += 0.30 if has_explicit_next_action(capsule) else 0
    score += 0.20 if has_decision_context(capsule) else 0
    score += 0.15 if has_tool_state(capsule) else 0
    score += 0.15 if has_open_loops(capsule) else 0
    
    # Penalties
    if has_stale_constraint(capsule):
        score *= 0.5
    
    if has_conflicting_info(capsule):
        score *= 0.7
    
    return min(score, 1.0)
```

---

## Score Interpretation

| Score | Interpretation | Action |
|-------|----------------|--------|
| 0.00 | Cannot resume | Need full context re-injection |
| 0.20 | Bare minimum | Can try but likely need clarification |
| 0.50 | Moderate | Can continue with some uncertainty |
| 0.70 | Good | High confidence continuation |
| 0.85+ | Excellent | Seamless continuation possible |

---

## Anti-Patterns (Must Penalize)

### Anti-Pattern 1: Participation Points

❌ WRONG: "Detected a file path → +0.25"
✅ RIGHT: "File path + topic + status → consider scoring"

### Anti-Pattern 2: Summary Quality ≠ Resume Capability

❌ WRONG: "Summary looks complete → high score"
✅ RIGHT: "Can I actually continue? → check gates first"

### Anti-Pattern 3: Completed Task Scored High

❌ WRONG: "Found lots of details → 0.75"
✅ RIGHT: "Task shows ✅ 完成 → 0.0"

---

## Examples

### Example 1: High Readiness (0.85)

```
Topic: 修复 resume-readiness evaluator
Status: Phase 1 进行中
Next: 标注 calibration error set
Files: tools/resume_readiness_calibration.py
Constraints: 必须在 Gate 1.5 框架内修复
```

**Score**: 0.20 (base) + 0.30 (next action) + 0.20 (context) + 0.15 (tool) = 0.85

---

### Example 2: Moderate Readiness (0.50)

```
Topic: Context Compression V2
Status: 验证阶段
Next: [unclear]
Files: 多个文件已创建
```

**Score**: 0.20 (base) + 0.15 (tool) = 0.35

Wait, no next action. Recalculate:
0.20 (base) + 0.15 (tool state) = 0.35

Actually: 0.20 + 0.15 = 0.35

---

### Example 3: Zero Readiness (0.0)

```
Content: "✅ Task Completed: Monitoring Setup"
```

**Score**: 0.0 (Gate 2 fail: task completed)

---

### Example 4: Zero Readiness (0.0)

```
Content: [Session startup message only]
```

**Score**: 0.0 (Gate 1 fail: no topic)

---

## Implementation Checklist

- [ ] Add `has_topic()` detector
- [ ] Add `is_task_completed()` detector
- [ ] Rewrite `compute_machine_readiness()` with gate logic
- [ ] Add completion marker penalty
- [ ] Add stale constraint detection
- [ ] Re-run calibration with new rubric

---

## Validation Criteria

After implementing V2 rubric:

| Metric | Target | Current |
|--------|--------|---------|
| Agreement Rate | >= 70% | 28% |
| False Positive Rate | < 20% | Unknown |
| False Negative Rate | < 15% | Unknown |

---

Created: 2026-03-09 11:20 CST
