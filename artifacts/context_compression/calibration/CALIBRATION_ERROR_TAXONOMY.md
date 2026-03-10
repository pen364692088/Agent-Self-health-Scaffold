# Calibration Error Taxonomy

**Date**: 2026-03-09T11:15:00-06:00
**Phase**: Gate 1.5 Phase 1

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Samples | 50 |
| Agreements | 14 |
| Disagreements | 36 |
| Agreement Rate | 28% |
| Overestimates | 5 (machine > human) |
| Underestimates | 31 (machine < human) |

---

## Root Cause Analysis

### Pattern 1: Participation Points Problem (Primary)

**Description**: Machine gives 0.25 for ANY detected feature, regardless of actual resume capability.

**Evidence**:
```
sample_synthetic_stress_user_correction_*:
  machine_readiness: 0.25 (has_constraint=true)
  human_readiness: 0 ("信息不足")
  disagreement: machine detected "不对，改成 capsule fallback 优先" as constraint
                but this is NOT enough to resume the task
```

**Frequency**: 31/36 disagreements (86%)

**Fix**: 
- Remove flat 0.25 per feature
- Require COMBINATION of features to achieve readiness
- Add "next_action_correctness" as mandatory signal

---

### Pattern 2: Surface Features ≠ Resume Capability

**Description**: Having file paths, decisions, or constraints doesn't mean you can continue the work.

**Evidence**:
```
sample_historical_old_topic_recall_bc615b44:
  machine_readiness: 0.25 (has_file_path=true)
  human_readiness: 0 ("信息不足")
  content: "## Task Completed: Monitoring Setup ✅"
  problem: Task already COMPLETED, no resume needed
```

**Frequency**: High overlap with Pattern 1

**Fix**:
- Check if task is COMPLETED before scoring
- Penalize samples with "✅ 完成" markers
- Require "active work in progress" signal

---

### Pattern 3: Missing Topic Context

**Description**: Capsule lacks the "what are we doing" context.

**Evidence**:
```
sample_synthetic_stress_post_tool_chat_*:
  machine_readiness: 0.25 (has_tool_state=true)
  human_readiness: 0 ("信息不足")
  problem: tool_state captured but NO context on why/what
```

**Fix**:
- Require topic/anchor along with tool_state
- Score tool_state as relevant ONLY if topic is also present

---

### Pattern 4: Agreement Only at Zero

**Description**: Agreement happens almost exclusively when both score 0.

**Evidence**: 14/14 agreements are (0, 0) pairs

**Implication**: Evaluator is not calibrated for ANY positive readiness case

**Fix**: Need calibration samples with actual positive readiness

---

## Disagreement Types Catalog

| Type | Count | Pattern |
|------|-------|---------|
| participation_points | 31 | Machine gives points for features, human says insufficient |
| completed_task_scored | 5 | Task already done, machine still scores |
| tool_without_context | 8 | Tool state captured but no topic |
| constraint_without_action | 12 | Constraint captured but no next step |

---

## What Human Evaluators Actually Look For

From human_reason field analysis:

1. **"信息不足"** (90% of cases) - Not enough to resume
2. **"topic清晰"** (rare) - Topic is clear but needs more
3. **"下一步明确"** (rare) - Next step is explicit

**Key insight**: Humans require:
- Topic + Context + Next Action (all three)

Machine requires:
- Any single feature (one is enough)

---

## Recommended Fixes

### 1. Change Scoring Model

Current:
```
readiness = 0.25 * count(features)
```

Proposed:
```
readiness = 0 if missing(topic)
readiness *= 0 if task_completed
readiness += 0.3 if has_next_action
readiness += 0.2 if has_tool_state AND has_topic
readiness += 0.2 if has_constraint AND has_topic
readiness *= penalty if stale_constraint
```

### 2. Add Mandatory Signals

Require at minimum:
- topic (what are we doing)
- context (why does it matter)
- status (where are we)

### 3. Penalize Completion Markers

If capsule contains:
- "✅ 完成"
- "Task Completed"
- "Done"

Apply heavy penalty or set readiness to 0.

---

## Next Steps

1. Create CALIBRATION_ERROR_SET.jsonl with detailed annotations
2. Rebuild readiness rubric (Phase 2)
3. Refit evaluator (Phase 3)
4. Re-validate (Phase 4)

