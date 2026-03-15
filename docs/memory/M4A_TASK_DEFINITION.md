# M4a: Capture Governance v1

**Status**: In Progress
**Branch**: feature/memory-kernel-m4a
**Started**: 2026-03-15T23:39:00Z

---

## Objective

自动捕获只写 candidate，不直接进入 authority knowledge。增加 capture 白名单、去重、噪音拦截、candidate promotion 机制。

---

## Core Principles

1. **Capture is candidate, not authority** - 捕获的内容只是候选，不是权威知识
2. **Whitelist only** - 只捕获白名单来源
3. **Deduplication** - 去重机制避免重复捕获
4. **Noise filtering** - 噪音拦截过滤低质量内容
5. **Explicit promotion** - 候选必须显式提升为正式记忆

---

## Required Fields

每条 capture 必须包含：
- capture_reason: 捕获原因
- source_ref: 来源引用
- scope: 作用域
- importance: 重要性 [0.0, 1.0]
- confidence: 置信度 [0.0, 1.0]
- authority_level: 权威等级

---

## Deliverables

| File | Description |
|------|-------------|
| core/memory/memory_capture.py | 捕获引擎 |
| core/memory/memory_candidate_store.py | 候选存储 |
| docs/memory/CAPTURE_POLICY.md | 捕获策略文档 |
| tests/memory/test_memory_capture.py | 捕获测试 |
| tests/memory/test_memory_candidate_promotion.py | 提升测试 |

---

## Capture Flow

```
Source → CaptureEngine → Validation → Deduplication → Noise Filter → CandidateStore
                                                                          ↓
                                                              Manual Review → Promotion
```

---

## Candidate States

| State | Description |
|-------|-------------|
| pending | 待审核 |
| approved | 已批准，可召回 |
| rejected | 已拒绝 |
| promoted | 已提升为正式记忆 |

---

## Whitelist Configuration

```yaml
capture_whitelist:
  sources:
    - session_log
    - decision_log
    - technical_note
  
  content_types:
    - RULE
    - FACT
    - PREFERENCE
  
  min_confidence: 0.5
  min_importance: 0.3
```

---

## Noise Filtering Rules

1. Empty or too short content (< 10 chars)
2. Duplicate content (similarity > 0.9)
3. Low confidence (< 0.5)
4. Low importance (< 0.3)
5. Missing required fields

---

## Promotion Criteria

- reviewed_by: 审核者
- review_notes: 审核备注
- approved_at: 批准时间
- target_tkr_layer: 目标层级

---

## Test Requirements

- test_capture_basic
- test_capture_with_whitelist
- test_capture_deduplication
- test_capture_noise_filter
- test_candidate_store_crud
- test_candidate_promotion
- test_candidate_rejection
- test_capture_missing_required_field

---

## Acceptance Criteria

1. 所有测试通过
2. 捕获不直接进入 authority knowledge
3. 白名单机制生效
4. 去重机制生效
5. 噪音拦截生效
6. Promotion 需要显式操作

---

## Constraints

- 不接 OpenClaw bridge
- 不引入新 process debt
- 独立分支/提交/测试/验收

---

**Updated**: 2026-03-15T23:39:00Z
