# Mainline Promotion Report

**Date**: 2026-03-09T11:35:00-06:00
**Phase**: Post-Gate 1 · Mainline Promotion

---

## Executive Summary

V2 Readiness Evaluator 已正式集成到主压缩流程。

---

## Promotion Status

| Component | Status | Version |
|-----------|--------|---------|
| capsule-builder-v2.py | ✅ Updated | 2.0-gate-based |
| capsule-builder (wrapper) | ✅ Calls V2 | Default: V2 |
| evaluator_version logging | ✅ Enabled | 2.0-gate-based |

---

## Call Path Verification

### 1. Entry Point
```
tools/capsule-builder (wrapper)
  ↓
tools/capsule-builder-v2.py (V2 implementation)
  ↓
compute_readiness_v2_gates() (V2 evaluator)
```

### 2. Verification Test

**Input**:
```bash
python3 tools/capsule-builder --input history.jsonl --session-id test --start 1 --end 4 --json
```

**Output**:
```json
{
  "status": "success",
  "readiness": 0.65,
  "evaluator_version": "2.0-gate-based",
  "gates": {
    "topic_present": true,
    "task_active": true,
    "passed": true
  }
}
```

**Verdict**: ✅ V2 evaluator is being called

---

## Key Changes

### Before (V1)
```python
readiness = sum([
    0.25 if decision_anchors else 0,
    0.25 if file_path_anchors else 0,
    0.25 if tool_state_anchors else 0,
    0.25 if (constraint_anchors or open_loop_anchors) else 0
])
```

### After (V2)
```python
# Gate 1: Topic required
if not topic_present:
    return 0.0

# Gate 2: Task not completed
if task_completed:
    return 0.0

# Enhancement signals
score = 0.20  # Base
score += 0.30 if has_next_action else 0
score += 0.20 if has_decision_context else 0
score += 0.15 if has_tool_state else 0
score += 0.15 if has_open_loops else 0
```

---

## Version Tracking

Every capsule now includes:

```json
{
  "evaluator_version": "2.0-gate-based",
  "resume_readiness": {
    "score": 0.65,
    "version": "2.0-gate-based",
    "gates": {...},
    "signals": {...}
  }
}
```

This enables:
- Production monitoring
- Version drift detection
- Rollback verification

---

## Fallback Path

V1 evaluator is available via:
```bash
# Currently V2 is default, no V1 fallback implemented
# If needed, can add --version v1 flag
```

---

## Next Steps

1. ✅ Mainline promotion complete
2. ⏳ Production guardrails setup
3. ⏳ Baseline window monitoring

---

Created: 2026-03-09 11:35 CST
