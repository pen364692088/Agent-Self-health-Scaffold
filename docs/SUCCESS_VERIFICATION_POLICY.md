# Success Verification Policy

**Version**: 1.0.0-draft
**Status**: Draft
**Date**: 2026-03-16

---

## Purpose

验证任务真正完成，防止假完成，确保成功判定可靠。

---

## Success Criteria

### Multi-Layer Verification

成功判定必须同时满足以下 6 层：

| Layer | Check | Description |
|-------|-------|-------------|
| L1 | Exit code | 命令返回 exit_code=0 |
| L2 | Artifact existence | 产物文件存在 |
| L3 | Contract validation | Contract 定义的条件满足 |
| L4 | Content validation | 内容/语义检查通过 |
| L5 | Consistency check | 三件套一致（state/ledger/evidence） |
| L6 | Event verification | task_completed 事件存在 |

### ⚠️ 禁止只靠 exit code

**不允许**:
- ❌ 只检查 exit_code=0 就判定成功
- ❌ 只检查文件存在就判定成功

**必须**:
- ✅ 所有 6 层检查通过
- ✅ 证据完整
- ✅ 三件套一致

---

## Layer Details

### L1: Exit Code

```python
def check_exit_code(result):
    return result.exit_code == 0
```

### L2: Artifact Existence

```python
def check_artifacts(expected_files):
    for file in expected_files:
        if not os.path.exists(file):
            return False
    return True
```

### L3: Contract Validation

```python
def check_contract(task_contract):
    # Check all contract conditions
    for condition in task_contract.conditions:
        if not condition.satisfied():
            return False
    return True
```

### L4: Content Validation

```python
def check_content(artifact, schema):
    # Validate content against schema
    content = load_artifact(artifact)
    return validate_against_schema(content, schema)
```

### L5: Consistency Check

```python
def check_consistency(task_id):
    state = load_task_state(task_id)
    ledger = load_task_ledger(task_id)
    evidence = load_task_evidence(task_id)
    
    # Check consistency
    return (
        state.status == ledger.status == "completed"
        and len(evidence) > 0
        and all_steps_have_evidence(state, evidence)
    )
```

### L6: Event Verification

```python
def check_event(task_id):
    events = load_events()
    return any(
        e.type == "task_completed"
        and e.task_id == task_id
        for e in events
    )
```

---

## False Positive Detection

### False Positive Patterns

| Pattern | Detection |
|---------|-----------|
| Exit code 0 but no output | L2 check fails |
| Output exists but wrong content | L4 check fails |
| State says completed but no evidence | L5 check fails |
| Evidence exists but inconsistent | L5 check fails |
| No completion event | L6 check fails |

### False Positive Rate

**Target**: ≤ 1%
**Measurement**: Sample audit of completed tasks

---

## Step Re-execution Protection

### Problem

Success step 不应该重跑：
- 已完成的 step 重复执行
- 浪费资源
- 可能引入不一致

### Solution

```python
def execute_step(step_id, operation):
    # Check if already completed
    if is_step_completed(step_id):
        log.info(f"Step {step_id} already completed, skipping")
        return get_cached_result(step_id)
    
    # Execute and mark completed
    result = operation()
    mark_step_completed(step_id, result)
    return result
```

### Evidence

- [ ] Step completion check
- [ ] Skip log (if skipped)
- [ ] Completion timestamp

---

## Evidence Requirements

### Verification Evidence

每次成功判定必须记录：

```json
{
  "task_id": "...",
  "verification": {
    "L1_exit_code": true,
    "L2_artifacts": true,
    "L3_contract": true,
    "L4_content": true,
    "L5_consistency": true,
    "L6_event": true
  },
  "evidence_paths": ["..."],
  "timestamp": "2026-03-16T00:00:00Z",
  "verifier": "success_verification_policy"
}
```

---

## Failure Handling

### Verification Failure

当任一层检查失败：

| Layer Failed | Action |
|--------------|--------|
| L1 | Mark step as failed, retry if possible |
| L2 | Mark step as incomplete, retry |
| L3 | Mark task as blocked, manual review |
| L4 | Mark step as failed, retry with fix |
| L5 | State recovery required |
| L6 | Event system check required |

---

## Audit Trail

### Audit Requirements

1. 所有成功判定必须有证据
2. 证据必须持久化
3. 支持 post-hoc 审计
4. 审计日志不可篡改

### Audit Process

```
1. Collect all verification evidence
2. Store in immutable storage
3. Generate audit hash
4. Record in task ledger
```

---

## Appendix

### Related Documents

- GATE_RULES.md
- task_state.json spec
- step_packet spec

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | 2026-03-16 | Initial draft |
